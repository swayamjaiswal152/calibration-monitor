import json
import asyncio
from fastapi import WebSocket
from typing import List, Optional
from redis.asyncio import Redis
from redis.asyncio.client import PubSub
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

class ConnectionManager:
    def __init__(self):
        self.active: List[WebSocket] = []
        self.redis: Optional[Redis] = None
        self.pubsub: Optional[PubSub] = None
        self._listener_task = None

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)
        # Start Redis listener on first connection
        if not self._listener_task:
            self.redis = Redis.from_url(REDIS_URL, decode_responses=True)
            self.pubsub = self.redis.pubsub()
            await self.pubsub.subscribe("metrics_channel")
            self._listener_task = asyncio.create_task(self.listen_redis())

    async def listen_redis(self):
        if not self.pubsub:
            return
        # All API pods subscribe to Redis. When worker publishes, ALL pods forward to their clients
        async for msg in self.pubsub.listen():
            if msg["type"] == "message":
                data = json.loads(msg["data"])
                for ws in list(self.active):
                    try:
                        await ws.send_json(data)
                    except:
                        pass

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

manager = ConnectionManager()