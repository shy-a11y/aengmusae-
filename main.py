import os
#Prevent library conflict
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import sys
import time
import wave
import pyaudio
import keyboard
from faster_whisper import WhisperModel


sys.stdout.reconfigure(encoding='utf-8')
'''
Model setting part
'''
MODEL_SIZE = "medium"
OUTPUT_FILE= "Lecture_note.txt"
TEMP_AUDIO = "temp_input.wav"

"""
Record manipulation key setting
"""
START_KEY = 'f9'
STOP_KEY = 'f10'
EXIT_KEY = 'esc'

print("Loading the model...")

try:
    whisper_model = WhisperModel(MODEL_SIZE, device = "auto", compute_type="int8")
except Exception:
    print("Failed to accelerate GPU, converting to CPU mode...")
    whisper_model = WhisperModel(MODEL_SIZE, device = "cpu", compute_type="int8")
print("Model loading done!")

def record_audio_continuously(filename):
    chunk = 1024
    format = pyaudio.paInt16
    channels = 1
    rate = 44100
    p = pyaudio.PyAudio()

    stream = p.open(format = format, channels = channels, rate=rate, input=True, frames_per_buffer=chunk)
    frames = []

    print(f"\nStart lecture (Press {STOP_KEY} Key if you wanna stop the lecture)")

    while True:
        try:
            data = stream.read(chunk)
            frames.append(data)
            if keyboard.is_pressed(STOP_KEY):
                print("Stop recording and start converting")
                break
        except IOError:
            continue
    stream.stop_stream()
    stream.close()
    p.terminate()

    with wave.open(filename,'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(p.get_sample_size(format))
        wf.setframerate(rate)
        wf.writeframes(b''.join(frames))

def transcribe_audio(filename):
    """
    Converting recorded file to text
    Speech to text
    """
    custom_prompt = "이 강의는 한국어와 영어가 자연스럽게 섞여 있는 언어 강의 입니다. The lecture mixes korean and english naturally."

    segments, info = whisper_model.transcribe(
        filename,
        beam_size=5,
        initial_prompt = custom_prompt
    )

    text=""
    for segment in segments:
        text += segment.text
    return text

def main():
    print("\n" + "="*60)
    print("     Writing down")
    print(f"   [{START_KEY}] Key: Start recording")
    print(f"   [{STOP_KEY}] Key: Stop recording and convert the text...")
    print(f"   [{EXIT_KEY}] Key: Terminate the program ")
    print("="*60)

    while True:
        if keyboard.is_pressed(EXIT_KEY):
            print("\nTerminating program")
            break
        if keyboard.is_pressed(START_KEY):
            record_audio_continuously(TEMP_AUDIO)

            if not os.path.exists(TEMP_AUDIO):
                print("There is no file recorded")
                time.sleep(1)
                continue

            print("Converting to the text,,,")
            result_text = transcribe_audio(TEMP_AUDIO)

            if not result_text.strip():
                print("Voice isnt recognised. try again.\n")
                continue
            print(f"\nRecorded text: {result_text}")

            current_time = time.strftime('%Y-%m-%d %H:%M:%S')
            with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{current_time}] {result_text}\n")
            
            print(f"Saved at {OUTPUT_FILE}...\n")
            time.sleep(1)
if __name__=="__main__":
    main()



