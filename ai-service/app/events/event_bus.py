"""Central In-Process Pub/Sub Event Bus decoupling AI Producers, Persistence, and WebSockets."""
import asyncio
from typing import Callable, Dict, List, Any
from app.events.event_schema import CampusEvent

class CampusEventBus:
    def __init__(self):
        # Event type -> list of sync callbacks
        self._sync_subscribers: Dict[str, List[Callable[[CampusEvent], None]]] = {}
        # Event type -> list of async queues / callbacks
        self._async_subscribers: Dict[str, List[asyncio.Queue]] = {}

    def subscribe(self, event_type: str, callback: Callable[[CampusEvent], None]):
        """Subscribes a synchronous listener to an event topic ('*' for all events)."""
        if event_type not in self._sync_subscribers:
            self._sync_subscribers[event_type] = []
        self._sync_subscribers[event_type].append(callback)

    def subscribe_async(self, event_type: str = "*") -> asyncio.Queue:
        """Subscribes an asyncio Queue for WebSocket broadcasts or async workers."""
        q = asyncio.Queue(maxsize=100)
        if event_type not in self._async_subscribers:
            self._async_subscribers[event_type] = []
        self._async_subscribers[event_type].append(q)
        return q

    def unsubscribe_async(self, queue: asyncio.Queue, event_type: str = "*"):
        if event_type in self._async_subscribers and queue in self._async_subscribers[event_type]:
            self._async_subscribers[event_type].remove(queue)

    def publish(self, event: CampusEvent):
        """Publishes an event to matching sync listeners and async queues."""
        # Sync listeners for specific type and wildcard
        for topic in (event.event_type, "*"):
            if topic in self._sync_subscribers:
                for cb in self._sync_subscribers[topic]:
                    try:
                        cb(event)
                    except Exception as e:
                        print(f"[EventBus] Error in sync subscriber ({topic}): {e}")

        # Async queues for specific type and wildcard
        for topic in (event.event_type, "*"):
            if topic in self._async_subscribers:
                for q in self._async_subscribers[topic]:
                    try:
                        if not q.full():
                            q.put_nowait(event)
                        else:
                            # Drop oldest if congested
                            try:
                                q.get_nowait()
                            except asyncio.QueueEmpty:
                                pass
                            q.put_nowait(event)
                    except Exception as e:
                        print(f"[EventBus] Error in async subscriber queue ({topic}): {e}")

# Global singleton event bus instance
default_event_bus = CampusEventBus()

