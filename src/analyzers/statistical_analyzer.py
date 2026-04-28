"""
统计分析器
Statistical Analyzer
"""

import math
from typing import Any, Dict, List, Optional, Tuple
from collections import deque

from .base_analyzer import BaseAnalyzer
from ..core.event_bus import EventBus
from ..utils.logger import get_logger


class StatisticalAnomalyDetector:
    """统计异常检测器"""

    @staticmethod
    def z_score(value: float, mean: float, std: float) -> float:
        """计算Z-score"""
        if std == 0:
            return 0.0
        return (value - mean) / std

    @staticmethod
    def detect_outliers_zscore(data: List[float], threshold: float = 3.0) -> List[int]:
        """使用Z-score检测异常值"""
        if len(data) < 2:
            return []

        mean = sum(data) / len(data)
        std = math.sqrt(sum((x - mean) ** 2 for x in data) / len(data))

        outliers = []
        for i, value in enumerate(data):
            z_score = StatisticalAnomalyDetector.z_score(value, mean, std)
            if abs(z_score) > threshold:
                outliers.append(i)

        return outliers

    @staticmethod
    def detect_outliers_iqr(data: List[float], multiplier: float = 1.5) -> List[int]:
        """使用IQR检测异常值"""
        if len(data) < 4:
            return []

        sorted_data = sorted(data)
        n = len(sorted_data)

        q1 = sorted_data[n // 4]
        q3 = sorted_data[3 * n // 4]
        iqr = q3 - q1

        lower_bound = q1 - multiplier * iqr
        upper_bound = q3 + multiplier * iqr

        outliers = []
        for i, value in enumerate(data):
            if value < lower_bound or value > upper_bound:
                outliers.append(i)

        return outliers

    @staticmethod
    def moving_average(data: List[float], window: int = 5) -> List[float]:
        """计算移动平均"""
        if window <= 0 or len(data) < window:
            return [sum(data) / len(data)] if data else []

        result = []
        for i in range(len(data) - window + 1):
            window_data = data[i:i + window]
            result.append(sum(window_data) / window)

        return result

    @staticmethod
    def calculate_confidence_interval(
        data: List[float],
        confidence: float = 0.95
    ) -> Tuple[float, float]:
        """计算置信区间"""
        if len(data) < 2:
            return 0.0, 0.0

        mean = sum(data) / len(data)
        std = math.sqrt(sum((x - mean) ** 2 for x in data) / (len(data) - 1))

        # 简化的置信区间计算
        import math
        z_score = {
            0.90: 1.645,
            0.95: 1.960,
            0.99: 2.576
        }.get(confidence, 1.960)

        margin = z_score * std / math.sqrt(len(data))

        return mean - margin, mean + margin


class StatisticalAnalyzer(BaseAnalyzer):
    """统计分析器"""

    def __init__(self, event_bus: EventBus):
        super().__init__(event_bus)
        self.name = "StatisticalAnalyzer"

        # 数据窗口
        self.window_size = 100
        self.data_windows: Dict[str, deque] = {}

        # 统计信息
        self.processed_count = 0
        self.anomalies_detected = 0

        # 配置
        self.outlier_threshold = 3.0  # Z-score阈值
        self.outlier_method = "zscore"  # zscore 或 iqr

    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化分析器"""
        self.window_size = config.get("window_size", 100)
        self.outlier_threshold = config.get("outlier_threshold", 3.0)
        self.outlier_method = config.get("outlier_method", "zscore")

        self.initialized = True
        self.logger.info(f"统计分析器初始化完成 (窗口大小: {self.window_size})")
        return True

    def analyze(self, data: Any) -> Optional[Dict[str, Any]]:
        """分析数据"""
        if not self.enabled:
            return None

        # 处理数值列表
        if isinstance(data, list) and all(isinstance(x, (int, float)) for x in data):
            return self._analyze_numeric_list(data)

        # 处理字典中的数值
        elif isinstance(data, dict):
            return self._analyze_dict(data)

        return None

    def _analyze_numeric_list(self, data: List[float]) -> Optional[Dict[str, Any]]:
        """分析数值列表"""
        if len(data) < 3:
            return None

        result = {
            "analyzer": self.name,
            "data_type": "numeric_list",
            "count": len(data),
            "statistics": {},
            "anomalies": []
        }

        # 基本统计
        mean = sum(data) / len(data)
        result["statistics"]["mean"] = mean

        if len(data) > 1:
            variance = sum((x - mean) ** 2 for x in data) / len(data)
            std = math.sqrt(variance)

            result["statistics"]["std"] = std
            result["statistics"]["min"] = min(data)
            result["statistics"]["max"] = max(data)
            result["statistics"]["median"] = sorted(data)[len(data) // 2]

        # 检测异常值
        if self.outlier_method == "zscore":
            outlier_indices = StatisticalAnomalyDetector.detect_outliers_zscore(
                data, self.outlier_threshold
            )
        else:
            outlier_indices = StatisticalAnomalyDetector.detect_outliers_iqr(
                data, self.outlier_threshold
            )

        for idx in outlier_indices:
            result["anomalies"].append({
                "index": idx,
                "value": data[idx],
                "z_score": StatisticalAnomalyDetector.z_score(
                    data[idx], mean, result["statistics"].get("std", 0.0)
                ) if result["statistics"].get("std", 0.0) > 0 else 0.0
            })

        self.processed_count += 1
        if result["anomalies"]:
            self.anomalies_detected += len(result["anomalies"])

        return result

    def _analyze_dict(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """分析字典数据"""
        result = {
            "analyzer": self.name,
            "data_type": "dict",
            "fields": {}
        }

        for key, value in data.items():
            if isinstance(value, (int, float)):
                # 更新数据窗口
                if key not in self.data_windows:
                    self.data_windows[key] = deque(maxlen=self.window_size)

                self.data_windows[key].append(float(value))

                # 如果有足够的数据，分析
                if len(self.data_windows[key]) >= 10:
                    window_data = list(self.data_windows[key])
                    analysis = self._analyze_numeric_list(window_data)

                    if analysis:
                        result["fields"][key] = {
                            "current_value": value,
                            "statistics": analysis.get("statistics", {}),
                            "anomalies": analysis.get("anomalies", [])
                        }

        self.processed_count += 1
        return result

    def cleanup(self) -> None:
        """清理资源"""
        self.data_windows.clear()
        self.logger.info(f"统计分析器已清理 (处理: {self.processed_count}, 异常: {self.anomalies_detected})")

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "processed_count": self.processed_count,
            "anomalies_detected": self.anomalies_detected,
            "window_size": self.window_size,
            "outlier_threshold": self.outlier_threshold,
            "outlier_method": self.outlier_method
        }

    def reset_statistics(self) -> None:
        """重置统计信息"""
        self.processed_count = 0
        self.anomalies_detected = 0
        self.data_windows.clear()
