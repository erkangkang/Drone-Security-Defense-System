"""
配置管理器
Configuration Manager
"""

import os
import re
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from ..utils.logger import get_logger


@dataclass
class DetectorConfig:
    """检测器配置"""
    enabled: bool = True
    interval: float = 1.0
    rules: List[str] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.platform: str = "unknown"
        self.logger = get_logger("config")

    def load(self) -> bool:
        """加载配置文件"""
        try:
            if not self.config_path.exists():
                self.logger.error(f"配置文件不存在: {self.config_path}")
                return False

            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f)

            self._expand_env_vars(self.config)
            self._validate_config()

            self.logger.info(f"配置文件加载成功: {self.config_path}")
            return True

        except yaml.YAMLError as e:
            self.logger.error(f"YAML解析错误: {e}")
            return False
        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")
            return False

    def _expand_env_vars(self, config: Any) -> Any:
        """展开环境变量"""
        if isinstance(config, dict):
            return {k: self._expand_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._expand_env_vars(v) for v in config]
        elif isinstance(config, str):
            # 匹配 ${VAR_NAME} 格式
            matches = re.findall(r'\$\{([^}]+)\}', config)
            for match in matches:
                env_value = os.environ.get(match)
                if env_value is not None:
                    config = config.replace(f"${{{match}}}", env_value)
            return config
        return config

    def _validate_config(self) -> None:
        """验证配置"""
        required_keys = ["version", "log_level", "detectors"]
        for key in required_keys:
            if key not in self.config:
                self.logger.warning(f"配置缺少必需的键: {key}")
                self.config[key] = {}

    def reload(self) -> bool:
        """重新加载配置"""
        self.logger.info("重新加载配置...")
        return self.load()

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值（支持点分隔路径）"""
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """设置配置值（支持点分隔路径）"""
        keys = key.split(".")
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def get_detector_config(self, detector_name: str) -> DetectorConfig:
        """获取检测器配置"""
        detector_data = self.get(f"detectors.{detector_name}", {})

        return DetectorConfig(
            enabled=detector_data.get("enabled", True),
            interval=detector_data.get("interval", 1.0),
            rules=detector_data.get("rules", []),
            settings=detector_data.get("settings", {})
        )

    def get_platform(self) -> str:
        """获取平台类型"""
        if self.platform != "unknown":
            return self.platform

        platform_config = self.get("platform", {})
        if platform_config.get("auto_detect", True):
            self.platform = self._detect_platform()
        else:
            self.platform = platform_config.get("name", "linux")

        return self.platform

    def _detect_platform(self) -> str:
        """检测当前平台"""
        try:
            import platform
            system = platform.system().lower()

            if system == "linux":
                # 检查是否为Android
                try:
                    with open("/proc/version", "r") as f:
                        if "android" in f.read().lower():
                            return "android"
                except (FileNotFoundError, IOError):
                    pass

                # 检查是否为嵌入式系统
                try:
                    with open("/etc/os-release", "r") as f:
                        os_release = f.read()
                        if "yocto" in os_release or "buildroot" in os_release:
                            return "embedded"
                except (FileNotFoundError, IOError):
                    pass

                return "linux"

            elif system == "windows":
                return "windows"

            elif system == "darwin":
                return "macos"

        except Exception as e:
            self.logger.warning(f"平台检测失败: {e}")

        return "linux"

    def load_platform_config(self, platform: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """加载平台特定配置"""
        if platform is None:
            platform = self.get_platform()

        platform_config_path = self.config_path.parent / "platform_configs" / f"{platform}_config.yaml"

        if not platform_config_path.exists():
            self.logger.warning(f"平台配置文件不存在: {platform_config_path}")
            return None

        try:
            with open(platform_config_path, "r", encoding="utf-8") as f:
                platform_config = yaml.safe_load(f)

            self.config.update(platform_config)
            self.logger.info(f"已加载平台配置: {platform}")
            return platform_config

        except Exception as e:
            self.logger.error(f"加载平台配置失败: {e}")
            return None

    def load_rules(self, rule_name: str) -> Optional[Dict[str, Any]]:
        """加载检测规则"""
        rules_path = self.config_path.parent / "rules" / f"{rule_name}_rules.yaml"

        if not rules_path.exists():
            self.logger.warning(f"规则文件不存在: {rules_path}")
            return None

        try:
            with open(rules_path, "r", encoding="utf-8") as f:
                rules = yaml.safe_load(f)

            self.logger.info(f"已加载规则: {rule_name}")
            return rules

        except Exception as e:
            self.logger.error(f"加载规则失败: {e}")
            return None

    def save(self) -> bool:
        """保存配置到文件"""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)

            self.logger.info(f"配置已保存: {self.config_path}")
            return True

        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
            return False

    def to_dict(self) -> Dict[str, Any]:
        """获取配置字典的副本"""
        return self.config.copy()
