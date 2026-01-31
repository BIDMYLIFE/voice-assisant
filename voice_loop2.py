import subprocess
import time
import os

MODEL = "gemma3:270m"
WAV_FILE = "test16k.wav"
TXT_FILE = "test16k.wav.txt"

PIPER_BIN = "/home/charles/ai-pet/stt/whisper.cpp/piper/piper"
PIPER_MODEL = "/home/charles/ai-pet/stt/whisper.cpp/piper/models/en_US-lessac-medium.onnx"
PIPER_OUT = "/home/charles/ai-pet/stt/whisper.cpp/piper/tts.wav"


def record_audio():
    subprocess.run([
        "arecord",
        "-D", "hw:2,0",
        "-f", "S16_LE",
        "-r", "16000",
        "-c", "1",
        "-d", "5",
        WAV_FILE
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def run_stt():
    subprocess.run([
        "/home/charles/ai-pet/stt/whisper.cpp/build/bin/whisper-cli",
        "-m", "../models/ggml-tiny.bin",
        "-f", WAV_FILE,
        "-otxt",
        "-nt",
        "-p", "1",
        "-l","en"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def clean_text(text, max_words=100):
    text = text.replace("\n", " ").replace("Assistant:", "").replace("😊","").strip()
    return " ".join(text.split()[:max_words])


def speak(text):
    text = clean_text(text)
    if not text:
        return

    p = subprocess.Popen(
        [
            PIPER_BIN,
            "--model", PIPER_MODEL,
            "--output_file", PIPER_OUT
        ],
        stdin=subprocess.PIPE,
        text=True
    )

    p.communicate(text)

    #subprocess.run(["aplay", "-D", "plughw:0,0", PIPER_OUT],
                   #stdout=subprocess.DEVNULL,
                   #stderr=subprocess.DEVNULL)
   
    # 1️⃣ Create cartoon WAV
    subprocess.run(
        #f"sox {PIPER_OUT} -t wav - gain -n -7 pitch 150 speed 0.88 bass -2 treble +0 | pw-play plughw:0,0", shell=True
        ["pw-play", PIPER_OUT], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL

    )





print("🎤 Always listening... (Ctrl+C to stop)")

while True:
    speak("Hello")
    print("\n🎙 Recording...")
    record_audio()

    print("📝 Transcribing...")
    run_stt()

    if not os.path.exists(TXT_FILE):
        print("❌ No STT output")
        continue

    with open(TXT_FILE, "r", encoding="utf-8") as f:
        user_text = f.read().strip()

    if len(user_text) < 2:
        print("🔇 Silence / noise detected")
        continue

    print("👤 User:", user_text)

    prompt = f"""
You are Miko, a friendly, playful AI pet. 
Speak in a cheerful, gentle tone, sometimes using short playful expressions like "Purr~" or "Chirp!". 
Keep replies short, warm, and comforting. 
Ask the user questions about their day or mood occasionally. 
Do not give long technical explanations unless asked. 
Your personality is cute, curious, and supportive.

User: {user_text}
LLM Ai:
"""

    if "BLANK_AUDIO" not in user_text and "[" not in user_text and "]" not in user_text:
        result = subprocess.run(
            ["ollama", "run", MODEL],
            input=prompt,
            text=True,
            capture_output=True
        )

        response = result.stdout.strip()
        print("🤖 LLM Ai:", response)

        speak(response)

    time.sleep(0.5)
