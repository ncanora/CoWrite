import asyncio
import websockets
from threading import Thread
import json
import queue
import time

class WebSocketClient:
    def __init__(self, uri, send_queue, receive_queue):
        self.uri = uri
        self.send_queue = send_queue  # queue.Queue()
        self.receive_queue = receive_queue  # queue.Queue()
        self.loop = asyncio.new_event_loop()
        self.batch_interval = 0.1  # Time interval to batch messages (in seconds)

    def start(self):
        t = Thread(target=self.run, daemon=True)
        t.start()

    def run(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.main())

    async def main(self):
        try:
            async with websockets.connect(self.uri) as websocket:
                # Send initial connection message
                initial_message = self.send_queue.get()
                await websocket.send(initial_message)

                send_task = asyncio.create_task(self.send_messages(websocket))
                receive_task = asyncio.create_task(self.receive_messages(websocket))
                await asyncio.gather(send_task, receive_task)
        except Exception as e:
            print(f"WebSocket error: {e}")

    async def send_messages(self, websocket):
        while True:
            messages = []
            try:
                # Wait for the first message (blocking)
                message = await self.loop.run_in_executor(None, self.send_queue.get)
                if message is None:
                    break  # None is a signal to close the connection

                # Decode the JSON string back to a Python dictionary
                message_dict = json.loads(message)
                messages.append(message_dict)

                # Batch messages within the specified interval
                batch_start_time = time.time()
                while time.time() - batch_start_time < self.batch_interval:
                    try:
                        # Non-blocking get with a small timeout
                        message = self.send_queue.get_nowait()
                        if message is None:
                            break  # None is a signal to close the connection

                        # Decode the JSON string back to a Python dictionary
                        message_dict = json.loads(message)
                        messages.append(message_dict)
                    except queue.Empty:
                        await asyncio.sleep(0.01)  # Sleep briefly if no message is available

                # Send batched messages as a JSON array if more than one message
                if len(messages) == 1:
                    # Serialize the single message back to a JSON string
                    await websocket.send(json.dumps(messages[0]))
                    print(f"Sent single message: {messages[0]}")  # Debugging statement
                else:
                    # Serialize the list of messages to a JSON array
                    await websocket.send(json.dumps(messages))
                    print(f"Sent batched messages: {messages}")  # Debugging statement
            except Exception as e:
                print(f"Error in send_messages: {e}")
                break

    async def receive_messages(self, websocket):
        async for message in websocket:
            try:
                data = json.loads(message)
                if isinstance(data, list):
                    for msg in data:
                        self.receive_queue.put(json.dumps(msg))
                else:
                    self.receive_queue.put(json.dumps(data))
            except json.JSONDecodeError:
                # If JSON decoding fails, treat as a raw message
                self.receive_queue.put(message)

    def close(self):
        self.send_queue.put(None)
