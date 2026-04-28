"""
阻断处理器
Block Handler
"""

import time
import socket
import threading
from typing import Any, Dict, List, Set, Optional
from collections import deque

from .base_handler import BaseHandler
from ..core.event_bus import EventBus
from ..utils.logger import get_logger


class BlockHandler(BaseHandler):
    """阻断处理器"""

    def __init__(self, event_bus: EventBus, config: Dict[str, Any]):
        super().__init__(event_bus)
        self.name = "BlockHandler"

        # 配置
        self.enabled = config.get("enabled", False)
        self.auto_block = config.get("auto_block", False)
        self.block_duration = config.get("block_duration", 300)  # 秒
        self.block_threshold = config.get("block_threshold", 3)  # 多少次触发后自动阻断

        # IP黑名单
        self.blocked_ips: Dict[str, float] = {}
        self.ip_violation_count: Dict[str, int] = {}

        # 端口黑名单
        self.blocked_ports: Set[int] = set()

        # 记录
        self.block_history: deque = deque(maxlen=1000)

        # 统计
        self.total_blocks = 0
        self.auto_blocks = 0
        self.manual_blocks = 0

        # 线程安全
        self.lock = threading.Lock()

    def initialize(self) -> bool:
        """初始化处理器"""
        if not self.enabled:
            self.logger.info("阻断处理器已禁用")
            return True

        # 订阅威胁事件
        self.subscription_id = self.event_bus.subscribe(
            "threat.detected",
            self._on_threat_detected
        )

        # 启动清理线程
        self.cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            name="BlockCleanupThread",
            daemon=True
        )
        self.cleanup_thread.start()

        self.logger.info(f"阻断处理器初始化完成 (自动阻断: {self.auto_block})")
        return True

    def _on_threat_detected(self, event) -> None:
        """威胁检测事件处理"""
        if not self.enabled:
            return

        try:
            if isinstance(event.data, dict):
                source = event.data.get("source", "")
                severity = event.data.get("severity", "")

                # 如果是IP地址，检查是否需要阻断
                if self._is_ip_address(source):
                    self._handle_ip_threat(source, severity)

        except Exception as e:
            self.logger.error(f"处理威胁事件失败: {e}")

    def _is_ip_address(self, source: str) -> bool:
        """检查是否为IP地址"""
        try:
            socket.inet_aton(source)
            return True
        except (socket.error, ValueError):
            return False

    def _handle_ip_threat(self, ip: str, severity: str) -> None:
        """处理IP威胁"""
        with self.lock:
            # 增加违规计数
            self.ip_violation_count[ip] = self.ip_violation_count.get(ip, 0) + 1

            # 检查是否达到自动阻断阈值
            if self.auto_block and self.ip_violation_count[ip] >= self.block_threshold:
                self._block_ip(ip, auto=True)
            elif severity in ["high", "critical"]:
                # 高危威胁立即阻断
                self._block_ip(ip, auto=True)

    def block_ip(self, ip: str, duration: Optional[int] = None, reason: str = "manual") -> bool:
        """阻断IP地址"""
        with self.lock:
            return self._block_ip(ip, duration or self.block_duration, auto=False, reason=reason)

    def _block_ip(self, ip: str, duration: int = None, auto: bool = False, reason: str = "auto") -> bool:
        """内部IP阻断实现"""
        duration = duration or self.block_duration

        # 检查是否已阻断
        if ip in self.blocked_ips:
            block_time = self.blocked_ips[ip]
            if time.time() - block_time < duration:
                return False  # 已经被阻断

        # 执行阻断
        self.blocked_ips[ip] = time.time()
        self.total_blocks += 1

        if auto:
            self.auto_blocks += 1
        else:
            self.manual_blocks += 1

        # 记录
        self.block_history.append({
            "timestamp": time.time(),
            "ip": ip,
            "duration": duration,
            "reason": reason,
            "auto": auto
        })

        self.logger.warning(f"IP已阻断: {ip} (持续: {duration}s, 原因: {reason})")

        # 发布阻断事件
        self.event_bus.publish_sync(
            "block.ip",
            {
                "ip": ip,
                "duration": duration,
                "reason": reason,
                "timestamp": time.time()
            }
        )

        return True

    def unblock_ip(self, ip: str) -> bool:
        """解除IP阻断"""
        with self.lock:
            if ip in self.blocked_ips:
                del self.blocked_ips[ip]

                # 重置违规计数
                if ip in self.ip_violation_count:
                    del self.ip_violation_count[ip]

                self.logger.info(f"IP解除阻断: {ip}")

                # 发布解除阻断事件
                self.event_bus.publish_sync(
                    "block.unblock_ip",
                    {
                        "ip": ip,
                        "timestamp": time.time()
                    }
                )

                return True

        return False

    def is_ip_blocked(self, ip: str) -> bool:
        """检查IP是否被阻断"""
        with self.lock:
            if ip not in self.blocked_ips:
                return False

            block_time = self.blocked_ips[ip]
            if time.time() - block_time >= self.block_duration:
                # 阻断已过期
                del self.blocked_ips[ip]
                return False

            return True

    def block_port(self, port: int) -> bool:
        """阻断端口"""
        with self.lock:
            self.blocked_ports.add(port)

            self.logger.warning(f"端口已阻断: {port}")

            return True

    def unblock_port(self, port: int) -> bool:
        """解除端口阻断"""
        with self.lock:
            if port in self.blocked_ports:
                self.blocked_ports.remove(port)
                self.logger.info(f"端口解除阻断: {port}")
                return True

        return False

    def is_port_blocked(self, port: int) -> bool:
        """检查端口是否被阻断"""
        with self.lock:
            return port in self.blocked_ports

    def _cleanup_loop(self):
        """清理过期阻断记录"""
        while self.enabled:
            try:
                self._cleanup_expired_blocks()
                time.sleep(60)  # 每分钟检查一次
            except Exception as e:
                self.logger.error(f"清理循环错误: {e}")

    def _cleanup_expired_blocks(self):
        """清理过期的阻断记录"""
        now = time.time()
        expired_ips = []

        with self.lock:
            for ip, block_time in self.blocked_ips.items():
                if now - block_time >= self.block_duration:
                    expired_ips.append(ip)

            for ip in expired_ips:
                del self.blocked_ips[ip]
                self.logger.info(f"阻断已过期: {ip}")

    def handle(self, data: Any) -> None:
        """处理数据（被动模式）"""
        if not self.enabled:
            return

        if isinstance(data, dict):
            action = data.get("action")
            ip = data.get("ip")

            if action == "block" and ip:
                self.block_ip(ip, reason="manual")
            elif action == "unblock" and ip:
                self.unblock_ip(ip)

    def get_blocked_ips(self) -> List[Dict[str, Any]]:
        """获取被阻断的IP列表"""
        now = time.time()
        blocked_list = []

        with self.lock:
            for ip, block_time in self.blocked_ips.items():
                remaining = self.block_duration - (now - block_time)
                if remaining > 0:
                    blocked_list.append({
                        "ip": ip,
                        "blocked_since": block_time,
                        "remaining_seconds": remaining,
                        "violation_count": self.ip_violation_count.get(ip, 0)
                    })
                else:
                    # 清理过期项
                    del self.blocked_ips[ip]

        return blocked_list

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.lock:
            return {
                "total_blocks": self.total_blocks,
                "auto_blocks": self.auto_blocks,
                "manual_blocks": self.manual_blocks,
                "currently_blocked_ips": len(self.blocked_ips),
                "blocked_ports": list(self.blocked_ports),
                "auto_block_enabled": self.auto_block,
                "block_threshold": self.block_threshold,
                "block_duration": self.block_duration,
                "enabled": self.enabled
            }

    def cleanup(self) -> None:
        """清理资源"""
        self.enabled = False

        if self.subscription_id:
            self.event_bus.unsubscribe(self.subscription_id)

        with self.lock:
            self.blocked_ips.clear()
            self.ip_violation_count.clear()
            self.blocked_ports.clear()
            self.block_history.clear()

        self.logger.info(f"阻断处理器已清理 (总阻断: {self.total_blocks})")
