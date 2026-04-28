"""
日志工具
Logger Utility
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


class SecurityLogger:
    """安全日志器"""

    _instance: Optional["SecurityLogger"] = None
    _loggers: dict = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.default_log_dir = Path("logs")

    def setup_logger(
        self,
        name: str,
        log_file: Optional[str] = None,
        level: int = logging.INFO,
        console_output: bool = True,
        log_format: Optional[str] = None
    ) -> logging.Logger:
        """设置日志器"""

        if name in self._loggers:
            return self._loggers[name]

        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.handlers.clear()

        if log_format is None:
            log_format = "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"

        formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")

        # 文件处理器
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

            # 轮转处理器（简单实现）
            if log_path.stat().st_size > 10 * 1024 * 1024:  # 10MB
                backup_path = log_path.with_suffix(f".{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.bak")
                log_path.rename(backup_path)

        # 控制台处理器
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        self._loggers[name] = logger
        return logger

    def get_logger(self, name: str) -> logging.Logger:
        """获取日志器"""
        if name not in self._loggers:
            return self.setup_logger(name)
        return self._loggers[name]

    def close_all(self):
        """关闭所有日志器"""
        for logger in self._loggers.values():
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)
        self._loggers.clear()


def get_logger(name: str = "security") -> logging.Logger:
    """获取日志器（便捷函数）"""
    return SecurityLogger().get_logger(name)


def setup_default_logger(level: int = logging.INFO) -> logging.Logger:
    """设置默认日志器"""
    logger_instance = SecurityLogger()
    return logger_instance.setup_logger(
        name="security",
        log_file="logs/security.log",
        level=level,
        console_output=True
    )
