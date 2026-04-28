"""
MAVLink 接口
MAVLink Interface
"""

import time
from typing import Any, Callable, Optional, Dict
from threading import Thread, Lock

from ..utils.logger import get_logger
from ..models.telemetry import MAVLinkMessage


class MAVLinkInterface:
    """MAVLink通信接口"""

    def __init__(self):
        self.connected = False
        self.serial_port: Optional[str] = None
        self.baudrate: int = 57600
        self.connection: Optional[Any] = None
        self.thread: Optional[Thread] = None
        self.running = False

        # 消息处理
        self.message_handlers: list = []
        self.lock = Lock()

        # 统计
        self.messages_received = 0
        self.messages_sent = 0
        self.errors = 0

        self.logger = get_logger("mavlink")

    def connect(
        self,
        connection_string: str,
        baudrate: int = 57600
    ) -> bool:
        """连接到MAVLink设备"""
        try:
            from pymavlink import mavutil

            self.serial_port = connection_string
            self.baudrate = baudrate

            self.logger.info(f"连接到MAVLink: {connection_string} @ {baudrate}")

            # 创建连接
            self.connection = mavutil.mavlink_connection(connection_string)

            # 等待连接建立
            self.connection.wait_heartbeat(timeout=5)

            self.connected = True
            self.logger.info("MAVLink连接成功")

            return True

        except Exception as e:
            self.logger.error(f"MAVLink连接失败: {e}")
            self.errors += 1
            return False

    def disconnect(self) -> None:
        """断开连接"""
        self.running = False

        if self.thread:
            self.thread.join(timeout=3)
            self.thread = None

        self.connected = False
        self.connection = None

        self.logger.info("MAVLink已断开")

    def start_reading(self, callback: Optional[Callable[[MAVLinkMessage], None]] = None) -> None:
        """开始读取消息"""
        if not self.connected:
            self.logger.error("MAVLink未连接")
            return

        if callback:
            with self.lock:
                self.message_handlers.append(callback)

        self.running = True
        self.thread = Thread(
            target=self._read_loop,
            name="MAVLinkReader",
            daemon=True
        )
        self.thread.start()

        self.logger.info("MAVLink读取已启动")

    def _read_loop(self):
        """读取循环"""
        while self.running and self.connection:
            try:
                # 读取消息
                msg = self.connection.recv_match(blocking=True, timeout=1.0)

                if msg:
                    self.messages_received += 1

                    # 转换为MAVLinkMessage
                    mavlink_msg = MAVLinkMessage(
                        msg_id=msg.get_msgId(),
                        sys_id=msg.get_srcSystem(),
                        comp_id=msg.get_srcComponent(),
                        seq=msg.get_seq(),
                        payload=self._extract_payload(msg),
                        source="mavlink"
                    )

                    # 调用处理器
                    with self.lock:
                        for handler in self.message_handlers:
                            try:
                                handler(mavlink_msg)
                            except Exception as e:
                                self.logger.error(f"消息处理器错误: {e}")

            except Exception as e:
                self.logger.error(f"读取消息错误: {e}")
                self.errors += 1

    def _extract_payload(self, msg) -> Dict[str, Any]:
        """提取消息负载"""
        payload = {}

        try:
            # 获取消息类型
            msg_type = msg.get_type()

            # 获取所有字段
            payload["type"] = msg_type
            payload["mavpacket"] = msg.get_msgId()

            # 根据消息类型提取特定字段
            if msg_type == "GLOBAL_POSITION_INT":
                payload["lat"] = msg.lat / 1e7
                payload["lon"] = msg.lon / 1e7
                payload["alt"] = msg.alt / 1000

            elif msg_type == "GPS_RAW_INT":
                payload["lat"] = msg.lat / 1e7
                payload["lon"] = msg.lon / 1e7
                payload["alt"] = msg.alt / 1000
                payload["fix_type"] = msg.fix_type
                payload["satellites_visible"] = msg.satellites_visible
                payload["eph"] = msg.eph / 100  # HDOP
                payload["epv"] = msg.epv / 100  # VDOP

            elif msg_type == "ATTITUDE":
                payload["roll"] = msg.roll
                payload["pitch"] = msg.pitch
                payload["yaw"] = msg.yaw
                payload["rollspeed"] = msg.rollspeed
                payload["pitchspeed"] = msg.pitchspeed
                payload["yawspeed"] = msg.yawspeed

            elif msg_type == "SCALED_IMU":
                payload["xacc"] = msg.xacc
                payload["yacc"] = msg.yacc
                payload["zacc"] = msg.zacc
                payload["xgyro"] = msg.xgyro
                payload["ygyro"] = msg.ygyro
                payload["zgyro"] = msg.zgyro

            elif msg_type == "COMMAND_LONG":
                payload["command"] = msg.command
                payload["param1"] = msg.param1
                payload["param2"] = msg.param2
                payload["param3"] = msg.param3
                payload["param4"] = msg.param4
                payload["param5"] = msg.param5
                payload["param6"] = msg.param6
                payload["param7"] = msg.param7
                payload["target_system"] = msg.target_system
                payload["target_component"] = msg.target_component

        except Exception as e:
            self.logger.error(f"提取负载失败: {e}")

        return payload

    def send_message(
        self,
        msg_id: int,
        payload: Dict[str, Any],
        sys_id: int = 1,
        comp_id: int = 1
    ) -> bool:
        """发送MAVLink消息"""
        if not self.connected:
            self.logger.error("MAVLink未连接")
            return False

        try:
            # 这里简化实现，实际需要根据消息类型构造消息
            self.messages_sent += 1
            return True

        except Exception as e:
            self.logger.error(f"发送消息失败: {e}")
            self.errors += 1
            return False

    def add_message_handler(self, handler: Callable[[MAVLinkMessage], None]) -> None:
        """添加消息处理器"""
        with self.lock:
            self.message_handlers.append(handler)

    def remove_message_handler(self, handler: Callable[[MAVLinkMessage], None]) -> None:
        """移除消息处理器"""
        with self.lock:
            if handler in self.message_handlers:
                self.message_handlers.remove(handler)

    def get_system_info(self) -> Optional[Dict[str, Any]]:
        """获取系统信息"""
        if not self.connected:
            return None

        try:
            return {
                "connected": True,
                "serial_port": self.serial_port,
                "baudrate": self.baudrate,
                "messages_received": self.messages_received,
                "messages_sent": self.messages_sent,
                "errors": self.errors
            }
        except Exception as e:
            self.logger.error(f"获取系统信息失败: {e}")
            return None

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "connected": self.connected,
            "messages_received": self.messages_received,
            "messages_sent": self.messages_sent,
            "errors": self.errors,
            "handlers_count": len(self.message_handlers)
        }
