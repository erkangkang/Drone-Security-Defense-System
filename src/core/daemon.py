"""
守护进程核心
Security Daemon
"""

import os
import signal
import sys
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any

from .config_manager import ConfigManager
from .event_bus import EventBus, Event
from .platform_detector import PlatformDetector
from ..utils.logger import get_logger, SecurityLogger
from ..utils.time_utils import TimeUtils, Timer


class SecurityDaemon:
    """安全守护进程"""

    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config_manager = ConfigManager(config_path)
        self.event_bus = EventBus()
        self.platform_detector = PlatformDetector()

        self.detectors: Dict[str, Any] = {}
        self.handlers: Dict[str, Any] = {}
        self.analyzers: Dict[str, Any] = {}
        self.mavlink_interface: Optional[Any] = None
        self._mavlink_conn: Optional[str] = None
        self._mavlink_baudrate: int = 57600

        self.running = False
        self.shutdown_event = threading.Event()
        self.logger: Optional[Any] = None

        # 统计信息
        self.stats = {
            "start_time": 0,
            "events_processed": 0,
            "threats_detected": 0,
            "uptime": 0
        }

        # 回调
        self.on_shutdown: Optional[Callable] = None

        # Web服务器
        self.web_bridge = None
        self.web_server = None

    def initialize(self) -> bool:
        """初始化守护进程"""
        # 加载配置
        if not self.config_manager.load():
            self._setup_default_logger()
            self.logger.error("配置加载失败")
            return False

        # 检测平台
        self.platform_detector.detect()
        self.config_manager.load_platform_config()

        # 设置日志
        self._setup_logger()

        self.logger.info("=" * 50)
        self.logger.info("无人机网络安全防御系统启动")
        self.logger.info("=" * 50)
        self.logger.info(f"版本: 1.0.0")
        self.logger.info(f"平台: {self.platform_detector.platform_info.platform_type.value}")
        self.logger.info(f"配置文件: {self.config_path}")

        # 初始化事件总线
        self.event_bus.start_async_workers()

        # 加载检测器
        self._load_detectors()

        # 加载接口
        self._load_interfaces()

        # 加载分析器
        self._load_analyzers()

        # 加载处理器
        self._load_handlers()

        # 加载Web服务器
        self._load_web_server()

        # 订阅事件
        self._subscribe_events()

        self.logger.info("守护进程初始化完成")
        return True

    def _load_interfaces(self):
        """加载数据接口"""
        interfaces_config = self.config_manager.get("interfaces", {})
        mavlink_config = interfaces_config.get("mavlink", {})

        if not mavlink_config.get("enabled", False):
            return

        try:
            from ..interfaces.mavlink_interface import MAVLinkInterface

            self.mavlink_interface = MAVLinkInterface()
            self._mavlink_conn = mavlink_config.get("connection_string", "udpin:0.0.0.0:14550")
            self._mavlink_baudrate = int(mavlink_config.get("baudrate", 57600))
            self.logger.info("MAVLink接口已加载")
        except Exception as e:
            self.logger.error(f"加载MAVLink接口失败: {e}")
            self.mavlink_interface = None

    def _setup_default_logger(self):
        """设置默认日志器"""
        self.logger = get_logger("daemon")
        SecurityLogger().setup_logger("daemon", console_output=True)

    def _setup_logger(self):
        """设置日志器"""
        log_level = self.config_manager.get("log_level", "INFO")
        log_path = self.config_manager.get("log_path", "logs/")

        # 转换日志级别
        import logging
        level = getattr(logging, log_level.upper(), logging.INFO)

        SecurityLogger().setup_logger(
            "daemon",
            log_file=f"{log_path}daemon.log",
            level=level,
            console_output=True
        )

        # 设置其他模块日志
        SecurityLogger().setup_logger(
            "security",
            log_file=f"{log_path}security.log",
            level=level,
            console_output=False
        )

        SecurityLogger().setup_logger(
            "detector",
            log_file=f"{log_path}detector.log",
            level=level,
            console_output=False
        )

        SecurityLogger().setup_logger(
            "handler",
            log_file=f"{log_path}handler.log",
            level=level,
            console_output=False
        )

        self.logger = get_logger("daemon")

    def _load_detectors(self):
        """加载检测器"""
        from ..detectors.mavlink_detector import MAVLinkDetector
        from ..detectors.gps_detector import GPSDetector
        from ..detectors.sensor_detector import SensorDetector
        from ..detectors.dos_detector import DOSDetector
        from ..detectors.firmware_detector import FirmwareDetector

        detector_classes = {
            "mavlink": MAVLinkDetector,
            "gps": GPSDetector,
            "sensor": SensorDetector,
            "dos": DOSDetector,
            "firmware": FirmwareDetector
        }

        for name, cls in detector_classes.items():
            detector_config = self.config_manager.get_detector_config(name)

            if detector_config.enabled:
                try:
                    detector = cls(self.event_bus, detector_config)
                    if detector.initialize():
                        self.detectors[name] = detector
                        self.logger.info(f"检测器已加载: {name}")
                except Exception as e:
                    self.logger.error(f"加载检测器失败 ({name}): {e}")

    def _load_analyzers(self):
        """加载分析器"""
        from ..analyzers.statistical_analyzer import StatisticalAnalyzer
        from ..analyzers.correlation_analyzer import CorrelationAnalyzer

        analyzer_config = self.config_manager.get("analyzers", {})

        # 统计分析器
        if analyzer_config.get("statistical", {}).get("enabled", True):
            try:
                analyzer = StatisticalAnalyzer(self.event_bus)
                analyzer.initialize(analyzer_config.get("statistical", {}))
                self.analyzers["statistical"] = analyzer
                self.logger.info("分析器已加载: statistical")
            except Exception as e:
                self.logger.error(f"加载分析器失败 (statistical): {e}")

        # 关联分析器
        if analyzer_config.get("correlation", {}).get("enabled", True):
            try:
                analyzer = CorrelationAnalyzer(self.event_bus)
                analyzer.initialize(analyzer_config.get("correlation", {}))
                self.analyzers["correlation"] = analyzer
                self.logger.info("分析器已加载: correlation")
            except Exception as e:
                self.logger.error(f"加载分析器失败 (correlation): {e}")

    def _load_handlers(self):
        """加载处理器"""
        from ..handlers.alert_handler import AlertHandler
        from ..handlers.log_handler import LogHandler
        from ..handlers.block_handler import BlockHandler

        alert_config = self.config_manager.get("alerts", {})
        blocking_config = self.config_manager.get("blocking", {})

        # 告警处理器
        if alert_config.get("enabled", True):
            try:
                handler = AlertHandler(self.event_bus, alert_config)
                self.handlers["alert"] = handler
                self.logger.info("处理器已加载: alert")
            except Exception as e:
                self.logger.error(f"加载处理器失败 (alert): {e}")

        # 日志处理器
        try:
            handler = LogHandler(self.event_bus)
            self.handlers["log"] = handler
            self.logger.info("处理器已加载: log")
        except Exception as e:
            self.logger.error(f"加载处理器失败 (log): {e}")

        # 阻断处理器
        if blocking_config.get("enabled", False):
            try:
                handler = BlockHandler(self.event_bus, blocking_config)
                self.handlers["block"] = handler
                self.logger.info("处理器已加载: block")
            except Exception as e:
                self.logger.error(f"加载处理器失败 (block): {e}")

    def _load_web_server(self):
        """加载Web服务器"""
        web_config = self.config_manager.get("web", {})
        if web_config.get("enabled", False):
            try:
                from .web_bridge import WebBridge
                from ..web.server import WebServer

                self.web_bridge = WebBridge(self)
                self.web_server = WebServer(self.web_bridge, web_config)
                self.logger.info("Web服务器已加载")
            except Exception as e:
                self.logger.error(f"加载Web服务器失败: {e}")

    def _subscribe_events(self):
        """订阅事件"""
        # 订阅威胁事件
        self.event_bus.subscribe(
            "threat.detected",
            self._on_threat_detected
        )

        # 订阅告警事件
        self.event_bus.subscribe(
            "alert.created",
            self._on_alert_created
        )

    def _on_threat_detected(self, event: Event):
        """威胁检测事件处理"""
        self.stats["threats_detected"] += 1
        self.logger.warning(f"威胁检测: {event.data.get('threat_type')}")

    def _on_alert_created(self, event: Event):
        """告警创建事件处理"""
        self.logger.info(f"告警创建: {event.data.get('alert_id')}")

    def start(self):
        """启动守护进程"""
        if self.running:
            self.logger.warning("守护进程已在运行")
            return

        self.running = True
        self.stats["start_time"] = time.time()

        # 启动检测器
        for name, detector in self.detectors.items():
            try:
                detector.start()
                self.logger.info(f"检测器已启动: {name}")
            except Exception as e:
                self.logger.error(f"启动检测器失败 ({name}): {e}")

        # 启动数据接口
        self._start_interfaces()

        # 启动Web服务器
        if self.web_server:
            try:
                self.web_server.run_in_thread()
                self.logger.info("Web服务器已启动（独立线程）")
            except Exception as e:
                self.logger.error(f"启动Web服务器失败: {e}")

        # 注册信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self.logger.info("守护进程已启动")

    def _start_interfaces(self):
        """启动数据接口"""
        if not self.mavlink_interface or not self._mavlink_conn:
            return

        try:
            ok = self.mavlink_interface.connect(self._mavlink_conn, self._mavlink_baudrate)
            if not ok:
                self.logger.error("MAVLink接口连接失败")
                return

            def _on_mavlink_message(msg):
                detector = self.detectors.get("mavlink")
                if detector:
                    detector.process_data(msg)

            self.mavlink_interface.start_reading(callback=_on_mavlink_message)
            self.logger.info("MAVLink接口已启动")
        except Exception as e:
            self.logger.error(f"启动MAVLink接口失败: {e}")

    def run(self):
        """运行守护进程主循环"""
        if not self.initialize():
            return

        self.start()

        try:
            while self.running:
                # 更新运行状态
                self.stats["uptime"] = time.time() - self.stats["start_time"]

                # 处理事件
                self._process_events()

                # 短暂休眠
                time.sleep(0.1)

        except KeyboardInterrupt:
            self.logger.info("收到键盘中断信号")
        except Exception as e:
            self.logger.error(f"守护进程异常: {e}")
        finally:
            self.shutdown()

    def _process_events(self):
        """处理事件"""
        processed = 0
        for detector in self.detectors.values():
            try:
                processed += int(getattr(detector.stats, "processed_count", 0))
            except Exception:
                pass
        self.stats["events_processed"] = processed

    def _signal_handler(self, signum, frame):
        """信号处理器"""
        signal_name = signal.Signals(signum).name
        self.logger.info(f"收到信号: {signal_name}")
        self.shutdown()

    def shutdown(self):
        """关闭守护进程"""
        if not self.running:
            return

        self.logger.info("正在关闭守护进程...")
        self.running = False
        self.shutdown_event.set()

        # 停止数据接口
        if self.mavlink_interface:
            try:
                self.mavlink_interface.disconnect()
            except Exception:
                pass

        # 停止Web服务器
        if self.web_server:
            try:
                self.web_server.stop()
                self.logger.info("Web服务器已停止")
            except Exception as e:
                self.logger.error(f"停止Web服务器失败: {e}")

        # 停止检测器
        for name, detector in self.detectors.items():
            try:
                detector.stop()
                self.logger.info(f"检测器已停止: {name}")
            except Exception as e:
                self.logger.error(f"停止检测器失败 ({name}): {e}")

        # 停止事件总线
        self.event_bus.stop_async_workers()

        # 关闭日志
        SecurityLogger().close_all()

        # 输出统计信息
        self._print_stats()

        self.logger.info("守护进程已关闭")

        # 调用回调
        if self.on_shutdown:
            self.on_shutdown()

    def _print_stats(self):
        """打印统计信息"""
        self.logger.info("=" * 50)
        self.logger.info("统计信息:")
        self.logger.info(f"运行时间: {TimeUtils.format_duration(self.stats['uptime'])}")
        self.logger.info(f"处理事件: {self.stats['events_processed']}")
        self.logger.info(f"检测威胁: {self.stats['threats_detected']}")
        self.logger.info("=" * 50)

    def reload_config(self) -> bool:
        """重新加载配置"""
        self.logger.info("重新加载配置...")
        if self.config_manager.reload():
            self.logger.info("配置重新加载成功")
            return True
        return False

    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            "running": self.running,
            "platform": self.platform_detector.platform_info.platform_type.value,
            "detectors": list(self.detectors.keys()),
            "handlers": list(self.handlers.keys()),
            "analyzers": list(self.analyzers.keys()),
            "stats": self.stats.copy()
        }

    def inject_data(self, detector_name: str, data: Any):
        """注入数据到检测器（用于测试）"""
        if detector_name in self.detectors:
            self.detectors[detector_name].process_data(data)
        else:
            self.logger.warning(f"检测器不存在: {detector_name}")
