"""
时间工具
Time Utility
"""

import time
from datetime import datetime, timedelta
from typing import Optional


class TimeUtils:
    """时间工具类"""

    @staticmethod
    def now() -> datetime:
        """获取当前UTC时间"""
        return datetime.utcnow()

    @staticmethod
    def now_timestamp() -> float:
        """获取当前时间戳"""
        return time.time()

    @staticmethod
    def now_ms() -> int:
        """获取当前时间戳（毫秒）"""
        return int(time.time() * 1000)

    @staticmethod
    def timestamp_to_datetime(ts: float) -> datetime:
        """时间戳转datetime"""
        return datetime.utcfromtimestamp(ts)

    @staticmethod
    def datetime_to_timestamp(dt: datetime) -> float:
        """datetime转时间戳"""
        return dt.timestamp()

    @staticmethod
    def format_duration(seconds: float) -> str:
        """格式化持续时间"""
        if seconds < 1:
            return f"{seconds * 1000:.2f}ms"
        elif seconds < 60:
            return f"{seconds:.2f}s"
        elif seconds < 3600:
            return f"{seconds / 60:.2f}m"
        else:
            return f"{seconds / 3600:.2f}h"

    @staticmethod
    def time_elapsed(start: float) -> float:
        """计算经过的时间"""
        return time.time() - start

    @staticmethod
    def time_elapsed_ms(start: float) -> int:
        """计算经过的时间（毫秒）"""
        return int((time.time() - start) * 1000)

    @staticmethod
    def sleep(seconds: float):
        """睡眠"""
        time.sleep(seconds)

    @staticmethod
    def is_expired(timestamp: datetime, ttl: int) -> bool:
        """检查是否过期"""
        return datetime.utcnow() - timestamp > timedelta(seconds=ttl)

    @staticmethod
    def time_delta_to_seconds(delta: timedelta) -> float:
        """时间差转秒数"""
        return delta.total_seconds()

    @staticmethod
    def to_iso_string(dt: Optional[datetime] = None) -> str:
        """转ISO字符串"""
        if dt is None:
            dt = datetime.utcnow()
        return dt.isoformat()

    @staticmethod
    def from_iso_string(iso_str: str) -> datetime:
        """从ISO字符串解析"""
        return datetime.fromisoformat(iso_str.replace("Z", "+00:00"))


class Timer:
    """计时器"""

    def __init__(self):
        self.start_time = None
        self.end_time = None

    def start(self):
        """开始计时"""
        self.start_time = time.time()
        self.end_time = None

    def stop(self) -> float:
        """停止计时并返回用时"""
        if self.start_time is None:
            return 0.0
        self.end_time = time.time()
        return self.end_time - self.start_time

    def elapsed(self) -> float:
        """获取已用时间"""
        if self.start_time is None:
            return 0.0
        end = self.end_time or time.time()
        return end - self.start_time

    def reset(self):
        """重置计时器"""
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


def measure_time(func):
    """测量函数执行时间的装饰器"""
    def wrapper(*args, **kwargs):
        timer = Timer()
        timer.start()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            elapsed = timer.elapsed()
            from .logger import get_logger
            logger = get_logger("timing")
            logger.debug(f"{func.__name__} executed in {TimeUtils.format_duration(elapsed)}")
    return wrapper
