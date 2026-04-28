"""
无人机网络安全防御系统 - 主入口
Drone Security Defense System - Main Entry Point
"""

import argparse
import os
import sys
import signal
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.daemon import SecurityDaemon
from src.utils.logger import get_logger, setup_default_logger


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="无人机网络安全防御系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --config config/default_config.yaml
  %(prog)s --config config/default_config.yaml --daemon
  %(prog)s --config config/default_config.yaml --daemon --pid /var/run/drone_security.pid
  %(prog)s --config config/default_config.yaml --status
  %(prog)s --config config/default_config.yaml --stop
        """
    )

    parser.add_argument(
        "--config",
        required=True,
        help="配置文件路径"
    )

    parser.add_argument(
        "--daemon",
        action="store_true",
        help="守护进程模式"
    )

    parser.add_argument(
        "--pid",
        help="PID文件路径"
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="日志级别"
    )

    parser.add_argument(
        "--log-path",
        default="logs/",
        help="日志目录路径"
    )

    # 操作模式
    mode_group = parser.add_mutually_exclusive_group()

    mode_group.add_argument(
        "--status",
        action="store_true",
        help="显示运行状态"
    )

    mode_group.add_argument(
        "--stop",
        action="store_true",
        help="停止守护进程"
    )

    mode_group.add_argument(
        "--reload",
        action="store_true",
        help="重新加载配置"
    )

    return parser.parse_args()


def setup_logging(args):
    """设置日志"""
    log_level = args.log_level
    log_path = args.log_path

    # 转换日志级别
    import logging
    level = getattr(logging, log_level)

    # 创建日志目录
    Path(log_path).mkdir(parents=True, exist_ok=True)

    # 设置默认日志
    logger = setup_default_logger(level)
    logger.setLevel(level)

    return logger


def write_pid_file(pid_file: str):
    """写入PID文件"""
    try:
        Path(pid_file).parent.mkdir(parents=True, exist_ok=True)
        with open(pid_file, "w") as f:
            f.write(str(os.getpid()))
    except Exception as e:
        logger = get_logger("main")
        logger.error(f"写入PID文件失败: {e}")


def remove_pid_file(pid_file: str):
    """删除PID文件"""
    try:
        if Path(pid_file).exists():
            Path(pid_file).unlink()
    except Exception as e:
        logger = get_logger("main")
        logger.error(f"删除PID文件失败: {e}")


def check_daemon_running(pid_file: str) -> bool:
    """检查守护进程是否运行"""
    if not Path(pid_file).exists():
        return False

    try:
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())

        # 检查进程是否存在
        if sys.platform == "win32":
            import ctypes
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(1, 0, pid)
            if handle:
                kernel32.CloseHandle(handle)
                return True
            return False
        else:
            os.kill(pid, 0)
            return True
    except (OSError, ValueError):
        return False


def stop_daemon(pid_file: str):
    """停止守护进程"""
    if not Path(pid_file).exists():
        logger = get_logger("main")
        logger.error(f"PID文件不存在: {pid_file}")
        return False

    try:
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())

        logger = get_logger("main")
        logger.info(f"停止守护进程 (PID: {pid})...")

        if sys.platform == "win32":
            import ctypes
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(1, False, pid)
            if handle:
                kernel32.TerminateProcess(handle, -1)
                kernel32.CloseHandle(handle)
        else:
            os.kill(pid, signal.SIGTERM)

        # 等待进程结束
        import time
        for _ in range(10):
            try:
                os.kill(pid, 0)
                time.sleep(0.5)
            except OSError:
                break

        remove_pid_file(pid_file)
        logger.info("守护进程已停止")
        return True

    except Exception as e:
        logger = get_logger("main")
        logger.error(f"停止守护进程失败: {e}")
        return False


def show_status(pid_file: str, config_path: str):
    """显示运行状态"""
    logger = get_logger("main")

    if not Path(pid_file).exists():
        logger.info("守护进程未运行")
        return

    try:
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())

        running = check_daemon_running(pid_file)

        if running:
            logger.info(f"守护进程运行中 (PID: {pid})")
        else:
            logger.info(f"守护进程已停止 (PID: {pid})")
            logger.info("可能需要清理PID文件")

        # 显示配置信息
        logger.info(f"配置文件: {config_path}")

    except Exception as e:
        logger.error(f"获取状态失败: {e}")


def reload_config(pid_file: str):
    """重新加载配置"""
    logger = get_logger("main")

    if not check_daemon_running(pid_file):
        logger.error("守护进程未运行")
        return False

    try:
        # 发送重载信号
        if sys.platform == "win32":
            logger.warning("Windows不支持配置热重载，请重启守护进程")
            return False
        else:
            with open(pid_file, "r") as f:
                pid = int(f.read().strip())

            os.kill(pid, signal.SIGHUP)
            logger.info("已发送配置重载信号")
            return True

    except Exception as e:
        logger.error(f"重载配置失败: {e}")
        return False


def main():
    """主函数"""
    args = parse_arguments()

    # 设置日志
    logger = setup_logging(args)

    # 处理特殊操作
    if args.pid:
        if args.status:
            show_status(args.pid, args.config)
            return 0

        if args.stop:
            if stop_daemon(args.pid):
                return 0
            else:
                return 1

        if args.reload:
            if reload_config(args.pid):
                return 0
            else:
                return 1

        # 检查是否已运行
        if check_daemon_running(args.pid):
            logger.error(f"守护进程已在运行 (PID文件: {args.pid})")
            return 1

    # 创建守护进程实例
    daemon = SecurityDaemon(args.config)

    # 写入PID文件
    if args.pid:
        write_pid_file(args.pid)

    # 注册信号处理
    def shutdown_handler(signum, frame):
        signal_name = signal.Signals(signum).name
        logger.info(f"收到信号: {signal_name}")
        daemon.shutdown()
        if args.pid:
            remove_pid_file(args.pid)
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    # 运行守护进程
    try:
        daemon.run()
        return 0
    except Exception as e:
        logger.error(f"守护进程异常: {e}")
        if args.pid:
            remove_pid_file(args.pid)
        return 1


if __name__ == "__main__":
    sys.exit(main())
