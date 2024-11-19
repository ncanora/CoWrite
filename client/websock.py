import websockets
import asyncio
from queue import Queue
from threading import Thread

message_queue = Queue()

websocket_loop = None


async def connect_to_host(ip, port):
    uri = f"ws://{ip}:{port}/ws"
    try:
        async with websockets.connect(uri) as websocket:
            message = await websocket.recv()
            print(f"< {message}")
            # You can add more logic here to handle messages
    except Exception as e:
        print(f"Error connecting to server at {uri}: {e}")

def run_connect_to_host(ip, port):
    asyncio.run(connect_to_host(ip, port))