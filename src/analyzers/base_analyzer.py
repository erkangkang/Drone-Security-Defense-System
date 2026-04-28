"""
分析器基类
Base Analyzer
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..core.event_bus import EventBus
from ..utils.logger import get_logger


class BaseAnalyzer(ABC):
    """分析器基类"""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.name = self.__class__.__name__
        self.logger = get_logger("analyzer")

        self.enabled = True
        self.initialized = False

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化分析器"""
        pass

    @abstractmethod
    def analyze(self, data: Any) -> Optional[Dict[str, Any]]:
        """分析数据"""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """清理资源"""
        pass

    def enable(self) -> None:
        """启用分析器"""
        self.enabled = True
        self.logger.info(f"{self.name} 已启用")

    def disable(self) -> None:
        """禁用分析器"""
        self.enabled = False
        self.logger.info(f"{self.name} 已禁用")

    def is_enabled(self) -> bool:
        """检查是否启用"""
        return self.enabled

    def get_name(self) -> str:
        """获取分析器名称"""
        return self.name

    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "initialized": self.initialized
        }
