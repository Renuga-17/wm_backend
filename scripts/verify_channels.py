import os
import django
import sys

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from config.asgi import application
from channels.layers import get_channel_layer
import asyncio

async def test_channels():
    channel_layer = get_channel_layer()
    if channel_layer:
        print(f"Successfully loaded channel layer: {channel_layer}")
    else:
        print("Failed to load channel layer")

if __name__ == "__main__":
    print("ASGI application instantiated successfully.")
    asyncio.run(test_channels())
