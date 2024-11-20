import websockets
import asyncio
from queue import Queue
from threading import Thread
import GLOBALS
import aioconsole

ws = None

async def connect_to_host(ip, port, name, hash_key, text_editor):
    uri = f"ws://{ip}:{port}/ws"
    try:
        ws = websockets.connect(uri)
        while True:
            async with websockets.connect(uri) as websocket:
                message = await websocket.recv()
                await manage_message_queue(text_editor)
                print(f"< {message}")
                # You can add more logic here to handle messages
    except Exception as e:
        print(f"Error connecting to server at {uri}: {e}")

async def send_message_loop():
    while True:
        s = await aioconsole.ainput("Send to server: ")
        await GLOBALS.SEND_QUEUE.append(s)
        await ws.send(s)

async def manage_message_queue(text_editor):
    size = await len(GLOBALS.SEND_QUEUE)
    while True:
        if size > 0:
            printf(GLOBALS.SEND_QUEUE.get())

def run_websocket_manager(ip, port, name, hash_key, text_editor):
    asyncio.run(connect_to_host(ip, port, name, hash_key, text_editor))
    asyncio.run(send_message_loop())
    asyncio.run(send_message_loop())