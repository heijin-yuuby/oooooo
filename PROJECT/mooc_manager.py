import os
import json
import subprocess
import logging
from pathlib import Path
import time
import shutil
import platform
from threading import Lock
import psutil

def setup_logging(name):
    """设置日志记录器"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # 确保日志目录存在
    os.makedirs('logs/app', exist_ok=True)
    
    # 文件处理器
    file_handler = logging.FileHandler(
        'logs/app/mooc_manager.log',
        encoding='utf-8'
    )
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    )
    logger.addHandler(file_handler)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    )
    logger.addHandler(console_handler)
    
    return logger

class MoocManager:
    def __init__(self):
        # 设置日志
        self.logger = setup_logging('mooc_manager')
        
        # 使用更清晰的目录结构
        self.project_root = Path(__file__).parent.absolute()
        self.mooc_exe = self.project_root / 'mooc_executable' / 'aoaostar_mooc'
        self.config_template = self.project_root / 'mooc_executable' / 'config.template.json'
        self.config_dir = self.project_root / 'mooc_configs'
        self.logs_dir = self.project_root / 'logs/tasks'
        
        # 检测运行环境
        self.use_docker = platform.system().lower() != 'linux'
        
        # 创建必要目录
        self.config_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        # 并发控制
        self.max_concurrent_tasks = 50  # 最大并发任务数
        self.running_tasks = {}  # 记录运行中的任务
        self.task_lock = Lock()  # 任务锁
        
        self.logger.info(f"MoocManager初始化 - 可执行文件: {self.mooc_exe}")
        self.logger.info(f"运行模式: {'Docker' if self.use_docker else '本地'}")
        self.logger.info(f"最大并发任务数: {self.max_concurrent_tasks}")

    def get_running_task_count(self):
        """获取当前运行中的任务数"""
        with self.task_lock:
            # 清理已结束的任务
            for order_id in list(self.running_tasks.keys()):
                process = self.running_tasks[order_id]
                if process.poll() is not None:
                    del self.running_tasks[order_id]
            return len(self.running_tasks)

    def is_account_running(self, account):
        """检查账号是否有正在运行的任务"""
        try:
            for order_id, process in self.running_tasks.items():
                log_path = self.logs_dir / f"task_{order_id}.log"
                if log_path.exists():
                    with open(log_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if account in content and process.poll() is None:
                            return True
            return False
        except Exception as e:
            self.logger.error(f"检查账号运行状态出错: {e}")
            return False

    def validate_account(self, account):
        """验证账号格式是否正确"""
        if not account or not isinstance(account, str):
            return False
        # 假设账号应该是12位数字
        if not account.isdigit() or len(account) != 12:
            return False
        return True

    def start_task(self, order_id, account, password, base_url):
        """启动新的刷课任务"""
        try:
            # 检查并发数量
            current_tasks = self.get_running_task_count()
            if current_tasks >= self.max_concurrent_tasks:
                error = f"系统任务数已达上限({self.max_concurrent_tasks})"
                self.logger.error(error)
                raise RuntimeError(error)

            # 检查账号是否已在运行
            if self.is_account_running(account):
                error = f"账号 {account} 已有正在运行的任务"
                self.logger.error(error)
                raise RuntimeError(error)

            # 验证账号
            if not self.validate_account(account):
                error = f"账号格式无效: {account}"
                self.logger.error(error)
                raise ValueError(error)

            self.logger.info(f"开始任务 - ID: {order_id}, 账号: {account}, 平台: {base_url}")
            
            # 使用绝对路径
            executable = str(self.mooc_exe.absolute())
            config_path = str(self.config_dir / f"config_{order_id}.json")
            log_path = str(self.logs_dir / f"task_{order_id}.log")
            
            # 检查可执行文件
            if not os.path.exists(executable):
                error = f"找不到可执行文件: {executable}"
                self.logger.error(error)
                raise FileNotFoundError(error)
            
            # 从模板创建配置
            if not self.config_template.exists():
                error = f"找不到配置模板: {self.config_template}"
                self.logger.error(error)
                raise FileNotFoundError(error)
            
            # 读取模板
            with open(self.config_template, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 更新用户信息
            if 'users' in config and len(config['users']) > 0:
                config['users'][0].update({
                    "username": str(account),
                    "password": str(password),
                    "base_url": str(base_url)
                })
                self.logger.info(f"更新配置 - ID: {order_id}, 账号: {account}, 平台: {base_url}")
            else:
                error = "配置模板格式无效"
                self.logger.error(error)
                raise ValueError(error)
            
            # 保存配置文件
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            self.logger.info(f"保存配置文件 - 路径: {config_path}")
            
            # 创建日志文件
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write(f"开始任务 {order_id}\n")
                f.write(f"工作目录: {self.project_root}\n")
                f.write(f"可执行文件: {executable}\n")
                f.write(f"配置文件: {config_path}\n")
                f.write(f"账号: {account}\n")
                f.write(f"平台: {base_url}\n")
                f.write(f"配置内容:\n{json.dumps(config, indent=2, ensure_ascii=False)}\n")
            
            # 根据环境选择启动方式
            if self.use_docker:
                self.logger.info(f"使用Docker启动任务 - ID: {order_id}")
                config_name = f"config_{order_id}.json"
                process = subprocess.Popen(
                    [
                        "docker", "run", "--rm",
                        "-v", f"{self.mooc_exe}:/app/aoaostar_mooc:ro",
                        "-v", f"{self.config_dir}/{config_name}:/app/config.json:ro",
                        "-v", f"{self.logs_dir}:/app/logs:rw",
                        "--security-opt", "seccomp=unconfined",
                        "mooc-automation",
                        "-c", "/app/config.json"
                    ],
                    stdout=open(log_path, 'a', encoding='utf-8'),
                    stderr=subprocess.STDOUT,
                    cwd=str(self.project_root)
                )
            else:
                self.logger.info(f"本地启动任务 - ID: {order_id}")
                process = subprocess.Popen(
                    [executable, "-c", config_path],
                    stdout=open(log_path, 'a', encoding='utf-8'),
                    stderr=subprocess.STDOUT,
                    cwd=str(self.project_root)
                )
            
            # 记录运行中的任务
            with self.task_lock:
                self.running_tasks[order_id] = process
            
            # 等待进程启动并检查日志
            max_retries = 30
            retries = 0
            automation_started = False
            login_success = False
            task_started = False
            
            while retries < max_retries:
                time.sleep(1)
                retries += 1
                
                # 检查进程状态
                return_code = process.poll()
                
                # 检查task日志
                with open(log_path, 'r', encoding='utf-8') as f:
                    task_log_content = f.read()
                
                # 检查是否启动成功
                if "web端启动成功" in task_log_content:
                    automation_started = True
                    self.logger.info(f"任务启动成功 - ID: {order_id}")
                
                # 检查是否登录成功
                if "登录成功" in task_log_content:
                    login_success = True
                    self.logger.info(f"登录成功 - ID: {order_id}")
                
                # 检查是否任务开始
                if "任务系统启动成功" in task_log_content:
                    task_started = True
                    self.logger.info(f"任务系统启动成功 - ID: {order_id}")
                    break
                
                # 检查是否有登录失败
                if ("Login failed" in task_log_content or 
                    "登录失败" in task_log_content or 
                    "请选择学校信息" in task_log_content):
                    error_msg = f"登录失败 - ID: {order_id}, 账号: {account}"
                    self.logger.error(error_msg)
                    process.kill()
                    with self.task_lock:
                        if order_id in self.running_tasks:
                            del self.running_tasks[order_id]
                    raise RuntimeError(error_msg)
                
                # 如果进程已结束
                if return_code is not None:
                    with self.task_lock:
                        if order_id in self.running_tasks:
                            del self.running_tasks[order_id]
                    if automation_started and login_success and task_started:
                        self.logger.info(f"任务完成 - ID: {order_id}")
                        return {
                            "status": "success",
                            "pid": process.pid,
                            "order_id": order_id
                        }
                    else:
                        error_msg = f"进程意外结束 - ID: {order_id}, 返回码: {return_code}"
                        self.logger.error(error_msg)
                        raise RuntimeError(error_msg)
            
            # 如果没有看到必要的成功信息
            if not (automation_started and login_success and task_started):
                process.kill()
                with self.task_lock:
                    if order_id in self.running_tasks:
                        del self.running_tasks[order_id]
                error_msg = f"任务启动超时 - ID: {order_id}"
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)
            
            # 进程正常运行中
            self.logger.info(f"任务运行中 - ID: {order_id}")
            return {
                "status": "success",
                "pid": process.pid,
                "order_id": order_id
            }
            
        except Exception as e:
            error_msg = f"任务启动失败 - ID: {order_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            with self.task_lock:
                if order_id in self.running_tasks:
                    del self.running_tasks[order_id]
            raise RuntimeError(error_msg)

    def get_task_status(self, order_id):
        """获取任务状态"""
        log_path = self.logs_dir / f"task_{order_id}.log"
        
        try:
            if log_path.exists():
                with open(log_path, encoding='utf-8') as f:
                    content = f.read()
                    
                    # 检查是否有明确的错误信息
                    if "账号密码不正确" in content:
                        status = "账号密码错误"
                    elif "学生信息不存在" in content:
                        status = "账号错误"
                    elif "登录失败" in content or "Login failed" in content:
                        status = "登录失败"
                    # 检查是否有明确的成功完成标志
                    elif "恭喜您, 所有任务都已全部完成" in content:
                        status = "已完成"
                    # 检查是否有登录成功标志
                    elif "] 登录成功" in content:
                        status = "运行中"
                    # 检查是否有启动标志
                    elif "web端启动成功" in content:
                        status = "正在启动"
                    # 检查是否有其他错误信息
                    elif "error" in content.lower() or "failed" in content.lower() or "fatal" in content.lower():
                        status = "运行出错"
                    else:
                        status = "状态未知"
                    
                    self.logger.info(f"获取任务状态 - ID: {order_id}, 状态: {status}")
                    return status
            else:
                self.logger.warning(f"找不到任务日志 - ID: {order_id}")
                return "未找到日志"
        except Exception as e:
            self.logger.error(f"检查任务状态出错 - ID: {order_id}: {e}")
            return "检查状态出错"

    def get_system_status(self):
        """获取系统状态"""
        try:
            running_count = self.get_running_task_count()
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            
            return {
                "running_tasks": running_count,
                "max_tasks": self.max_concurrent_tasks,
                "cpu_usage": cpu_percent,
                "memory_usage": memory.percent,
                "memory_available": f"{memory.available / (1024*1024*1024):.1f}GB"
            }
        except Exception as e:
            self.logger.error(f"获取系统状态出错: {e}")
            return None

mooc_manager = MoocManager() 