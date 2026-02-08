import asyncio
from typing import Dict, Set, Any
from sse_starlette.sse import EventSourceResponse
import json


class SSEManager:
    """Менеджер для управления SSE соединениями"""
    
    def __init__(self):
        self.connections: Dict[str, Set[asyncio.Queue]] = {}
        self.connection_id_counter = 0
    
    def _generate_connection_id(self) -> str:
        """Генерация уникального ID для соединения"""
        self.connection_id_counter += 1
        return f"conn_{self.connection_id_counter}"
    
    async def add_connection(self, channel: str = "default") -> EventSourceResponse:
        """Добавление нового SSE соединения"""
        if channel not in self.connections:
            self.connections[channel] = set()
        
        queue = asyncio.Queue(maxsize=10)
        self.connections[channel].add(queue)
        
        async def event_generator():
            try:
                # Ждем сообщения в очереди
                while True:
                    message = await queue.get()
                    yield message
                    
            except asyncio.CancelledError:
                # Клиент отключился
                await self.remove_connection(queue, channel)
            finally:
                # Всегда очищаем соединение при завершении
                await self.remove_connection(queue, channel)
        
        return EventSourceResponse(event_generator(), ping=600)
    
    async def remove_connection(self, queue: asyncio.Queue, channel: str):
        """Удаление соединения"""
        if channel in self.connections and queue in self.connections[channel]:
            self.connections[channel].remove(queue)
            if not self.connections[channel]:
                del self.connections[channel]
    
    async def send_message(
        self,
        data: Any,
        event: str = 'message',
        channel: str = 'default'
    ):
        """Отправка сообщения всем подписчикам канала"""
        if channel not in self.connections:
            return
        
        message = {
            'event': event,
            'data': json.dumps(data, ensure_ascii=False) if not isinstance(data, str) else data
        }
        
        for queue in list(self.connections[channel]):
            try:
                await queue.put(message)
            except Exception:
                # Если очередь полна или клиент отключился, удаляем соединение
                await self.remove_connection(queue, channel)
    
    async def send_to_all(self, data: Any, event: str = 'message'):
        """Отправка сообщения во все каналы"""
        for channel in list(self.connections.keys()):
            await self.send_message(data, event, channel)
    
    def get_stats(self) -> Dict:
        """Получение статистики подключений"""
        return {
            'total_channels': len(self.connections),
            'connections_per_channel': {
                channel: len(queues) 
                for channel, queues in self.connections.items()
            },
            'total_connections': sum(
                len(queues) for queues in self.connections.values()
            )
        }


# Создаем глобальный экземпляр менеджера
sse_manager = SSEManager()
