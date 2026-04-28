"""
机器学习分析器
ML Analyzer
"""

import time
from typing import Any, Dict, List, Optional
from collections import deque

from .base_analyzer import BaseAnalyzer
from ..core.event_bus import EventBus
from ..utils.logger import get_logger


class MLAnalyzer(BaseAnalyzer):
    """机器学习分析器"""

    def __init__(self, event_bus: EventBus):
        super().__init__(event_bus)
        self.name = "MLAnalyzer"

        # 模型
        self.model = None
        self.model_path = ""
        self.model_loaded = False

        # 特征提取
        self.feature_window_size = 50
        self.feature_history: deque = deque(maxlen=1000)

        # 统计
        self.predictions_made = 0
        self.threats_detected = 0

        # 配置
        self.confidence_threshold = 0.7

    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化分析器"""
        self.model_path = config.get("model_path", "")
        self.confidence_threshold = config.get("confidence_threshold", 0.7)
        self.feature_window_size = config.get("feature_window_size", 50)

        # 尝试加载模型
        if self.model_path:
            self._load_model(self.model_path)
        else:
            self.logger.info("未指定模型路径，ML分析器将在被动模式运行")

        self.initialized = True
        self.logger.info(f"ML分析器初始化完成 (模型: {self.model_loaded})")
        return True

    def _load_model(self, model_path: str) -> bool:
        """加载机器学习模型"""
        try:
            import pickle
            from pathlib import Path

            if not Path(model_path).exists():
                self.logger.warning(f"模型文件不存在: {model_path}")
                return False

            with open(model_path, "rb") as f:
                self.model = pickle.load(f)

            self.model_loaded = True
            self.logger.info(f"模型加载成功: {model_path}")
            return True

        except Exception as e:
            self.logger.error(f"模型加载失败: {e}")
            return False

    def analyze(self, data: Any) -> Optional[Dict[str, Any]]:
        """分析数据"""
        if not self.enabled or not self.model_loaded:
            return None

        # 提取特征
        features = self._extract_features(data)
        if not features:
            return None

        # 记录特征历史
        self.feature_history.append(features)

        # 进行预测
        prediction = self._predict(features)

        if prediction:
            self.predictions_made += 1
            if prediction.get("is_threat", False):
                self.threats_detected += 1

        return prediction

    def _extract_features(self, data: Any) -> Optional[List[float]]:
        """提取特征"""
        features = []

        # 处理数值列表
        if isinstance(data, list) and all(isinstance(x, (int, float)) for x in data):
            if len(data) < 3:
                return None

            # 基本统计特征
            mean = sum(data) / len(data)
            variance = sum((x - mean) ** 2 for x in data) / len(data)
            std = variance ** 0.5 if variance > 0 else 0

            features.extend([
                mean,
                std,
                min(data),
                max(data),
                sorted(data)[len(data) // 2]  # median
            ])

        # 处理字典
        elif isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (int, float)):
                    features.append(float(value))

        # 处理对象
        elif hasattr(data, "__dict__"):
            for attr in dir(data):
                if not attr.startswith("_"):
                    value = getattr(data, attr)
                    if isinstance(value, (int, float)):
                        features.append(float(value))

        # 填充特征向量到固定长度
        max_features = 20
        if len(features) < max_features:
            features.extend([0.0] * (max_features - len(features)))
        else:
            features = features[:max_features]

        return features

    def _predict(self, features: List[float]) -> Optional[Dict[str, Any]]:
        """使用模型进行预测"""
        try:
            if self.model is None:
                return None

            # 根据模型类型进行预测
            if hasattr(self.model, "predict_proba"):
                # 有概率输出的模型
                proba = self.model.predict_proba([features])[0]
                is_threat = max(proba) > self.confidence_threshold
                confidence = max(proba)

                return {
                    "is_threat": is_threat,
                    "confidence": confidence,
                    "prediction": int(is_threat),
                    "probabilities": proba.tolist() if hasattr(proba, "tolist") else list(proba)
                }

            elif hasattr(self.model, "predict"):
                # 只有预测输出的模型
                prediction = int(self.model.predict([features])[0])
                is_threat = prediction == 1

                return {
                    "is_threat": is_threat,
                    "confidence": 1.0 if is_threat else 0.0,
                    "prediction": prediction
                }

        except Exception as e:
            self.logger.error(f"预测失败: {e}")

        return None

    def cleanup(self) -> None:
        """清理资源"""
        self.feature_history.clear()
        self.model = None
        self.model_loaded = False
        self.logger.info(f"ML分析器已清理 (预测: {self.predictions_made}, 威胁: {self.threats_detected})")

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "model_loaded": self.model_loaded,
            "model_path": self.model_path,
            "predictions_made": self.predictions_made,
            "threats_detected": self.threats_detected,
            "detection_rate": (
                (self.threats_detected / self.predictions_made * 100)
                if self.predictions_made > 0 else 0.0
            ),
            "confidence_threshold": self.confidence_threshold,
            "feature_history_size": len(self.feature_history)
        }

    def train_model(self, training_data: List[Any], labels: List[int]) -> bool:
        """训练模型（简化实现）"""
        try:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import accuracy_score

            # 提取特征
            features_list = []
            for data in training_data:
                features = self._extract_features(data)
                if features:
                    features_list.append(features)

            if len(features_list) == 0:
                self.logger.error("无法提取训练特征")
                return False

            # 划分训练集和测试集
            X_train, X_test, y_train, y_test = train_test_split(
                features_list, labels, test_size=0.2, random_state=42
            )

            # 训练模型
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.model.fit(X_train, y_train)

            # 评估模型
            y_pred = self.model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)

            self.model_loaded = True
            self.logger.info(f"模型训练完成，准确率: {accuracy:.2f}")
            return True

        except ImportError:
            self.logger.warning("scikit-learn未安装，无法训练模型")
            return False
        except Exception as e:
            self.logger.error(f"模型训练失败: {e}")
            return False

    def save_model(self, path: str) -> bool:
        """保存模型"""
        if not self.model_loaded:
            self.logger.error("没有可保存的模型")
            return False

        try:
            import pickle

            with open(path, "wb") as f:
                pickle.dump(self.model, f)

            self.logger.info(f"模型已保存: {path}")
            return True

        except Exception as e:
            self.logger.error(f"模型保存失败: {e}")
            return False
