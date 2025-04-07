import tkinter as tk
import threading
import time
import os
import pygame
import pyttsx3
import speech_recognition as sr

# === FAKE CALL (LOW SUS) CONFIG ===
default_lines = [
    "Hey, I’m almost there. Just 5 minutes away.",
    "I’m right around the corner, hang tight.",
    "Almost reached. Stay where you are.",
    "I'm at the gate. Coming in.",
    "Just parked. Walking over now."
]

def speak_text(text):
    engine = pyttsx3.init()
    engine.setProperty("rate", 160)
    engine.setProperty("volume", 1.0)
    voices = engine.getProperty("voices")
    engine.setProperty("voice", voices[1].id if len(voices) > 1 else voices[0].id)
    engine.say(text)
    engine.runAndWait()

def play_ringtone_loop():
    ringtone_path = "ringtonee.mp3"
    if not os.path.exists(ringtone_path):
        print("❌ ringtonee.mp3 not found!")
        return

    pygame.mixer.init()
    pygame.mixer.music.load(ringtone_path)
    pygame.mixer.music.play(-1)

def run_fake_call():
    print("\n💬 Choose your fake call message:")
    for idx, line in enumerate(default_lines, 1):
        print(f"{idx}. {line}")
    print("6. Type a custom message")

    try:
        choice = int(input("Enter option (1-6): "))
    except ValueError:
        print("❌ Invalid input. Using default option 1.")
        choice = 1

    if 1 <= choice <= 5:
        final_line = default_lines[choice - 1]
    elif choice == 6:
        final_line = input("Enter your custom fake call message: ")
    else:
        print("❌ Invalid choice. Using default option 1.")
        final_line = default_lines[0]

    ringtone_thread = threading.Thread(target=play_ringtone_loop)
    ringtone_thread.start()

    while True:
        action = input("👉 Your action (r = receive, d = decline): ").strip().lower()
        if action in ['r', 'd']:
            pygame.mixer.music.stop()
            break

    if action == 'r':
        print(f"\n🔊 Fake Caller says: “{final_line}”")
        speak_text(final_line)
    elif action == 'd':
        print("📵 Call declined.")

# === VOICE AI (MID SUS) CONFIG ===
try:
    ai_engine = pyttsx3.init()
except RuntimeError as e:
    print(f"Error initializing TTS engine: {e}")
    ai_engine = None

def speak_ai(text):
    if ai_engine:
        ai_engine.say(text)
        ai_engine.runAndWait()
    else:
        print(f"(TTS not available) AI: {text}")

def get_audio():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.adjust_for_ambient_noise(source)
        audio = r.listen(source)

    try:
        print("Recognizing...")
        text = r.recognize_google(audio)
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        print("Could not understand audio")
        return ""
    except sr.RequestError as e:
        print(f"Could not request results; {e}")
        return ""

def get_ai_response(user_input):
    user_input_lower = user_input.lower()
    if "hello" in user_input_lower or "hi" in user_input_lower:
        return "Hey there! How can I help you?"
    elif "how are you" in user_input_lower:
        return "I'm doing well, thank you for asking."
    elif "fine" in user_input_lower or "good" in user_input_lower:
        return "That's great to hear!"
    elif "scared" in user_input_lower or "nervous" in user_input_lower:
        return "It's okay, I'm here. Just focus on your breathing."
    elif "see anyone" in user_input_lower or "around you" in user_input_lower:
        return "Can you describe what you see around you?"
    elif "walking" in user_input_lower or "going somewhere" in user_input_lower:
        return "Are you heading somewhere specific?"
    elif "bye" in user_input_lower or "exit" in user_input_lower:
        return "Okay, talk to you later!"
    else:
        return "Hmm, that's interesting. Tell me more."

def run_voice_chat():
    print("Initiating Fake Call with AI...")
    speak_ai("Hello? Is anyone there?")

    while True:
        user_utterance = get_audio()
        if user_utterance:
            ai_response = get_ai_response(user_utterance)
            print(f"AI: {ai_response}")
            speak_ai(ai_response)
            if "bye" in user_utterance.lower() or "exit" in user_utterance.lower():
                break
        else:
            print("No speech detected. Please try again.")

# === GUI ===
def start_gui():
    root = tk.Tk()
    root.title("Fake Call AI - Suspicion Selector")
    root.geometry("350x200")
    root.configure(bg="#f0f0f0")

    title = tk.Label(root, text="Select Suspicion Level", font=("Arial", 14, "bold"), bg="#f0f0f0")
    title.pack(pady=20)

    low_btn = tk.Button(root, text="🔘 Low Sus (Fake Call)", font=("Arial", 12),
                        command=lambda: threading.Thread(target=run_fake_call).start(), bg="#b2f2bb")
    low_btn.pack(pady=10, ipadx=10, ipady=5)

    mid_btn = tk.Button(root, text="🔘 Mid Sus (AI Voice Chat)", font=("Arial", 12),
                        command=lambda: threading.Thread(target=run_voice_chat).start(), bg="#ffe066")
    mid_btn.pack(pady=10, ipadx=10, ipady=5)

    root.mainloop()

# === ENTRY POINT ===
if __name__ == "__main__":
    start_gui()