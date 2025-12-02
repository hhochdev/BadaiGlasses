from google import genai
import pyaudio
import wave
from pydub import AudioSegment
import keyboard
import pyttsx3
engine = pyttsx3.init()
FORMAT = pyaudio.paInt16  # 16-bit audio
CHANNELS = 1              # Mono audio
RATE = 44100              # Sample rate (samples per second)
CHUNK = 1024              # Frames per buffer
RECORD_SECONDS = 5        # Duration of recording
WAVE_OUTPUT_FILENAME = "recorded_audio.wav"
audio = pyaudio.PyAudio()
client = genai.Client()
rate = engine.getProperty('rate')   # getting details of current speaking rate
print (rate)                        # printing current voice rate
engine.setProperty('rate', 125)     # setting up new voice rate
volume = engine.getProperty('volume')   # getting to know current volume level (min=0 and max=1)
print (volume)                          # printing current volume level
engine.setProperty('volume',1.0)        # setting up volume level  between 0 and 1
voices = engine.getProperty('voices')       # getting details of current voice
engine.setProperty('voice', voices[1].id)
def RecordAudio():
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
def Prompt():
    audio = client.files.upload(file="output/processedclip.mp3")
    response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=[audio],
    )
    engine.say(response.text)
    engine.runAndWait()
    engine.stop()
    print("audio said")
while True:
    if keyboard.is_pressed('r'):
        RecordAudio()
        Prompt()
