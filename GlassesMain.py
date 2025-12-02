from google import genai
import pyaudio
import wave
from pydub import AudioSegment
import keyboard
import pyttsx3
import threading
import time

FORMAT = pyaudio.paInt16  # 16-bit audio
CHANNELS = 1              # Mono audio
RATE = 44100              # Sample rate (samples per second)
CHUNK = 1024              # Frames per buffer
WAVE_OUTPUT_FILENAME = "recorded_audio.wav"
audio = pyaudio.PyAudio()
client = genai.Client()

# Recording state
recording_event = threading.Event()
record_thread = None
rec_stream = None
rec_frames = []

def _record_worker():
    global rec_frames, rec_stream
    while recording_event.is_set():
        data = rec_stream.read(CHUNK, exception_on_overflow=False)
        rec_frames.append(data)

def start_recording():
    global rec_frames, rec_stream, record_thread
    if recording_event.is_set():
        return
    rec_frames = []
    rec_stream = audio.open(format=FORMAT,
                            channels=CHANNELS,
                            rate=RATE,
                            input=True,
                            frames_per_buffer=CHUNK)
    recording_event.set()
    record_thread = threading.Thread(target=_record_worker, daemon=True)
    record_thread.start()
    print("Recording started...")

def stop_recording():
    global rec_stream, record_thread, rec_frames
    if not recording_event.is_set():
        return
    recording_event.clear()
    print("Recording stopped.")
    rec_stream.stop_stream()
    rec_stream.close()
    waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    waveFile.setnchannels(CHANNELS)
    waveFile.setsampwidth(audio.get_sample_size(FORMAT))
    waveFile.setframerate(RATE)
    waveFile.writeframes(b''.join(rec_frames))
    waveFile.close()
    print(f"Audio saved to {WAVE_OUTPUT_FILENAME}")
    processed_sound = AudioSegment.from_wav(WAVE_OUTPUT_FILENAME)
    processed_sound.export("output/processedclip.mp3", format="mp3")
    Prompt()

def Prompt():
    uploaded = client.files.upload(file="output/processedclip.mp3")
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[uploaded],
    )
    pyttsx3.speak(response.text)
    print("audio said")
    print("wait2.5sec")
    time.sleep(2.5)
def Loop():
    keyboard.on_press_key('r', lambda e: start_recording())
    keyboard.on_release_key('r', lambda e: stop_recording())
while True:
    Loop()
