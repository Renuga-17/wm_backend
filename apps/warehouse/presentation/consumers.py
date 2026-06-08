import json
from channels.generic.websocket import AsyncWebsocketConsumer

class OccupancyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = 'occupancy_updates'
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
    async def occupancy_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))
