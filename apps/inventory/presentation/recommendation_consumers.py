import json
from channels.generic.websocket import AsyncWebsocketConsumer

class RecommendationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = 'recommendation_updates'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # Receive message from room group
    async def recommendation_message(self, event):
        # Send complete event dictionary to WebSocket client
        await self.send(text_data=json.dumps(event))


class CongestionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = 'congestion_alerts'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def congestion_message(self, event):
        await self.send(text_data=json.dumps(event))


class SlottingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = 'slotting_alerts'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def slotting_message(self, event):
        await self.send(text_data=json.dumps(event))


class AlertConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = 'system_alerts'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def alert_message(self, event):
        await self.send(text_data=json.dumps(event))

