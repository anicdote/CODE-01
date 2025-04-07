import pyttsx3
import time
import os
from playsound import playsound

# Default 5 fake call messages
default_lines = [
    "Hey, I’m almost there. Just 5 minutes away.",
    "I’m right around the corner, hang tight.",
    "Almost reached. Stay where you are.",
    "I'm at the gate. Coming in.",
    "Just parked. Walking over now."
]

# Text-to-Speech function
def speak_text(text):
    engine = pyttsx3.init()
    engine.setProperty("rate", 160)
    engine.setProperty("volume", 1.0)
    voices = engine.getProperty("voices")
    if len(voices) > 1:
        engine.setProperty("voice", voices[1].id)
    else:
        engine.setProperty("voice", voices[0].id)
    engine.say(text)
    engine.runAndWait()

# Function to play the fake call
def play_fake_call():
    print("\n📞 FAKE CALL INCOMING...")

    # Step 1: Play ringtone
    print("🎶 Playing ringtone...")
    if os.path.exists("ringtone.mp3"):
        try:
            playsound("ringtone.mp3")
        except Exception as e:
            print("⚠️ Error playing ringtone:", e)
    else:
        print("❌ ringtone.mp3 not found!")

    # Step 2: Show options
    print("\n💬 Choose your fake call message:")
    for idx, line in enumerate(default_lines, 1):
        print(f"{idx}. {line}")
    print("6. Type a custom message")

    try:
        choice = int(input("Enter option (1-6): "))
    except ValueError:
        print("❌ Please enter a number. Using default option 1.")
        choice = 1

    if 1 <= choice <= 5:
        final_line = default_lines[choice - 1]
    elif choice == 6:
        final_line = input("Enter your custom fake call message: ")
    else:
        print("❌ Invalid choice. Using default option 1.")
        final_line = default_lines[0]

    # Step 3: Speak message
    time.sleep(2)
    print(f"\n🔊 Fake Caller says: “{final_line}”")
    speak_text(final_line)

# ✅ This part must be present to start the program
if __name__ == "__main__":
    while True:
        play_fake_call()
        again = input("\n🔁 Do you want to simulate another fake call? (y/n): ").lower()
        if again != 'y':
            print("👋 Exiting fake call simulator.")
            break