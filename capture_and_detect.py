import pyaudiowpatch as pyaudio
import time
import numpy as np
from scipy.signal import resample_poly
from faster_whisper import WhisperModel

p = pyaudio.PyAudio()

device = p.get_device_info_by_index(14)

channels = int(device["maxInputChannels"])
rate = int(device["defaultSampleRate"])

print("Device:", device["name"])
print("Recording for 5 seconds...")

stream = p.open(
    format=pyaudio.paInt16,
    channels=channels,
    rate=rate,
    input=True,
    input_device_index=14,
    frames_per_buffer=1024,
)

frames = []
start_time = time.time()

while time.time() - start_time < 5:
    data = stream.read(1024)
    frames.append(data)

stream.stop_stream()
stream.close()
p.terminate()

print("Audio captured.")
print("Converting audio...")

audio_bytes = b"".join(frames)

audio = np.frombuffer(audio_bytes, dtype=np.int16)

audio = audio.reshape(-1, channels)

audio = audio.mean(axis=1)

audio = audio.astype(np.float32) / 32768.0

audio = resample_poly(audio, 16000, rate)

print("Running Whisper...")

model = WhisperModel(
    "tiny",
    device="cpu",
    compute_type="int8"
)

segments, info = model.transcribe(
    audio,
    vad_filter=True
)

print(f"Language: {info.language}")
print(f"Probability: {info.language_probability}")

for segment in segments:
    print(f"{segment.start:.1f}s - {segment.end:.1f}s: {segment.text}")