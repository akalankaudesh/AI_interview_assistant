import sounddevice as sd
import numpy as np
import openai
import queue
import tkinter as tk
from tkinter import scrolledtext
from gtts import gTTS
import tempfile
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

q = queue.Queue()
recording = False
samplerate = 16000
duration = 5  # seconds per capture

def callback(indata, frames, time, status):
    if recording:
        q.put(indata.copy())

def record_audio():
    global recording
    recording = True
    text_box.insert(tk.END, "🎤 Listening...\n")
    text_box.see(tk.END)
    sd.InputStream(callback=callback, channels=1, samplerate=samplerate).start()
    root.after(int(duration * 1000), stop_recording)

def stop_recording():
    global recording
    recording = False
    text_box.insert(tk.END, "🧠 Processing...\n")
    text_box.see(tk.END)
    process_audio()

def process_audio():
    frames = []
    while not q.empty():
        frames.append(q.get())
    if not frames:
        text_box.insert(tk.END, "No audio captured.\n")
        return

    audio = np.concatenate(frames, axis=0).flatten()
    text_box.insert(tk.END, "Recognizing speech...\n")

    # Convert audio to text using OpenAI Whisper API
    import io
    import soundfile as sf
    buffer = io.BytesIO()
    sf.write(buffer, audio, samplerate, format='WAV')
    buffer.seek(0)

    try:
        transcript = openai.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",
            file=buffer
        )
        user_text = transcript.text
        text_box.insert(tk.END, f"🗣 You said: {user_text}\n")

        get_ai_response(user_text)

    except Exception as e:
        text_box.insert(tk.END, f"Error: {e}\n")

def get_ai_response(prompt):
    try:
        completion = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an AI interview assistant helping software engineers prepare for interviews."},
                {"role": "user", "content": prompt}
            ]
        )
        answer = completion.choices[0].message.content
        text_box.insert(tk.END, f"🤖 AI: {answer}\n")
        speak_text(answer)

    except Exception as e:
        text_box.insert(tk.END, f"Error generating AI response: {e}\n")

def speak_text(text):
    try:
        tts = gTTS(text)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tts.save(temp_file.name)
        os.system(f"start {temp_file.name}")
    except Exception as e:
        text_box.insert(tk.END, f"TTS Error: {e}\n")

# --- UI SETUP ---
root = tk.Tk()
root.title("AI Interview Assistant")

frame = tk.Frame(root)
frame.pack(pady=10)

start_btn = tk.Button(frame, text="🎙 Start Recording", command=record_audio, bg="lightgreen", width=20)
start_btn.grid(row=0, column=0, padx=10)

stop_btn = tk.Button(frame, text="⏹ Stop", command=stop_recording, bg="salmon", width=20)
stop_btn.grid(row=0, column=1, padx=10)

text_box = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=70, height=20)
text_box.pack(padx=10, pady=10)

root.mainloop()
