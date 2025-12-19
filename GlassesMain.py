from google import genai
import pyaudio
import wave
from pydub import AudioSegment
from pynput import keyboard
import pyttsx3
import threading
import time
import cv2
is_pressed = False
frame_count = 0
currently_pressed = set()
combination = {keyboard.Key.cmd_l, keyboard.Key.cmd_r} 
FORMAT = pyaudio.paInt16  # 16-bit audio
CHANNELS = 1              # Mono audio
RATE = 44100              # Sample rate (samples per second)
CHUNK = 1024              # Frames per buffer
WAVE_OUTPUT_FILENAME = "output/recorded_audio.wav"
audio = pyaudio.PyAudio()
client = genai.Client()

# Recording state
recording_event = threading.Event()
rec_frames = []
rec_stream = None
record_thread = None
def cap_image(framenum):
    global frame_count
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_count == framenum:
            ret, frame = cap.read()
            cv2.imwrite("output/capimage.png", frame)
            frame_count = 0
            break
        frame_count += 1
def _record_worker():
    global rec_stream
    global rec_frames
    while recording_event.is_set():
        data = rec_stream.read(CHUNK, exception_on_overflow=False)
        rec_frames.append(data)

def start_recording(key):
    global is_pressed
    if key in combination:
        currently_pressed.add(key)

    if currently_pressed == combination:
        is_pressed = True
        print('pressed!')
        cap_image(7)
    global rec_frames, rec_stream
    if is_pressed:
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
    is_pressed = False
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
    sound = client.files.upload(file="output/processedclip.mp3")
    image = client.files.upload(file="output/capimage.png")

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[sound, image],
    )
    pyttsx3.speak(response.text)
    print(response.text)
    print("audio said")
# Register keyboard handlers once
listener = keyboard.Listener(
    on_press=start_recording,
    on_release=stop_recording)
listener.start()

print("Ready: hold 'r' to record, release to send to Prompt().")
while True:
    time.sleep(1)
