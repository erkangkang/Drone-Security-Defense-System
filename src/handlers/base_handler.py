"""
处理器基类
Base Handler
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ..core.event_bus import EventBus
from ..utils.logger import get_logger


class BaseHandler(ABC):
    """处理器基类"""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.name = self.__class__.__name__
        self.logger = get_logger("handler")

        self.enabled = True
        self.subscription_id: Optional[str] = None

    @abstractmethod
    def initialize(self) -> bool:
        """初始化处理器"""
        pass

    @abstractmethod
    def handle(self, data: Any) -> None:
        """处理数据"""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """清理资源"""
        pass

    def enable(self) -> None:
        """启用处理器"""
        self.enabled = True
        self.logger.info(f"{self.name} 已启用")

    def disable(self) -> None:
        """禁用处理器"""
        self.enabled = False
        self.logger.info(f"{self.name} 已禁用")

    def is_enabled(self) -> bool:
        """检查是否启用"""
        return self.enabled

    def get_name(self) -> str:
        """获取处理器名称"""
        return self.name

    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "subscribed": self.subscription_id is not None
        }
