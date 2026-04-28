"""
事件总线
Event Bus
"""

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from collections import deque
from uuid import uuid4

from ..utils.logger import get_logger
from ..utils.time_utils import TimeUtils


@dataclass
class Event:
    """事件"""
    event_type: str
    data: Dict[str, Any]
    timestamp: float = field(default_factory=TimeUtils.now_timestamp)
    event_id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "data": self.data,
            "timestamp": self.timestamp
        }


@dataclass
class Subscription:
    """订阅"""
    subscription_id: str
    event_type: str
    callback: Callable[[Event], Any]
    filter_func: Optional[Callable[[Event], bool]] = None
    async_mode: bool = False
    created_at: float = field(default_factory=TimeUtils.now_timestamp)


class EventBus:
    """事件总线"""

    def __init__(self, max_history: int = 1000, async_workers: int = 4):
        self.subscriptions: Dict[str, Subscription] = {}
        self.event_type_subscriptions: Dict[str, List[str]] = {}
        self.event_history: deque = deque(maxlen=max_history)
        self.subscription_counter = 0

        self.lock = threading.Lock()
        self.logger = get_logger("event_bus")

        # 异步处理
        self.async_queue = deque()
        self.async_workers = async_workers
        self.worker_threads: List[threading.Thread] = []
        self.running = False

    def subscribe(
        self,
        event_type: str,
        callback: Callable[[Event], Any],
        filter_func: Optional[Callable[[Event], bool]] = None,
        async_mode: bool = False
    ) -> str:
        """订阅事件"""
        with self.lock:
            subscription_id = f"sub_{self.subscription_counter}"
            self.subscription_counter += 1

            subscription = Subscription(
                subscription_id=subscription_id,
                event_type=event_type,
                callback=callback,
                filter_func=filter_func,
                async_mode=async_mode
            )

            self.subscriptions[subscription_id] = subscription

            if event_type not in self.event_type_subscriptions:
                self.event_type_subscriptions[event_type] = []
            self.event_type_subscriptions[event_type].append(subscription_id)

            self.logger.debug(f"订阅已创建: {subscription_id} -> {event_type}")

        return subscription_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """取消订阅"""
        with self.lock:
            if subscription_id not in self.subscriptions:
                self.logger.warning(f"订阅不存在: {subscription_id}")
                return False

            subscription = self.subscriptions[subscription_id]

            if subscription.event_type in self.event_type_subscriptions:
                subs = self.event_type_subscriptions[subscription.event_type]
                if subscription_id in subs:
                    subs.remove(subscription_id)

            del self.subscriptions[subscription_id]

            self.logger.debug(f"订阅已取消: {subscription_id}")

        return True

    def publish(self, event: Event) -> None:
        """发布事件"""
        self.event_history.append(event)

        # 获取所有匹配的订阅
        matching_subs = []
        with self.lock:
            event_type = event.event_type

            for sub_id in self.event_type_subscriptions.get(event_type, []):
                sub = self.subscriptions.get(sub_id)
                if sub:
                    # 检查过滤器
                    if sub.filter_func is None or sub.filter_func(event):
                        matching_subs.append(sub)

        # 分发事件
        for sub in matching_subs:
            if sub.async_mode:
                self._async_publish(sub, event)
            else:
                try:
                    sub.callback(event)
                except Exception as e:
                    self.logger.error(f"事件回调失败 ({sub.subscription_id}): {e}")

        self.logger.debug(f"事件已发布: {event.event_type}, 订阅者: {len(matching_subs)}")

    def publish_sync(self, event_type: str, data: Dict[str, Any]) -> None:
        """同步发布事件（便捷方法）"""
        event = Event(event_type=event_type, data=data)
        self.publish(event)

    def _async_publish(self, subscription: Subscription, event: Event) -> None:
        """异步发布事件"""
        self.async_queue.append((subscription, event))

    def _worker_loop(self) -> None:
        """工作线程循环"""
        while self.running:
            if self.async_queue:
                with self.lock:
                    if self.async_queue:
                        subscription, event = self.async_queue.popleft()
                    else:
                        continue

                try:
                    subscription.callback(event)
                except Exception as e:
                    self.logger.error(f"异步事件回调失败 ({subscription.subscription_id}): {e}")
            else:
                time.sleep(0.01)

    def start_async_workers(self) -> None:
        """启动异步工作线程"""
        if self.running:
            return

        self.running = True

        for i in range(self.async_workers):
            thread = threading.Thread(
                target=self._worker_loop,
                name=f"EventBusWorker-{i}",
                daemon=True
            )
            thread.start()
            self.worker_threads.append(thread)

        self.logger.info(f"已启动 {self.async_workers} 个异步工作线程")

    def stop_async_workers(self) -> None:
        """停止异步工作线程"""
        self.running = False

        for thread in self.worker_threads:
            thread.join(timeout=1.0)

        self.worker_threads.clear()
        self.logger.info("异步工作线程已停止")

    def get_subscription_count(self, event_type: Optional[str] = None) -> int:
        """获取订阅数量"""
        with self.lock:
            if event_type is None:
                return len(self.subscriptions)
            else:
                return len(self.event_type_subscriptions.get(event_type, []))

    def get_event_history(self, event_type: Optional[str] = None, limit: int = 100) -> List[Event]:
        """获取事件历史"""
        events = list(self.event_history)

        if event_type is not None:
            events = [e for e in events if e.event_type == event_type]

        return events[-limit:]

    def clear_history(self) -> None:
        """清空事件历史"""
        self.event_history.clear()
        self.logger.debug("事件历史已清空")

    def __enter__(self):
        """上下文管理器入口"""
        self.start_async_workers()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop_async_workers()
