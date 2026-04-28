"""
固件完整性检测器
Firmware Integrity Detector
"""

import hashlib
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass

from .base_detector import BaseDetector
from ..core.event_bus import EventBus
from ..core.config_manager import DetectorConfig
from ..utils.logger import get_logger
from ..utils.crypto import CryptoUtils
from ..models.threat_event import ThreatEvent, Severity, ThreatType


@dataclass
class FirmwareInfo:
    """固件信息"""
    firmware_path: str
    expected_hash: str
    algorithm: str = "sha256"
    last_check_time: float = 0.0
    current_hash: str = ""


class FirmwareDetector(BaseDetector):
    """固件完整性检测器"""

    def __init__(self, event_bus: EventBus, config: DetectorConfig):
        super().__init__(event_bus, config)
        self.name = "FirmwareDetector"

        # 固件信息
        self.firmware_info: Optional[FirmwareInfo] = None

        # 配置
        self.check_interval = config.settings.get("check_interval", 3600)  # 秒
        self.firmware_path = config.settings.get("firmware_path", "")
        self.expected_hash = config.settings.get("expected_hash", "")
        self.signature_required = config.settings.get("signature_required", False)
        self.signature_path = config.settings.get("signature_path", "")
        self.public_key_path = config.settings.get("public_key_path", "")

        # 状态
        self.integrity_ok = True
        self.last_check_time = 0.0
        self.check_count = 0

    def initialize(self) -> bool:
        """初始化检测器"""
        if not self.firmware_path:
            self.logger.warning("未配置固件路径，检测器将被动运行")
            return True

        self.firmware_info = FirmwareInfo(
            firmware_path=self.firmware_path,
            expected_hash=self.expected_hash
        )

        # 首次检查
        self._check_firmware_integrity()

        self.logger.info("固件检测器初始化完成")
        return True

    def analyze(self, data: Any) -> Optional[ThreatEvent]:
        """分析固件数据"""
        # 如果是被动调用（收到固件数据），立即检查
        if isinstance(data, dict):
            firmware_path = data.get("firmware_path")
            if firmware_path:
                self.firmware_path = firmware_path
                self.firmware_info = FirmwareInfo(
                    firmware_path=firmware_path,
                    expected_hash=data.get("expected_hash", "")
                )
                return self._check_firmware_integrity()

        return None

    def _check_firmware_integrity(self) -> Optional[ThreatEvent]:
        """检查固件完整性"""
        if not self.firmware_info or not os.path.exists(self.firmware_info.firmware_path):
            return None

        self.check_count += 1
        now = time.time()
        self.last_check_time = now

        try:
            # 计算当前哈希
            current_hash = CryptoUtils.hash_file(
                self.firmware_info.firmware_path,
                self.firmware_info.algorithm
            )
            self.firmware_info.current_hash = current_hash
            self.firmware_info.last_check_time = now

            # 如果没有预期哈希，记录当前哈希
            if not self.firmware_info.expected_hash:
                self.logger.info(f"首次固件检查，记录哈希: {current_hash}")
                self.firmware_info.expected_hash = current_hash
                self.integrity_ok = True
                return None

            # 比较哈希
            if current_hash != self.firmware_info.expected_hash:
                self.integrity_ok = False
                self.logger.error(f"固件完整性检查失败！预期: {self.firmware_info.expected_hash}, 实际: {current_hash}")

                return ThreatEvent(
                    threat_type=ThreatType.FIRMWARE_TAMPERING.value,
                    severity=Severity.CRITICAL,
                    detector=self.name,
                    source=self.firmware_info.firmware_path,
                    evidence={
                        "expected_hash": self.firmware_info.expected_hash,
                        "current_hash": current_hash,
                        "algorithm": self.firmware_info.algorithm,
                        "firmware_path": self.firmware_info.firmware_path
                    },
                    confidence=1.0
                )
            else:
                self.integrity_ok = True
                self.logger.debug("固件完整性检查通过")

        except Exception as e:
            self.logger.error(f"固件完整性检查失败: {e}")

        return None

    def _check_signature(self) -> Optional[ThreatEvent]:
        """检查固件签名"""
        if not self.signature_required:
            return None

        if not self.signature_path or not self.public_key_path:
            self.logger.warning("签名验证已启用但未配置签名文件或公钥")
            return None

        if not os.path.exists(self.signature_path) or not os.path.exists(self.public_key_path):
            self.logger.warning("签名文件或公钥文件不存在")
            return None

        try:
            # 这里简化实现，实际应该使用完整的签名验证
            # 可以使用 OpenSSL 或 cryptography 库
            self.logger.info("固件签名检查（简化实现）")
            # 实际实现需要:
            # 1. 读取公钥
            # 2. 读取签名
            # 3. 读取固件
            # 4. 验证签名

        except Exception as e:
            self.logger.error(f"签名验证失败: {e}")
            return ThreatEvent(
                threat_type=ThreatType.FIRMWARE_TAMPERING.value,
                severity=Severity.CRITICAL,
                detector=self.name,
                source=self.firmware_info.firmware_path if self.firmware_info else "unknown",
                evidence={
                    "error": str(e),
                    "signature_path": self.signature_path,
                    "public_key_path": self.public_key_path
                },
                confidence=0.9
            )

        return None

    def _loop_iteration(self):
        """单次迭代"""
        # 定期检查固件完整性
        now = time.time()

        if self.last_check_time > 0 and now - self.last_check_time < self.check_interval:
            return

        if self.firmware_info:
            threat_event = self._check_firmware_integrity()
            if threat_event:
                self._handle_threat(threat_event)

            if self.signature_required:
                signature_event = self._check_signature()
                if signature_event:
                    self._handle_threat(signature_event)

    def cleanup(self) -> None:
        """清理资源"""
        pass

    def get_firmware_info(self) -> Optional[Dict[str, Any]]:
        """获取固件信息"""
        if not self.firmware_info:
            return None

        return {
            "firmware_path": self.firmware_info.firmware_path,
            "expected_hash": self.firmware_info.expected_hash,
            "current_hash": self.firmware_info.current_hash,
            "algorithm": self.firmware_info.algorithm,
            "integrity_ok": self.integrity_ok,
            "last_check_time": self.firmware_info.last_check_time,
            "check_count": self.check_count
        }

    def update_expected_hash(self, new_hash: str) -> None:
        """更新预期哈希"""
        if self.firmware_info:
            self.firmware_info.expected_hash = new_hash
            self.logger.info(f"已更新预期哈希: {new_hash}")
        else:
            self.logger.warning("固件信息未初始化")

    def force_check(self) -> Optional[ThreatEvent]:
        """强制执行完整性检查"""
        if self.firmware_info:
            return self._check_firmware_integrity()
        return None
