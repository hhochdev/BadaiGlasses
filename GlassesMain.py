from google import genai
import pyaudio
import wave
from pydub import AudioSegment
import keyboard
FORMAT = pyaudio.paInt16  # 16-bit audio
CHANNELS = 1              # Mono audio
RATE = 44100              # Sample rate (samples per second)
CHUNK = 1024              # Frames per buffer
RECORD_SECONDS = 5        # Duration of recording
WAVE_OUTPUT_FILENAME = "recorded_audio.wav"
audio = pyaudio.PyAudio()
while True:
    if keyboard.is_pressed('r'):
        break
stream = audio.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
print("Recording started...")
frames = []
for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK)
    frames.append(data)
print("Recording stopped.")
stream.stop_stream()
stream.close()
audio.terminate()
waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
waveFile.setnchannels(CHANNELS)
waveFile.setsampwidth(audio.get_sample_size(FORMAT))
waveFile.setframerate(RATE)
waveFile.writeframes(b''.join(frames))
waveFile.close()
print(f"Audio saved to {WAVE_OUTPUT_FILENAME}")
processed_sound = AudioSegment.from_wav(WAVE_OUTPUT_FILENAME)
processed_sound.export("output/processedclip.mp3", format="mp3")
client = genai.Client()
audio = client.files.upload(file="output/processedclip.mp3")
response = client.models.generate_content(

    model="gemini-2.0-flash",
    contents=[audio],
)

print(response.text)
response = client.models.generate_content(

    model="gemini-2.0-flash",
    contents=[input(":")],
)
print(response.text)