"""
平台检测器
Platform Detector
"""

import os
import platform
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional

from ..utils.logger import get_logger


class PlatformType(Enum):
    """平台类型"""
    LINUX = "linux"
    ANDROID = "android"
    WINDOWS = "windows"
    MACOS = "macos"
    EMBEDDED = "embedded"
    UNKNOWN = "unknown"


class ResourceProfile(Enum):
    """资源配置文件"""
    MINIMAL = "minimal"
    BALANCED = "balanced"
    FULL = "full"


@dataclass
class PlatformInfo:
    """平台信息"""
    platform_type: PlatformType
    system: str
    machine: str
    python_version: str
    cpu_count: int
    memory_total_mb: int
    is_docker: bool = False
    is_vm: bool = False


class PlatformDetector:
    """平台检测器"""

    def __init__(self):
        self.platform_info: Optional[PlatformInfo] = None
        self.logger = get_logger("platform")

    def detect(self) -> PlatformInfo:
        """检测平台信息"""
        system = platform.system().lower()
        machine = platform.machine()
        python_version = platform.python_version()
        cpu_count = os.cpu_count() or 1

        # 检测平台类型
        platform_type = self._detect_platform_type(system)

        # 检测内存
        memory_total_mb = self._detect_memory()

        # 检测容器/虚拟机
        is_docker = self._is_docker()
        is_vm = self._is_vm()

        self.platform_info = PlatformInfo(
            platform_type=platform_type,
            system=system,
            machine=machine,
            python_version=python_version,
            cpu_count=cpu_count,
            memory_total_mb=memory_total_mb,
            is_docker=is_docker,
            is_vm=is_vm
        )

        self._log_platform_info()

        return self.platform_info

    def _detect_platform_type(self, system: str) -> PlatformType:
        """检测平台类型"""
        if system == "linux":
            # 检查Android
            try:
                with open("/proc/version", "r") as f:
                    if "android" in f.read().lower():
                        return PlatformType.ANDROID
            except (FileNotFoundError, IOError):
                pass

            # 检查嵌入式系统
            try:
                with open("/etc/os-release", "r") as f:
                    os_release = f.read()
                    if any(x in os_release for x in ["yocto", "buildroot", "openwrt"]):
                        return PlatformType.EMBEDDED
            except (FileNotFoundError, IOError):
                pass

            # 检查ARM架构（可能是嵌入式）
            if "arm" in platform.machine().lower() or "aarch64" in platform.machine().lower():
                return PlatformType.EMBEDDED

            return PlatformType.LINUX

        elif system == "windows":
            return PlatformType.WINDOWS

        elif system == "darwin":
            return PlatformType.MACOS

        return PlatformType.UNKNOWN

    def _detect_memory(self) -> int:
        """检测内存大小（MB）"""
        try:
            import psutil
            return int(psutil.virtual_memory().total / (1024 * 1024))
        except ImportError:
            pass

        try:
            if platform.system() == "Linux":
                with open("/proc/meminfo", "r") as f:
                    for line in f:
                        if line.startswith("MemTotal:"):
                            mem_kb = int(line.split()[1])
                            return int(mem_kb / 1024)
        except (FileNotFoundError, IOError):
            pass

        return 1024  # 默认1GB

    def _is_docker(self) -> bool:
        """检测是否在Docker容器中运行"""
        try:
            with open("/proc/1/cgroup", "r") as f:
                return "docker" in f.read() or "/docker/" in f.read()
        except (FileNotFoundError, IOError):
            pass

        # 检查环境变量
        if os.environ.get("DOCKER_CONTAINER"):
            return True

        return False

    def _is_vm(self) -> bool:
        """检测是否在虚拟机中运行"""
        try:
            if platform.system() == "Linux":
                with open("/proc/cpuinfo", "r") as f:
                    cpuinfo = f.read().lower()
                    # 检查常见的虚拟机CPU标识
                    vm_indicators = ["qemu", "kvm", "vmware", "virtualbox", "xen"]
                    return any(indicator in cpuinfo for indicator in vm_indicators)
        except (FileNotFoundError, IOError):
            pass

        return False

    def _log_platform_info(self) -> None:
        """记录平台信息"""
        if self.platform_info:
            self.logger.info(f"检测到平台: {self.platform_info.platform_type.value}")
            self.logger.info(f"系统: {self.platform_info.system}")
            self.logger.info(f"架构: {self.platform_info.machine}")
            self.logger.info(f"CPU核心数: {self.platform_info.cpu_count}")
            self.logger.info(f"内存: {self.platform_info.memory_total_mb} MB")
            self.logger.info(f"Python版本: {self.platform_info.python_version}")
            self.logger.info(f"Docker: {self.platform_info.is_docker}")
            self.logger.info(f"虚拟机: {self.platform_info.is_vm}")

    def get_resource_profile(self, config_profile: Optional[str] = None) -> ResourceProfile:
        """获取资源配置文件"""
        if config_profile:
            try:
                return ResourceProfile(config_profile)
            except ValueError:
                pass

        # 根据平台信息自动选择
        if self.platform_info is None:
            self.detect()

        # 嵌入式系统使用minimal配置
        if self.platform_info.platform_type == PlatformType.EMBEDDED:
            return ResourceProfile.MINIMAL

        # 低资源系统使用minimal配置
        if self.platform_info.memory_total_mb < 512:
            return ResourceProfile.MINIMAL

        # Docker/VM使用balanced配置
        if self.platform_info.is_docker or self.platform_info.is_vm:
            return ResourceProfile.BALANCED

        # 高资源系统使用full配置
        if self.platform_info.memory_total_mb >= 4096:
            return ResourceProfile.FULL

        return ResourceProfile.BALANCED

    def get_platform_specific_config(self) -> Dict[str, Any]:
        """获取平台特定配置"""
        if self.platform_info is None:
            self.detect()

        config = {}

        # 根据平台类型设置配置
        if self.platform_info.platform_type == PlatformType.EMBEDDED:
            config.update({
                "log_level": "WARNING",
                "max_workers": 1,
                "buffer_size": 100,
                "enable_ml_analyzer": False,
                "enable_cloud_sync": False
            })
        elif self.platform_info.platform_type == PlatformType.ANDROID:
            config.update({
                "log_level": "INFO",
                "max_workers": 2,
                "buffer_size": 500,
                "enable_ml_analyzer": False,
                "enable_cloud_sync": True
            })
        else:
            config.update({
                "log_level": "INFO",
                "max_workers": self.platform_info.cpu_count,
                "buffer_size": 1000,
                "enable_ml_analyzer": True,
                "enable_cloud_sync": True
            })

        return config
