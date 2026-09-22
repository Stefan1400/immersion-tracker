from faster_whisper import WhisperModel

model = WhisperModel("tiny", device="cpu", compute_type="int8")

segments, info = model.transcribe(
   "./test.mp4",
   vad_filter=True
)

print(f"Language: {info.language}")
print(f"Probability: {info.language_probability}")

for segment in segments:
   print(
      f"{segment.start:.1f}s - {segment.end:.1f}s: "
      f"{segment.text}"
   )