from scipy.signal import resample_poly
from faster_whisper import WhisperModel
import pyaudiowpatch as pyaudio

import asyncio
import math
import threading
import time
from collections import deque
from queue import Queue, Empty

import numpy as np
import websockets
import json


# -------------------------
# WebSocket state
# -------------------------

connected_clients = set()


async def handler(websocket):
    connected_clients.add(websocket)
    print("Next.js connected!")

    try:
        await websocket.wait_closed()
    finally:
        connected_clients.discard(websocket)
        print("Next.js disconnected!")


async def send_detection(result):
    for websocket in connected_clients.copy():
        await websocket.send(result)


# -------------------------
# Audio setup
# -------------------------

p = pyaudio.PyAudio()

device_index = 14
device = p.get_device_info_by_index(device_index)

channels = int(device["maxInputChannels"])
rate = int(device["defaultSampleRate"])
chunk_size = 1024

print("Device:", device["name"])

stream = p.open(
    format=pyaudio.paInt16,
    channels=channels,
    rate=rate,
    input=True,
    input_device_index=device_index,
    frames_per_buffer=chunk_size,
)


# -------------------------
# Whisper setup
# -------------------------

print("Loading Whisper...")

model = WhisperModel(
    "tiny",
    device="cpu",
    compute_type="int8"
)


# -------------------------
# Shared state
# -------------------------

buffer_seconds = 5

max_buffer_chunks = math.ceil(
    buffer_seconds * rate / chunk_size
)

audio_buffer = deque(maxlen=max_buffer_chunks)

buffer_lock = threading.Lock()
buffer_ready = threading.Event()
stop_event = threading.Event()

detection_queue = Queue()

# -------------------------
# Audio capture thread
# -------------------------

def capture_audio():
    print("Starting continuous audio capture...")

    while not stop_event.is_set():
        try:
            data = stream.read(
                chunk_size,
                exception_on_overflow=False
            )

            with buffer_lock:
                audio_buffer.append(data)

                if len(audio_buffer) >= max_buffer_chunks:
                    buffer_ready.set()

        except Exception as error:
            print("Audio capture error:", error)
            break


# -------------------------
# Whisper detection thread
# -------------------------

def detect_audio():
    print("Waiting for 5 seconds of audio...")

    buffer_ready.wait()

    print("5-second buffer ready.")
    print("Starting language detection...")

    while not stop_event.is_set():

        # Take a snapshot of the latest 5 seconds.
        with buffer_lock:
            frames = list(audio_buffer)

        audio_bytes = b"".join(frames)

        # Convert bytes → NumPy audio.
        audio = np.frombuffer(
            audio_bytes,
            dtype=np.int16
        )

        audio = audio.reshape(-1, channels)

        # Convert stereo → mono.
        audio = audio.mean(axis=1)

        # Convert int16 → float32.
        audio = audio.astype(np.float32) / 32768.0

        # Convert sample rate → 16 kHz.
        audio = resample_poly(
            audio,
            16000,
            rate
        )

        print("\nAnalyzing latest 5 seconds...")

        segments, info = model.transcribe(
            audio,
            vad_filter=True
        )

        print(f"Language: {info.language}")
        print(f"Probability: {info.language_probability}")

        if info.language == "ja":
            result = "ja"
        else:
            result = "not_ja"

        detection_queue.put(result)

        # Wait approximately one second before analyzing
        # the next rolling 5-second window.
        stop_event.wait(1)


# -------------------------
# WebSocket + detection
# -------------------------

total_immersion_time = 0
immersion_started_at = None
is_immersing = False


def get_detection():
    try:
        return detection_queue.get(timeout=0.5)
    except Empty:
        return None


async def main():
    global capture_thread
    global detection_thread
    global total_immersion_time
    global immersion_started_at
    global is_immersing

    async with websockets.serve(
        handler,
        "localhost",
        8765
    ):
        print("WebSocket server running on ws://localhost:8765")
        print("Listening continuously...")

        capture_thread = threading.Thread(
            target=capture_audio,
            daemon=True
        )

        detection_thread = threading.Thread(
            target=detect_audio,
            daemon=True
        )

        capture_thread.start()
        detection_thread.start()

        while not stop_event.is_set():
            result = await asyncio.to_thread(
                get_detection
            )

            if result is not None:

                if result == 'ja':
                    if not is_immersing:
                        is_immersing = True
                        immersion_started_at = time.time()

                elif result == 'not_ja':
                    if is_immersing:
                        now = time.time()

                        total_immersion_time += (
                            now - immersion_started_at
                        )

                        is_immersing = False
                        immersion_started_at = None

                current_immersion_time = total_immersion_time

                if is_immersing:
                    current_immersion_time += (
                        time.time() - immersion_started_at
                    )

                print(
                    f"total_immersion_time: "
                    f"{current_immersion_time}"
                )

                await send_detection(json.dumps({
                    'language': result,
                    'total_immersion_in_seconds': int(
                        current_immersion_time
                    )
                }))



# -------------------------
# Start / shutdown
# -------------------------

capture_thread = None
detection_thread = None

try:
    asyncio.run(main())

except KeyboardInterrupt:
    print("\nStopped.")

finally:
    stop_event.set()

    if capture_thread is not None:
        capture_thread.join(timeout=1)

    if detection_thread is not None:
        detection_thread.join(timeout=1)

    stream.stop_stream()
    stream.close()
    p.terminate()