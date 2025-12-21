import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import sys
import time
import wave
import pyaudio
import keyboard
import ollama
from faster_whisper import WhisperModel


sys.stdout.reconfigure(encoding='utf-8')
'''
Model setting part
'''
MODEL_SIZE = "small"
OUTPUT_FILE= "Lecture_content.txt"
TEMP_AUDIO = "temp_input.wav"

"""
Record manipulation key setting
"""
START_KEY = 'f9'
STOP_KEY = 'f10'
EXIT_KEY = 'esc'

print("Loading the model...")
whisper_model = WhisperModel(MODEL_SIZE, device = "auto", compute_type="int8")
print("Model loading done!")

"""
Record until stop key is pressed.
"""
def record_audio_continuously(filename):
    chunk = 1024
    format = pyaudio.paInt16
    channels = 1
    rate = 44100
    p = pyaudio.PyAudio()

    stream = p.open(format=format, channels=channels, rate=rate, input=True, frames_per_buffer=chunk)
    frames = []

    print(f"\n Start the lesson..Press {STOP_KEY} to stop")
    while True:
        try:
            data = stream.read(chunk) 
            frames.append(data)

            if keyboard.is_pressed(STOP_KEY):
                print(f"Record terminated. Converting the speech..")
                break
        except IOError:
            #Prevent buffer overflow
            continue
    
    stream.stop_stream()
    stream.close()
    p.terminate()

    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(p.get_sample_size(format))
        wf.setframerate(rate)
        wf.writeframes(b''.join(frames))

def transcribe_audio(filename):
    segments, info = whisper_model.transcribe(filename, beam_size=5)
    text=""
    for segment in segments:
        text += segment.text
    return text

def correct_grammar_with_llama(text):
    """Correct grammar using Ollama model Llama 3"""
    prompt = f"""
    당신은 한국어와 영어를 사용하는 강의 전문 에디터입니다.
    아래 [입력된 텍스트]를 보고 영어와 한국어를 정확하게 인식해서 그대로 기록해주세요.

    규칙:
    1. 한국어와 영어가 섞인 문맥을 자연스럽게 유지하세요.
    2. '응답'이나 '설명'을 덧붙이지 말고 가능한한 정교하게 음성을 인식하고 그대로 출력해주세요.

    [입력된 텍스트]: {text}
    """

    response = ollama.chat(model='llama3', messages=[
        {'role':'user', 'content': prompt},
    ])
    return response['message']['content']

def main():
    print("\n" + "="*60)
    print(" AI lecture assistant Aengmusae")
    print(f"  [{START_KEY}] Key: start recording")
    print(f"  [{STOP_KEY}] Key: stop recording and start converting")
    print(f"  [{EXIT_KEY}] Key: terminate program")
    print("="*60)

    while True:
        if keyboard.is_pressed(EXIT_KEY):
            print("\nTerminate the program.")
        if keyboard.is_pressed(START_KEY):
            record_audio_continuously(TEMP_AUDIO)
            if not os.path.exists(TEMP_AUDIO):
                print("There is no recorded file :)")
                time.sleep(1)
                continue
            print("Converting text....")
            original_text= transcribe_audio(TEMP_AUDIO)

            if not original_text.strip():
                print("Voice is not recognised. Sorry!")
                continue
            print(f"\n [Original]: {original_text}")

            print("Correcting the grammar and organizing the content of the class..")
            corrected_text = correct_grammar_with_llama(original_text)
            print(f"Corrected text: {corrected_text}")

            current_time = time.strftime('%Y-%m-%d %H:%M:%S')
            with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                f.write(f"\n[{current_time}]\n")
                f.write(f"Original content: {original_text}\n")
                f.write(f"Corrected content: {corrected_text}\n")
                f.write("-"*50+"\n")
            print(f" File is stored in '{OUTPUT_FILE}'!")

            #Prevent Key press overlaps
            time.sleep(1)

if __name__ == "__main__":
    main()

