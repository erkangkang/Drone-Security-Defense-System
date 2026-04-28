"""
网络接口
Network Interface
"""

import socket
import time
import threading
from typing import Optional, Dict, Any, Callable, List, Tuple
from collections import deque
from dataclasses import dataclass

from ..utils.logger import get_logger
from ..utils.packet_parser import PacketParser
from ..models.telemetry import NetworkConnection


@dataclass
class NetworkStats:
    """网络统计"""
    total_packets: int = 0
    total_bytes: int = 0
    connections_count: int = 0
    errors: int = 0


class NetworkInterface:
    """网络接口"""

    def __init__(self):
        self.connected = False
        self.interface_name: Optional[str] = None
        self.socket: Optional[socket.socket] = None

        # 配置
        self.port: int = 0
        self.protocol: str = "tcp"
        self.buffer_size: int = 1024

        # 连接跟踪
        self.active_connections: Dict[str, NetworkConnection] = {}
        self.connection_history: deque = deque(maxlen=1000)

        # 消息处理
        self.packet_handlers: List[Callable[[bytes, str], None]] = []
        self.connection_handlers: List[Callable[[NetworkConnection], None]] = []

        self.lock = threading.Lock()

        # 线程
        self.listen_thread: Optional[threading.Thread] = None
        self.running = False

        # 统计
        self.stats = NetworkStats()

        self.logger = get_logger("network")
        self.parser = PacketParser()

    def bind(
        self,
        host: str = "0.0.0.0",
        port: int = 0,
        protocol: str = "tcp"
    ) -> bool:
        """绑定网络接口"""
        try:
            self.port = port
            self.protocol = protocol.lower()

            # 创建socket
            if self.protocol == "tcp":
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            elif self.protocol == "udp":
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            else:
                self.logger.error(f"不支持的协议: {protocol}")
                return False

            # 绑定
            self.socket.bind((host, port))

            if self.protocol == "tcp":
                self.socket.listen(10)

            self.connected = True
            self.logger.info(f"网络接口已绑定: {host}:{port} ({protocol})")
            return True

        except Exception as e:
            self.logger.error(f"绑定失败: {e}")
            self.stats.errors += 1
            return False

    def disconnect(self) -> None:
        """断开连接"""
        self.running = False

        if self.listen_thread:
            self.listen_thread.join(timeout=3)
            self.listen_thread = None

        # 关闭所有连接
        with self.lock:
            for conn_key, conn in list(self.active_connections.items()):
                self._close_connection(conn_key)

        if self.socket:
            self.socket.close()
            self.socket = None

        self.connected = False
        self.logger.info("网络接口已断开")

    def start_listening(self) -> None:
        """开始监听"""
        if not self.connected:
            self.logger.error("网络接口未绑定")
            return

        self.running = True
        self.listen_thread = threading.Thread(
            target=self._listen_loop,
            name="NetworkListener",
            daemon=True
        )
        self.listen_thread.start()

        self.logger.info("网络监听已启动")

    def _listen_loop(self):
        """监听循环"""
        while self.running:
            try:
                if self.protocol == "tcp":
                    self._handle_tcp_connection()
                elif self.protocol == "udp":
                    self._handle_udp_datagram()

            except Exception as e:
                self.logger.error(f"监听错误: {e}")
                self.stats.errors += 1
                time.sleep(1)

    def _handle_tcp_connection(self):
        """处理TCP连接"""
        try:
            client_socket, client_address = self.socket.accept()
            source_ip, source_port = client_address

            # 创建连接记录
            conn_key = f"{source_ip}:{source_port}"

            conn = NetworkConnection(
                source_ip=source_ip,
                source_port=source_port,
                dest_ip="",
                dest_port=self.port,
                protocol="tcp"
            )

            with self.lock:
                self.active_connections[conn_key] = (conn, client_socket)
                self.stats.connections_count += 1

            # 启动客户端处理线程
            client_thread = threading.Thread(
                target=self._handle_client,
                args=(conn_key, client_socket),
                name=f"TCPClient-{conn_key}",
                daemon=True
            )
            client_thread.start()

            # 调用连接处理器
            with self.lock:
                for handler in self.connection_handlers:
                    try:
                        handler(conn)
                    except Exception as e:
                        self.logger.error(f"连接处理器错误: {e}")

        except socket.timeout:
            pass
        except Exception as e:
            self.logger.error(f"TCP连接处理错误: {e}")
            self.stats.errors += 1

    def _handle_udp_datagram(self):
        """处理UDP数据报"""
        try:
            data, client_address = self.socket.recvfrom(self.buffer_size)
            source_ip, source_port = client_address

            conn = NetworkConnection(
                source_ip=source_ip,
                source_port=source_port,
                dest_ip="",
                dest_port=self.port,
                protocol="udp",
                bytes_received=len(data)
            )

            self._process_packet(data, conn)

        except socket.timeout:
            pass
        except Exception as e:
            self.logger.error(f"UDP数据报处理错误: {e}")
            self.stats.errors += 1

    def _handle_client(self, conn_key: str, client_socket: socket.socket):
        """处理客户端连接"""
        try:
            while self.running:
                data = client_socket.recv(self.buffer_size)
                if not data:
                    break

                # 更新连接统计
                with self.lock:
                    if conn_key in self.active_connections:
                        conn, _ = self.active_connections[conn_key]
                        conn.bytes_received += len(data)

                self._process_packet(data, None)

        except Exception as e:
            self.logger.debug(f"客户端连接断开 ({conn_key}): {e}")
        finally:
            self._close_connection(conn_key)

    def _close_connection(self, conn_key: str) -> None:
        """关闭连接"""
        with self.lock:
            if conn_key in self.active_connections:
                conn, client_socket = self.active_connections[conn_key]

                # 记录到历史
                self.connection_history.append(conn)

                # 关闭socket
                try:
                    client_socket.close()
                except Exception as e:
                    pass

                del self.active_connections[conn_key]
                self.stats.connections_count -= 1

    def _process_packet(self, data: bytes, connection: Optional[NetworkConnection]) -> None:
        """处理数据包"""
        self.stats.total_packets += 1
        self.stats.total_bytes += len(data)

        # 调用数据包处理器
        with self.lock:
            for handler in self.packet_handlers:
                try:
                    handler(data, connection.source_ip if connection else "")
                except Exception as e:
                    self.logger.error(f"数据包处理器错误: {e}")

    def inject_packet(self, data: bytes, source_ip: str = "") -> None:
        """注入数据包（用于测试）"""
        self._process_packet(data, None)

    def send(self, data: bytes, dest_ip: str, dest_port: int) -> bool:
        """发送数据"""
        try:
            if self.protocol == "udp" and self.socket:
                self.socket.sendto(data, (dest_ip, dest_port))
                return True
            return False
        except Exception as e:
            self.logger.error(f"发送数据失败: {e}")
            self.stats.errors += 1
            return False

    def add_packet_handler(self, handler: Callable[[bytes, str], None]) -> None:
        """添加数据包处理器"""
        with self.lock:
            self.packet_handlers.append(handler)

    def add_connection_handler(self, handler: Callable[[NetworkConnection], None]) -> None:
        """添加连接处理器"""
        with self.lock:
            self.connection_handlers.append(handler)

    def remove_packet_handler(self, handler: Callable[[bytes, str], None]) -> None:
        """移除数据包处理器"""
        with self.lock:
            if handler in self.packet_handlers:
                self.packet_handlers.remove(handler)

    def remove_connection_handler(self, handler: Callable[[NetworkConnection], None]) -> None:
        """移除连接处理器"""
        with self.lock:
            if handler in self.connection_handlers:
                self.connection_handlers.remove(handler)

    def get_active_connections(self) -> List[Dict[str, Any]]:
        """获取活跃连接"""
        with self.lock:
            return [
                {"key": key, "connection": conn.to_dict()}
                for key, (conn, _) in self.active_connections.items()
            ]

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.lock:
            return {
                "total_packets": self.stats.total_packets,
                "total_bytes": self.stats.total_bytes,
                "active_connections": self.stats.connections_count,
                "errors": self.stats.errors,
                "protocol": self.protocol,
                "port": self.port,
                "handlers_count": len(self.packet_handlers)
            }
