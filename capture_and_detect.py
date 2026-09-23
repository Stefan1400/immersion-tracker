from scipy.signal import resample_poly
from faster_whisper import WhisperModel
import pyaudiowpatch as pyaudio
import time
import numpy as np
import asyncio
import websockets

connected_clients = set()

async def handler(websocket):
      connected_clients.add(websocket)

      print("Next.js connected!")

      try:
            await websocket.wait_closed()
      finally:
            connected_clients.remove(websocket)
            print("Next.js disconnected!")


async def send_detection(result):
      for websocket in connected_clients:
            await websocket.send(result)


p = pyaudio.PyAudio()

device = p.get_device_info_by_index(14)

channels = int(device["maxInputChannels"])
rate = int(device["defaultSampleRate"])

print("Device:", device["name"])

stream = p.open(
    format=pyaudio.paInt16,
    channels=channels,
    rate=rate,
    input=True,
    input_device_index=14,
    frames_per_buffer=1024,
)

print("Loading Whisper...")

model = WhisperModel(
    "tiny",
    device="cpu",
    compute_type="int8"
)

print("Listening continuously...")
print("Press Ctrl+C to stop.")

def detect_audio():
      print("\nRecording for 5 seconds...")

      frames = []
      start_time = time.time()

      while time.time() - start_time < 5:
            data = stream.read(1024)
            frames.append(data)

      print("Audio captured.")
      print("Converting audio...")

      audio_bytes = b"".join(frames)

      audio = np.frombuffer(
            audio_bytes,
            dtype=np.int16
      )

      audio = audio.reshape(-1, channels)

      audio = audio.mean(axis=1)

      audio = audio.astype(np.float32) / 32768.0

      audio = resample_poly(
            audio,
            16000,
            rate
      )

      print("Detecting language...")

      segments, info = model.transcribe(
            audio,
            vad_filter=True
      )

      print(f"Language: {info.language}")
      print(f"Probability: {info.language_probability}")

      is_japanese = info.language == 'ja'

      if is_japanese:
            return 'ja'
      else:
            return 'not_ja'
            


async def main():
      async with websockets.serve(handler, "localhost", 8765):
            print("WebSocket server running on ws://localhost:8765")
            print("Listening continuously...")

            while True:
                  result = await asyncio.to_thread(detect_audio)
                  await send_detection(result)


try: 
      asyncio.run(main())
      
except KeyboardInterrupt:
    print("\nStopped.")

finally:
    stream.stop_stream()
    stream.close()
    p.terminate()