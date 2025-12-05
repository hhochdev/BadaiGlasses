import RPi.GPIO as GPIO
from google import genai
import pyaudio
import wave
from pydub import AudioSegment
import pyttsx3
import threading
import time
GPIO.setmode(GPIO.BOARD)
GPIO.setup(10, GPIO.IN)
FORMAT = pyaudio.paInt16  # 16-bit audio
CHANNELS = 1              # Mono audio
RATE = 44100              # Sample rate (samples per second)
CHUNK = 1024              # Frames per buffer
WAVE_OUTPUT_FILENAME = "output/recorded_audio.wav"
audio = pyaudio.PyAudio()
client = genai.Client()

# Recording state
recording_event = threading.Event()
global record_thread
global rec_stream
global rec_frames
rec_frames = []
rec_stream = None
record_thread = None
def _record_worker():
    while recording_event.is_set():
        data = rec_stream.read(CHUNK, exception_on_overflow=False)
        rec_frames.append(data)

def start_recording():
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
    if not recording_event.is_set():
        return
    # Signal worker to stop
    recording_event.clear()
    print("Stopping recording...")
    # Close the stream to unblock the worker's read()
    if rec_stream is not None:
        rec_stream.stop_stream()
        rec_stream.close()

    # Join the worker briefly; it's a daemon so don't block indefinitely
    if record_thread is not None:
        record_thread.join(timeout=1.0)

    print("Recording stopped.")

    # Save recorded data
    waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    waveFile.setnchannels(CHANNELS)
    waveFile.setsampwidth(audio.get_sample_size(FORMAT))
    waveFile.setframerate(RATE)
    waveFile.writeframes(b''.join(rec_frames))
    waveFile.close()
    print(f"Audio saved to {WAVE_OUTPUT_FILENAME}")

    processed_sound = AudioSegment.from_wav(WAVE_OUTPUT_FILENAME)
    processed_sound.export("output/processedclip.mp3", format="mp3")

    # Run Prompt asynchronously so the key-release handler returns quickly
    threading.Thread(target=Prompt, daemon=True).start()

def Prompt():
    uploaded = client.files.upload(file="output/processedclip.mp3")
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[uploaded],
    )
    pyttsx3.speak(response.text)
    print("audio said")
    
# Register keyboard handlers once
GPIO.add_event_detect(10, GPIO.HIGH, start_recording)
GPIO.add_event_detect(10, GPIO.LOW, stop_recording)
GPIO.add_event_detect(10, GPIO.HIGH, start_recording)
print("Ready: hold 'r' to record, release to send to Prompt().")
while True:
    time.sleep(1)
