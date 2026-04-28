"""
云端处理器
Cloud Handler
"""

import json
import time
import threading
from typing import Any, Dict, Optional
from collections import deque
from pathlib import Path

from .base_handler import BaseHandler
from ..core.event_bus import EventBus
from ..utils.logger import get_logger


class CloudHandler(BaseHandler):
    """云端同步处理器"""

    def __init__(self, event_bus: EventBus, config: Optional[Dict[str, Any]] = None):
        super().__init__(event_bus)
        self.name = "CloudHandler"

        # 配置
        config = config or {}
        self.enabled = config.get("enabled", False)
        self.endpoint = config.get("endpoint", "")
        self.api_key = config.get("api_key", "")
        self.sync_interval = config.get("sync_interval", 300)  # 秒
        self.offline_cache = config.get("offline_cache", True)
        self.cache_path = config.get("cache_path", "logs/cloud_cache.json")

        # 缓存
        self.event_queue: deque = deque(maxlen=1000)
        self.offline_cache_data: deque = deque(maxlen=5000)

        # 统计
        self.synced_count = 0
        self.sync_failed_count = 0
        self.last_sync_time = 0.0

        # 线程
        self.sync_thread: Optional[threading.Thread] = None

        # 加载离线缓存
        self._load_offline_cache()

    def initialize(self) -> bool:
        """初始化处理器"""
        if not self.enabled:
            self.logger.info("云端处理器已禁用")
            return True

        # 验证配置
        if not self.endpoint or not self.api_key:
            self.logger.warning("云端配置不完整，禁用云端同步")
            self.enabled = False
            return False

        # 订阅事件
        self.event_bus.subscribe(
            "threat.detected",
            self._on_threat_detected
        )

        self.event_bus.subscribe(
            "alert.created",
            self._on_alert_created
        )

        # 启动同步线程
        self.sync_thread = threading.Thread(
            target=self._sync_loop,
            name="CloudSyncThread",
            daemon=True
        )
        self.sync_thread.start()

        self.logger.info(f"云端处理器初始化完成 (间隔: {self.sync_interval}s)")
        return True

    def _on_threat_detected(self, event) -> None:
        """威胁检测事件处理"""
        if not self.enabled:
            return

        try:
            if isinstance(event.data, dict):
                self.event_queue.append({
                    "type": "threat",
                    "data": event.data,
                    "timestamp": time.time()
                })

        except Exception as e:
            self.logger.error(f"处理威胁事件失败: {e}")

    def _on_alert_created(self, event) -> None:
        """告警创建事件处理"""
        if not self.enabled:
            return

        try:
            if isinstance(event.data, dict):
                self.event_queue.append({
                    "type": "alert",
                    "data": event.data,
                    "timestamp": time.time()
                })

        except Exception as e:
            self.logger.error(f"处理告警事件失败: {e}")

    def _sync_loop(self):
        """同步循环"""
        while self.enabled:
            try:
                time.sleep(1)

                # 检查是否需要同步
                if len(self.event_queue) > 0 or time.time() - self.last_sync_time >= self.sync_interval:
                    self._sync_to_cloud()

            except Exception as e:
                self.logger.error(f"同步循环错误: {e}")

    def _sync_to_cloud(self) -> None:
        """同步到云端"""
        if not self.event_queue:
            return

        # 收集待同步的事件
        events_to_sync = []
        while self.event_queue:
            events_to_sync.append(self.event_queue.popleft())

        # 发送到云端
        success = self._send_to_cloud(events_to_sync)

        if success:
            self.synced_count += len(events_to_sync)
            self.last_sync_time = time.time()
            self.logger.info(f"已同步 {len(events_to_sync)} 个事件到云端")
        else:
            # 失败时缓存到本地
            if self.offline_cache:
                for event in events_to_sync:
                    self.offline_cache_data.append(event)
                self._save_offline_cache()

            self.sync_failed_count += len(events_to_sync)
            self.logger.error(f"云端同步失败，已缓存 {len(events_to_sync)} 个事件")

    def _send_to_cloud(self, events: list) -> bool:
        """发送事件到云端"""
        try:
            import requests

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            payload = {
                "events": events,
                "timestamp": time.time(),
                "version": "1.0.0"
            }

            response = requests.post(
                f"{self.endpoint}/events",
                headers=headers,
                json=payload,
                timeout=10
            )

            return response.status_code == 200

        except ImportError:
            self.logger.warning("requests库未安装，无法同步到云端")
            return False
        except Exception as e:
            self.logger.error(f"发送到云端失败: {e}")
            return False

    def _load_offline_cache(self) -> None:
        """加载离线缓存"""
        if not self.offline_cache:
            return

        try:
            cache_file = Path(self.cache_path)
            if cache_file.exists():
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                    # 恢复事件队列
                    for event in data.get("events", []):
                        self.offline_cache_data.append(event)

                self.logger.info(f"已加载离线缓存: {len(self.offline_cache_data)} 个事件")

        except Exception as e:
            self.logger.error(f"加载离线缓存失败: {e}")

    def _save_offline_cache(self) -> None:
        """保存离线缓存"""
        if not self.offline_cache:
            return

        try:
            cache_file = Path(self.cache_path)
            cache_file.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "last_saved": time.time(),
                "events": list(self.offline_cache_data)
            }

            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            self.logger.error(f"保存离线缓存失败: {e}")

    def handle(self, data: Any) -> None:
        """处理数据（被动模式）"""
        if not self.enabled:
            return

        if isinstance(data, dict):
            self.event_queue.append({
                "type": "manual",
                "data": data,
                "timestamp": time.time()
            })

    def sync_rules_from_cloud(self) -> Optional[Dict[str, Any]]:
        """从云端同步规则"""
        if not self.enabled:
            return None

        try:
            import requests

            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }

            response = requests.get(
                f"{self.endpoint}/rules",
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                rules = response.json()
                self.logger.info("规则已从云端同步")
                return rules

        except Exception as e:
            self.logger.error(f"同步规则失败: {e}")

        return None

    def upload_firmware_hash(self, firmware_hash: str, firmware_path: str) -> bool:
        """上传固件哈希到云端"""
        if not self.enabled:
            return False

        try:
            import requests

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            payload = {
                "firmware_hash": firmware_hash,
                "firmware_path": firmware_path,
                "timestamp": time.time()
            }

            response = requests.post(
                f"{self.endpoint}/firmware/hash",
                headers=headers,
                json=payload,
                timeout=10
            )

            return response.status_code == 200

        except Exception as e:
            self.logger.error(f"上传固件哈希失败: {e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "synced_count": self.synced_count,
            "sync_failed_count": self.sync_failed_count,
            "last_sync_time": self.last_sync_time,
            "queue_size": len(self.event_queue),
            "offline_cache_size": len(self.offline_cache_data),
            "sync_interval": self.sync_interval,
            "endpoint": self.endpoint,
            "enabled": self.enabled
        }

    def cleanup(self) -> None:
        """清理资源"""
        self.enabled = False

        # 最后同步一次
        self._sync_to_cloud()

        # 保存离线缓存
        if self.offline_cache:
            self._save_offline_cache()

        self.event_queue.clear()
        self.offline_cache_data.clear()

        self.logger.info(f"云端处理器已清理 (同步: {self.synced_count}, 失败: {self.sync_failed_count})")
