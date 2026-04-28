"""
数据包解析工具
Packet Parser Utility
"""

import struct
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass


@dataclass
class ParsedPacket:
    """解析后的数据包"""
    protocol: str = ""
    source_ip: str = ""
    dest_ip: str = ""
    source_port: int = 0
    dest_port: int = 0
    payload: bytes = b""
    raw_data: bytes = b""
    timestamp: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "protocol": self.protocol,
            "source_ip": self.source_ip,
            "dest_ip": self.dest_ip,
            "source_port": self.source_port,
            "dest_portable": self.dest_port,
            "payload_length": len(self.payload),
            "raw_length": len(self.raw_data),
            "timestamp": self.timestamp
        }


class PacketParser:
    """数据包解析器"""

    @staticmethod
    def parse_ethernet_frame(data: bytes) -> Optional[Dict[str, Any]]:
        """解析以太网帧"""
        if len(data) < 14:
            return None

        ether_header = struct.unpack("!6s6sH", data[:14])
        dest_mac = ":".join(f"{b:02x}" for b in ether_header[0])
        src_mac = ":".join(f"{b:02x}" for b in ether_header[1])
        eth_type = ether_header[2]

        payload = data[14:]

        return {
            "dest_mac": dest_mac,
            "src_mac": src_mac,
            "eth_type": eth_type,
            "payload": payload
        }

    @staticmethod
    def parse_ip_packet(data: bytes) -> Optional[Dict[str, Any]]:
        """解析IP数据包"""
        if len(data) < 20:
            return None

        ip_header = data[:20]
        iph = struct.unpack("!BBHHHBBH4s4s", ip_header)

        version = (iph[0] >> 4) & 0xF
        ihl = (iph[0] & 0xF) * 4
        protocol = iph[6]

        if version != 4 or len(data) < ihl:
            return None

        src_addr = ".".join(map(str, iph[8]))
        dest_addr = ".".join(map(str, iph[9]))

        payload = data[ihl:]

        return {
            "version": version,
            "ihl": ihl,
            "protocol": protocol,
            "src_addr": src_addr,
            "dest_addr": dest_addr,
            "payload": payload
        }

    @staticmethod
    def parse_tcp_segment(data: bytes) -> Optional[Dict[str, Any]]:
        """解析TCP段"""
        if len(data) < 20:
            return None

        tcp_header = data[:20]
        tcph = struct.unpack("!HHLLBBHHH", tcp_header)

        src_port = tcph[0]
        dest_port = tcph[1]
        seq_num = tcph[2]
        ack_num = tcph[3]
        offset = (tcph[4] >> 4) & 0xF
        flags = tcph[5]

        if len(data) < offset * 4:
            return None

        payload = data[offset * 4:]

        return {
            "src_port": src_port,
            "dest_port": dest_port,
            "seq_num": seq_num,
            "ack_num": ack_num,
            "flags": flags,
            "syn": bool(flags & 0x02),
            "ack": bool(flags & 0x10),
            "fin": bool(flags & 0x01),
            "rst": bool(flags & 0x04),
            "payload": payload
        }

    @staticmethod
    def parse_udp_datagram(data: bytes) -> Optional[Dict[str, Any]]:
        """解析UDP数据报"""
        if len(data) < 8:
            return None

        udp_header = data[:8]
        udph = struct.unpack("!HHHH", udp_header)

        src_port = udph[0]
        dest_port = udph[1]
        length = udph[2]
        checksum = udph[3]

        payload = data[8:]

        return {
            "src_port": src_port,
            "dest_port": dest_port,
            "length": length,
            "checksum": checksum,
            "payload": payload
        }

    @staticmethod
    def parse_mavlink_header(data: bytes) -> Optional[Dict[str, Any]]:
        """解析MAVLink v1/v2头部"""
        if len(data) < 6:
            return None

        stx = data[0]

        # MAVLink v1
        if stx == 0xFE:
            if len(data) < 6:
                return None

            payload_length = data[1]
            seq = data[2]
            sys_id = data[3]
            comp_id = data[4]
            msg_id = data[5]

            header_length = 6

            return {
                "version": 1,
                "payload_length": payload_length,
                "sequence": seq,
                "system_id": sys_id,
                "component_id": comp_id,
                "message_id": msg_id,
                "header_length": header_length
            }

        # MAVLink v2
        elif stx == 0xFD:
            if len(data) < 10:
                return None

            payload_length = data[1]
            packet_flags = data[2]
            sys_id = data[3]
            comp_id = data[4]
            msg_id = data[5] | (data[6] << 8) | (data[7] << 16)
            msg_id = msg_id & 0xFFFFFF

            header_length = 10

            return {
                "version": 2,
                "payload_length": payload_length,
                "flags": packet_flags,
                "system_id": sys_id,
                "component_id": comp_id,
                "message_id": msg_id,
                "header_length": header_length
            }

        return None

    @staticmethod
    def is_mavlink_packet(data: bytes) -> bool:
        """检查是否为MAVLink数据包"""
        if len(data) < 1:
            return False
        return data[0] in [0xFE, 0xFD]

    @staticmethod
    def extract_payload(data: bytes, protocol: str) -> bytes:
        """提取负载"""
        if protocol == "mavlink":
            mavlink_header = PacketParser.parse_mavlink_header(data)
            if mavlink_header:
                header_len = mavlink_header["header_length"]
                payload_len = mavlink_header["payload_length"]
                return data[header_len:header_len + payload_len]

        return data
