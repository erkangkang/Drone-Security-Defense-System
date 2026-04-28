"""
检测器基类
Base Detector
"""

import threading
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass

from ..core.event_bus import EventBus
from ..core.config_manager import DetectorConfig
from ..utils.logger import get_logger
from ..utils.time_utils import TimeUtils
from ..models.threat_event import ThreatEvent, Severity


@dataclass
class DetectorStats:
    """检测器统计信息"""
    processed_count: int = 0
    detected_count: int = 0
    error_count: int = 0
    last_process_time: float = 0.0


class BaseDetector(ABC):
    """检测器基类"""

    def __init__(
        self,
        event_bus: EventBus,
        config: DetectorConfig
    ):
        self.event_bus = event_bus
        self.config = config
        self.name = self.__class__.__name__

        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.stats = DetectorStats()

        self.logger = get_logger("detector")

    @abstractmethod
    def initialize(self) -> bool:
        """初始化检测器"""
        pass

    @abstractmethod
    def analyze(self, data: Any) -> Optional[ThreatEvent]:
        """分析数据，返回威胁事件"""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """清理资源"""
        pass

    def start(self) -> bool:
        """启动检测器"""
        if self.running:
            self.logger.warning(f"{self.name} 已在运行")
            return False

        self.running = True

        if self.config.interval > 0:
            # 启动独立线程
            self.thread = threading.Thread(
                target=self._run_loop,
                name=self.name,
                daemon=True
            )
            self.thread.start()
            self.logger.info(f"{self.name} 已启动（间隔: {self.config.interval}s）")
        else:
            self.logger.info(f"{self.name} 已启动（被动模式）")

        return True

    def stop(self) -> bool:
        """停止检测器"""
        if not self.running:
            return False

        self.running = False

        if self.thread:
            self.thread.join(timeout=5.0)
            self.thread = None

        self.cleanup()
        self.logger.info(f"{self.name} 已停止")
        return True

    def _run_loop(self):
        """运行循环"""
        while self.running:
            try:
                self._loop_iteration()
            except Exception as e:
                self.logger.error(f"{self.name} 运行错误: {e}")
                self.stats.error_count += 1

            time.sleep(self.config.interval)

    @abstractmethod
    def _loop_iteration(self):
        """单次迭代"""
        pass

    def process_data(self, data: Any) -> Optional[ThreatEvent]:
        """处理数据"""
        try:
            start_time = time.time()
            threat_event = self.analyze(data)

            self.stats.processed_count += 1
            self.stats.last_process_time = time.time() - start_time

            if threat_event:
                self._handle_threat(threat_event)

            return threat_event

        except Exception as e:
            self.logger.error(f"{self.name} 数据处理错误: {e}")
            self.stats.error_count += 1
            return None

    def _handle_threat(self, threat_event: ThreatEvent) -> None:
        """处理检测到的威胁"""
        self.stats.detected_count += 1

        # 发布威胁事件
        self.event_bus.publish_sync(
            "threat.detected",
            {
                "threat_type": threat_event.threat_type,
                "severity": threat_event.severity.value,
                "detector": threat_event.detector,
                "confidence": threat_event.confidence,
                "evidence": threat_event.evidence
            }
        )

        # 发布原始事件
        self.event_bus.publish_sync(
            "threat.raw",
            threat_event.to_dict()
        )

        self.logger.warning(
            f"检测到威胁: {threat_event.threat_type} "
            f"(置信度: {threat_event.confidence:.2f})"
        )

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "name": self.name,
            "running": self.running,
            "processed_count": self.stats.processed_count,
            "detected_count": self.stats.detected_count,
            "error_count": self.stats.error_count,
            "detection_rate": self._calculate_detection_rate(),
            "last_process_time": self.stats.last_process_time
        }

    def _calculate_detection_rate(self) -> float:
        """计算检测率"""
        if self.stats.processed_count == 0:
            return 0.0
        return (self.stats.detected_count / self.stats.processed_count) * 100

    def reset_stats(self) -> None:
        """重置统计信息"""
        self.stats = DetectorStats()
