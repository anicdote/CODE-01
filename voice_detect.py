import os
import numpy as np
import torch
import sounddevice as sd
import soundfile as sf
from resemblyzer import VoiceEncoder, preprocess_wav
from scipy.spatial.distance import cosine
import whisper
import librosa
import difflib
import re
import requests

# === CONFIGURATION ===
REGISTERED_EMBEDDING = "registered_embed.npy"
REGISTERED_AUDIO = "registered_audio.wav"
LIVE_AUDIO = "live_audio.wav"
SAMPLE_RATE = 16000
RECORD_SECONDS = 6
THRESHOLD = 0.75
DISTRESS_KEYWORDS = [
    "help", "fire", "emergency", "danger", "call police",
    "i need help", "please help", "i'm in trouble", "save me", "help me"
]

# === SMS ALERT CONFIG ===
TRUSTED_PHONE_NUMBER = "+1234567890"  # Replace with your trusted number
TEXTBELT_API_KEY = "textbelt"  # Use 'textbelt' for free-tier testing

# === INIT MODELS ===
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
torch.set_num_threads(1)

print("🚀 Loading models...")
vad_model, utils = torch.hub.load(repo_or_dir="snakers4/silero-vad", model="silero_vad", force_reload=False)
(get_speech_timestamps, _, read_audio, _, _) = utils
encoder = VoiceEncoder()
whisper_model = whisper.load_model("base")  # You can switch to "medium" for better accuracy

# === FUNCTIONS ===

def send_sms_alert():
    message = "🚨 Distress signal detected from registered user. Immediate action may be needed!"
    try:
        response = requests.post('https://textbelt.com/text', {
            'phone': TRUSTED_PHONE_NUMBER,
            'message': message,
            'key': TEXTBELT_API_KEY,
        })
        result = response.json()
        if result.get("success"):
            print("📱 SMS alert sent successfully.")
        else:
            print("❌ Failed to send SMS:", result)
    except Exception as e:
        print("❌ Error sending SMS:", e)

def record_audio(filename, duration=RECORD_SECONDS):
    print(f"\n🎤 Recording for {duration} seconds...")
    audio = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='float32')
    sd.wait()
    sf.write(filename, audio, SAMPLE_RATE, format='WAV', subtype='PCM_16')
    print(f"✅ Audio saved: {filename}")

def apply_vad(input_path, output_path):
    print("🧹 Applying VAD (voice activity detection)...")
    wav = read_audio(input_path, sampling_rate=SAMPLE_RATE)
    timestamps = get_speech_timestamps(wav, vad_model, sampling_rate=SAMPLE_RATE)
    if not timestamps:
        print("❌ No speech detected.")
        return False
    voiced = torch.cat([wav[t['start']:t['end']] for t in timestamps])
    sf.write(output_path, voiced.numpy(), SAMPLE_RATE, format='WAV', subtype='PCM_16')
    return True

def register_user():
    print("🔐 Registering user voice...")
    record_audio(REGISTERED_AUDIO)
    if not apply_vad(REGISTERED_AUDIO, REGISTERED_AUDIO):
        print("❌ Registration failed. No voice detected.")
        return
    wav = preprocess_wav(REGISTERED_AUDIO)
    embed = encoder.embed_utterance(wav)
    np.save(REGISTERED_EMBEDDING, embed)
    print("✅ Voice registered successfully.")

def is_registered_speaker(live_path):
    try:
        live_wav = preprocess_wav(live_path)
        live_embed = encoder.embed_utterance(live_wav)
        reg_embed = np.load(REGISTERED_EMBEDDING)
        similarity = 1 - cosine(reg_embed, live_embed)
        print(f"🧠 Voice similarity score: {similarity:.3f}")
        return similarity > THRESHOLD
    except Exception as e:
        print("❌ Speaker verification failed:", e)
        return False

def clean_transcript(text):
    text = re.sub(r'[^\w\s]', '', text.lower())
    return text.split()

def detect_distress(audio_path):
    print("🗣️ Transcribing with Whisper (no FFmpeg)...")
    try:
        audio, sr = librosa.load(audio_path, sr=16000, mono=True)
        if len(audio) < sr:
            print("❌ Audio too short to transcribe.")
            return False

        audio_tensor = torch.from_numpy(audio).float()
        result = whisper_model.transcribe(audio_tensor.numpy(), language='en', fp16=False)
        transcript = result.get("text", "")
        print("📄 Transcript:", transcript)

        words = clean_transcript(transcript)
        strong_matches = 0
        partial_matches = 0

        for keyword in DISTRESS_KEYWORDS:
            kw_words = keyword.split()
            match_found = all(
                difflib.get_close_matches(word, words, n=1, cutoff=0.8) for word in kw_words
            )
            if match_found:
                strong_matches += 1
            elif any(difflib.get_close_matches(word, words, n=1, cutoff=0.7) for word in kw_words):
                partial_matches += 1

        print(f"🔍 Matches — Strong: {strong_matches}, Partial: {partial_matches}")

        if strong_matches >= 1 or (strong_matches == 0 and partial_matches >= 2):
            print("⚠️ Distress keyword detected.")
            return True

        print("✅ No distress keyword found.")
        return False
    except Exception as e:
        print("❌ Whisper transcription failed:", e)
        return False

# === MAIN FLOW ===

if __name__ == "__main__":
    if not os.path.exists(REGISTERED_EMBEDDING):
        print("📝 No voice registered. Starting registration...")
        register_user()
        exit()

    print("\n🎧 Listening for possible distress call from registered user...")
    record_audio(LIVE_AUDIO)
    if not apply_vad(LIVE_AUDIO, LIVE_AUDIO):
        exit()

    if is_registered_speaker(LIVE_AUDIO):
        print("✅ Voice matched with registered user.")
        if detect_distress(LIVE_AUDIO):
            print("⚠️ EMERGENCY DETECTED! Take immediate action!")
            send_sms_alert()
        else:
            print("✅ Speech detected but no distress signal.")
    else:
        print("❌ Speaker not recognized — skipping analysis.")

    if os.path.exists(LIVE_AUDIO):
        os.remove(LIVE_AUDIO)











