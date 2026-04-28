"""
关联分析器
Correlation Analyzer
"""

import time
from typing import Any, Dict, List, Optional, Tuple
from collections import deque, defaultdict
from dataclasses import dataclass
from datetime import datetime

from .base_analyzer import BaseAnalyzer
from ..core.event_bus import EventBus
from ..utils.logger import get_logger


@dataclass
class CorrelationEvent:
    """关联事件"""
    timestamp: float
    threat_type: str
    source: str
    severity: str
    data: Dict[str, Any]


class CorrelationAnalyzer(BaseAnalyzer):
    """关联分析器"""

    def __init__(self, event_bus: EventBus):
        super().__init__(event_bus)
        self.name = "CorrelationAnalyzer"

        # 事件时间窗口（秒）
        self.time_window = 30.0
        self.event_history: deque = deque(maxlen=1000)

        # 关联规则
        self.correlation_rules: List[Dict[str, Any]] = []

        # 统计信息
        self.processed_count = 0
        self.correlations_found = 0

        # 攻击链检测
        self.attack_tracking: Dict[str, List[Tuple]] = defaultdict(list)

    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化分析器"""
        self.time_window = config.get("time_window", 30.0)

        # 加载默认关联规则
        self._load_default_rules()

        # 订阅威胁事件
        self._subscribe_to_events()

        self.initialized = True
        self.logger.info(f"关联分析器初始化完成 (时间窗口: {self.time_window}s)")
        return True

    def _load_default_rules(self) -> None:
        """加载默认关联规则"""
        # GPS欺骗 + 位置跳变组合
        self.correlation_rules.append({
            "name": "gps_spoofing_chain",
            "threat_types": ["gps_spoofing", "gps_position_jump"],
            "time_window": 10.0,
            "min_occurrences": 2,
            "severity_boost": 1
        })

        # MAVLink劫持 + 命令注入组合
        self.correlation_rules.append({
            "name": "mavlink_hijack_chain",
            "threat_types": ["mavlink_hijacking", "mavlink_command_injection"],
            "time_window": 5.0,
            "min_occurrences": 2,
            "severity_boost": 2
        })

        # 高频威胁（可能的大规模攻击）
        self.correlation_rules.append({
            "name": "high_frequency_threats",
            "threat_types": ["any"],
            "time_window": 5.0,
            "min_occurrences": 10,
            "severity_boost": 1
        })

    def _subscribe_to_events(self) -> None:
        """订阅事件"""
        self.event_bus.subscribe(
            "threat.detected",
            self._on_threat_detected
        )

    def _on_threat_detected(self, event) -> None:
        """威胁检测事件处理"""
        try:
            if isinstance(event.data, dict):
                threat_event = CorrelationEvent(
                    timestamp=event.data.get("timestamp", time.time()),
                    threat_type=event.data.get("threat_type", ""),
                    source=event.data.get("source", ""),
                    severity=event.data.get("severity", ""),
                    data=event.data
                )

                self.event_history.append(threat_event)
                self._check_correlations(threat_event)

        except Exception as e:
            self.logger.error(f"处理威胁事件失败: {e}")

    def analyze(self, data: Any) -> Optional[Dict[str, Any]]:
        """分析数据（被动模式）"""
        if not self.enabled:
            return None

        # 主要通过事件订阅工作
        return None

    def _check_correlations(self, event: CorrelationEvent) -> None:
        """检查关联"""
        now = time.time()

        # 获取时间窗口内的事件
        recent_events = [
            e for e in self.event_history
            if now - e.timestamp <= self.time_window
        ]

        # 检查每个关联规则
        for rule in self.correlation_rules:
            correlation = self._check_rule(rule, recent_events, event)
            if correlation:
                self.correlations_found += 1
                self._report_correlation(correlation)

    def _check_rule(
        self,
        rule: Dict[str, Any],
        events: List[CorrelationEvent],
        current_event: CorrelationEvent
    ) -> Optional[Dict[str, Any]]:
        """检查关联规则"""
        threat_types = rule["threat_types"]
        time_window = rule["time_window"]
        min_occurrences = rule["min_occurrences"]

        # 统计匹配的事件
        matching_events = []

        if "any" in threat_types:
            # 任何威胁类型
            matching_events = events
        else:
            # 特定威胁类型
            for evt in events:
                if evt.threat_type in threat_types:
                    matching_events.append(evt)

        # 检查是否满足条件
        if len(matching_events) >= min_occurrences:
            return {
                "rule_name": rule["name"],
                "matched_events": len(matching_events),
                "min_required": min_occurrences,
                "time_window": time_window,
                "severity_boost": rule["severity_boost"],
                "threat_types": list(set(e.threat_type for e in matching_events)),
                "sources": list(set(e.source for e in matching_events)),
                "first_event_time": min(e.timestamp for e in matching_events),
                "last_event_time": max(e.timestamp for e in matching_events)
            }

        return None

    def _report_correlation(self, correlation: Dict[str, Any]) -> None:
        """报告关联"""
        self.logger.warning(
            f"检测到攻击关联: {correlation['rule_name']} "
            f"(事件: {correlation['matched_events']})"
        )

        # 发布关联事件
        self.event_bus.publish_sync(
            "threat.correlation",
            {
                "analyzer": self.name,
                "correlation": correlation
            }
        )

    def _detect_attack_chain(self, events: List[CorrelationEvent]) -> Optional[List[str]]:
        """检测攻击链"""
        if len(events) < 2:
            return None

        # 简化的攻击链检测
        chain = []

        # GPS攻击链
        gps_events = [e for e in events if "gps" in e.threat_type]
        if len(gps_events) >= 2:
            chain.append("gps_attack_chain")

        # MAVLink攻击链
        mavlink_events = [e for e in events if "mavlink" in e.threat_type]
        if len(mavlink_events) >= 2:
            chain.append("mavlink_attack_chain")

        # DoS攻击链
        dos_events = [e for e in events if "dos" in e.threat_type]
        if len(dos_events) >= 3:
            chain.append("dos_attack_chain")

        return chain if chain else None

    def get_event_summary(self) -> Dict[str, Any]:
        """获取事件摘要"""
        now = time.time()

        # 统计各类威胁数量
        threat_counts = defaultdict(int)
        source_counts = defaultdict(int)

        for event in self.event_history:
            if now - event.timestamp <= 300:  # 5分钟内
                threat_counts[event.threat_type] += 1
                source_counts[event.source] += 1

        return {
            "total_events": len(self.event_history),
            "recent_threats": dict(threat_counts),
            "recent_sources": dict(source_counts),
            "correlations_found": self.correlations_found
        }

    def cleanup(self) -> None:
        """清理资源"""
        self.event_history.clear()
        self.attack_tracking.clear()
        self.logger.info(f"关联分析器已清理 (处理: {self.processed_count}, 关联: {self.correlations_found})")

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "processed_count": self.processed_count,
            "correlations_found": self.correlations_found,
            "time_window": self.time_window,
            "event_history_size": len(self.event_history),
            "rules_loaded": len(self.correlation_rules)
        }
