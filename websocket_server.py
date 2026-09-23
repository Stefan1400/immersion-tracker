import asyncio
import websockets


async def handler(websocket):
    print("Next.js connected!")

    await websocket.send("ja")

    await asyncio.sleep(5)

    await websocket.send("en")


async def main():
    async with websockets.serve(handler, "localhost", 8765):
        print("WebSocket server running on ws://localhost:8765")
        await asyncio.Future()


asyncio.run(main())