from flask import Flask, request, render_template, redirect, url_for, flash, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
import os
import logging
from datetime import datetime
from mooc_manager import mooc_manager
from functools import wraps
from utils.alipay_helper import AlipayHelper
from extensions import db
from models import User, Task, Order
import uuid

# 配置日志
def setup_logging():
    # 确保日志目录存在
    os.makedirs('logs/app', exist_ok=True)
    os.makedirs('logs/tasks', exist_ok=True)
    os.makedirs('logs/system', exist_ok=True)

    # 配置根日志记录器
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            # 应用日志
            logging.FileHandler('logs/app/web_app.log', encoding='utf-8'),
            # 控制台输出
            logging.StreamHandler()
        ]
    )

    # 获取应用的日志记录器
    logger = logging.getLogger('mooc_app')
    logger.setLevel(logging.INFO)
    
    return logger

# 设置日志
logger = setup_logging()

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 用于flash消息

# 确保实例目录存在
instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
os.makedirs(instance_path, exist_ok=True)

# 配置数据库
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(instance_path, "app.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db.init_app(app)

# 登录验证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'error')
            return redirect(url_for('login'))
        
        # 验证用户是否存在
        user = User.query.get(session['user_id'])
        if user is None:
            # 如果用户不存在，清除会话并重定向到登录页面
            session.clear()
            flash('会话已过期，请重新登录', 'error')
            return redirect(url_for('login'))
            
        return f(*args, **kwargs)
    return decorated_function

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'error')
            return redirect(url_for('register'))
            
        if User.query.filter_by(email=email).first():
            flash('邮箱已被注册', 'error')
            return redirect(url_for('register'))
            
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('注册成功，请登录', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            flash('登录成功', 'success')
            return redirect(url_for('dashboard'))
            
        flash('用户名或密码错误', 'error')
        return redirect(url_for('login'))
        
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('已退出登录', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        user = User.query.get(session['user_id'])
        if user is None:
            session.clear()
            flash('用户不存在，请重新登录', 'error')
            return redirect(url_for('login'))
            
        tasks = Task.query.filter_by(user_id=user.id).order_by(Task.created_at.desc()).all()
        system_status = mooc_manager.get_system_status()
        return render_template('dashboard.html', user=user, tasks=tasks, system_status=system_status)
    except Exception as e:
        logger.error(f"访问仪表盘时发生错误: {str(e)}", exc_info=True)
        flash('访问仪表盘时发生错误', 'error')
        return redirect(url_for('login'))

# 修改原有路由，添加用户认证
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/submit', methods=['POST'])
@login_required
def submit():
    try:
        account = request.form.get('account')
        password = request.form.get('password')
        platform = request.form.get('platform')
        
        user = User.query.get(session['user_id'])
        if user.balance < 10:
            flash('余额不足，请先充值', 'error')
            return redirect(url_for('dashboard'))
        
        logger.info(f"收到任务提交请求 - 账号: {account}, 平台: {platform}")
        
        if not account or not password or not platform:
            logger.warning(f"提交的表单缺少必要字段 - 账号: {account}")
            flash('请填写所有必填字段', 'error')
            return redirect(url_for('dashboard'))
        
        # 创建任务记录
        task = Task(
            user_id=session['user_id'],
            account=account,
            platform=platform
        )
        db.session.add(task)
        db.session.commit()
        logger.info(f"创建新任务记录 - ID: {task.id}, 账号: {account}, 平台: {platform}")
        
        # 启动MOOC任务
        result = mooc_manager.start_task(str(task.id), account, password, platform)
        logger.info(f"任务启动结果 - ID: {task.id}, 结果: {result}")
        
        if result['status'] == 'success':
            # 扣除用户余额
            user.balance -= 10
            db.session.commit()
            
            logger.info(f"任务提交成功 - ID: {task.id}, 账号: {account}")
            flash('任务已成功提交', 'success')
            return redirect(url_for('status', task_id=task.id))
        else:
            task.status = '提交失败'
            db.session.commit()
            logger.error(f"任务提交失败 - ID: {task.id}, 账号: {account}")
            flash('任务提交失败', 'error')
            return redirect(url_for('dashboard'))
            
    except Exception as e:
        logger.error(f"提交任务时发生错误: {str(e)}", exc_info=True)
        flash('提交任务时发生错误', 'error')
        return redirect(url_for('dashboard'))

@app.route('/status/<int:task_id>')
@login_required
def status(task_id):
    task = Task.query.get_or_404(task_id)
    # 确保用户只能查看自己的任务
    if task.user_id != session['user_id']:
        flash('无权访问此任务', 'error')
        return redirect(url_for('dashboard'))
        
    mooc_status = mooc_manager.get_task_status(str(task_id))
    logger.info(f"检查任务状态 - ID: {task_id}, 当前状态: {mooc_status}")
    
    if mooc_status != task.status:
        old_status = task.status
        task.status = mooc_status
        db.session.commit()
        logger.info(f"更新任务状态 - ID: {task_id}, 旧状态: {old_status}, 新状态: {mooc_status}")
    
    return render_template('status.html', task=task)

@app.route('/api/status/<task_id>', methods=['GET'])
@login_required
def api_status(task_id):
    task = Task.query.filter_by(id=task_id, user_id=session['user_id']).first()
    if not task:
        flash('任务不存在', 'error')
        return redirect(url_for('dashboard'))
    
    return jsonify({
        'id': task.id,
        'status': task.status,
        'created_at': task.created_at.isoformat(),
        'updated_at': task.updated_at.isoformat()
    })

# 创建支付订单
@app.route('/api/create_order', methods=['POST'])
@login_required
def create_order():
    try:
        amount = request.form.get('amount')
        logger.info(f"收到充值请求 - 金额: {amount}")
        
        if not amount:
            return jsonify({'status': 'error', 'message': '请输入充值金额'})
            
        # 创建订单记录
        order_no = str(uuid.uuid4()).replace('-', '')
        order = Order(
            order_no=order_no,
            user_id=session['user_id'],
            amount=float(amount),
            status='pending'
        )
        db.session.add(order)
        db.session.commit()
        logger.info(f"订单创建成功 - 订单号: {order_no}")
        
        # 生成支付链接
        try:
            alipay = AlipayHelper()
            pay_url = alipay.create_order(
                order_no=order_no,
                amount=amount,
                subject="网课助手猫会员充值"
            )
            logger.info(f"支付链接生成成功 - URL: {pay_url}")
            return jsonify({'status': 'success', 'pay_url': pay_url})
        except Exception as e:
            logger.error(f"生成支付链接失败: {str(e)}", exc_info=True)
            return jsonify({'status': 'error', 'message': '生成支付链接失败'})
            
    except Exception as e:
        logger.error(f"创建订单失败: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': '创建订单失败'})

# 支付宝同步回调
@app.route('/api/alipay/return', methods=['GET'])
def alipay_return():
    try:
        data = request.args.to_dict()
        logger.info(f"收到支付宝同步通知 - 参数: {data}")
        
        alipay = AlipayHelper()
        verify_result = alipay.verify_payment(data)
        logger.info(f"支付宝同步通知验证结果: {verify_result}")
        
        if verify_result:
            order_no = data.get('out_trade_no')
            trade_no = data.get('trade_no')
            
            logger.info(f"支付宝同步通知验证成功 - 订单号: {order_no}, 交易号: {trade_no}")
            
            order = Order.query.filter_by(order_no=order_no).first()
            if not order:
                logger.error(f"订单不存在 - 订单号: {order_no}")
                flash('订单不存在', 'error')
                return redirect(url_for('recharge'))
                
            if order.status == 'paid':
                logger.info(f"订单已支付 - 订单号: {order_no}")
                flash('订单已支付', 'info')
                return redirect(url_for('recharge'))
                
            # 更新订单状态
            order.status = 'paid'
            order.trade_no = trade_no
            order.paid_at = datetime.utcnow()
            
            # 更新用户余额
            user = User.query.get(order.user_id)
            if user:
                old_balance = user.balance
                user.balance += order.amount
                db.session.commit()
                logger.info(f"订单支付成功，余额已更新 - 订单号: {order_no}, 用户: {user.username}, 旧余额: {old_balance}, 新余额: {user.balance}")
                flash('充值成功！', 'success')
            else:
                logger.error(f"用户不存在 - 订单号: {order_no}, 用户ID: {order.user_id}")
                flash('用户不存在', 'error')
        else:
            logger.error(f"支付验证失败（同步通知） - 参数: {data}")
            flash('支付验证失败', 'error')
    except Exception as e:
        logger.error(f"处理支付宝同步回调时发生错误: {str(e)}", exc_info=True)
        flash('处理支付回调时发生错误', 'error')
        
    return redirect(url_for('recharge'))

# 支付宝异步通知
@app.route('/api/alipay/notify', methods=['POST'])
def alipay_notify():
    try:
        data = request.form.to_dict()
        logger.info(f"收到支付宝异步通知 - 参数: {data}")
        
        alipay = AlipayHelper()
        verify_result = alipay.verify_payment(data)
        logger.info(f"支付宝异步通知验证结果: {verify_result}")
        
        if verify_result:
            order_no = data.get('out_trade_no')
            trade_no = data.get('trade_no')
            trade_status = data.get('trade_status')
            
            logger.info(f"支付宝异步通知验证成功 - 订单号: {order_no}, 交易号: {trade_no}, 状态: {trade_status}")
            
            if trade_status == 'TRADE_SUCCESS':
                order = Order.query.filter_by(order_no=order_no).first()
                if not order:
                    logger.error(f"订单不存在 - 订单号: {order_no}")
                    return 'fail'
                    
                if order.status == 'paid':
                    logger.info(f"订单已支付 - 订单号: {order_no}")
                    return 'success'
                    
                if order.status == 'pending':
                    order.status = 'paid'
                    order.trade_no = trade_no
                    order.paid_at = datetime.utcnow()
                    
                    # 更新用户余额
                    user = User.query.get(order.user_id)
                    if user:
                        old_balance = user.balance
                        user.balance += order.amount
                        db.session.commit()
                        logger.info(f"订单支付成功，余额已更新 - 订单号: {order_no}, 用户: {user.username}, 旧余额: {old_balance}, 新余额: {user.balance}")
                        return 'success'
                    else:
                        logger.error(f"用户不存在 - 订单号: {order_no}, 用户ID: {order.user_id}")
                else:
                    logger.info(f"订单状态异常 - 订单号: {order_no}, 状态: {order.status}")
            else:
                logger.info(f"交易状态不是成功 - 订单号: {order_no}, 状态: {trade_status}")
        else:
            logger.error(f"支付宝异步通知验证失败 - 参数: {data}")
    except Exception as e:
        logger.error(f"处理支付宝异步通知时发生错误: {str(e)}", exc_info=True)
    
    return 'fail'

# 添加充值页面路由
@app.route('/recharge')
@login_required
def recharge():
    user = User.query.get(session['user_id'])
    orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).all()
    return render_template('recharge.html', user=user, orders=orders)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    logger.info("Web应用启动 - 监听端口: 20086")
    app.run(host='127.0.0.1', port=20086, debug=True)
