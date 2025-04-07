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
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import json
from collections import Counter
import speech_recognition as sr
from datetime import datetime
import cohere
from twilio.rest import Client as TwilioClient
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template_string
import threading
import webbrowser
import geocoder

# === CONFIGURATION ===
REGISTERED_EMBEDDING = "registered_embed.npy"
REGISTERED_AUDIO = "registered_audio.wav"
LIVE_AUDIO = "live_audio.wav"
AMBIENT_AUDIO = "ambient_audio.wav"
DISTRESS_REPORT = "distress_report.txt"
SAMPLE_RATE = 16000
RECORD_SECONDS = 10
AMBIENT_RECORD_SECONDS = 20
THRESHOLD = 0.75
DISTRESS_KEYWORDS = [
    "help", "fire", "emergency", "danger", "call police",
    "i need help", "please help", "i'm in trouble", "save me", "help me",
    "save me", "they're following me"
]
EMAIL_ADDRESS = "ani.cs052@gmail.com"
EMAIL_PASSWORD = "bhgq tmik edyq rzst"
TO_EMAIL = "preetamumesh06@gmail.com"

# Cohere and Twilio Config
load_dotenv()
COHERE_API_KEY = os.getenv("COHERE_API_KEY") or "aweyjAvLINmpLsY0AYKe4ibnWY5P5DiGJgg3A9A3"
co = cohere.Client(COHERE_API_KEY)
TWILIO_SID = os.getenv("TWILIO_SID") or "AC6515508846e35b104184a020ff00e2d3"
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN") or "c2228dd11548aded4ad6c129ef1096bb"
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER") or "+16198808861"
TO_NUMBER = os.getenv("TO_NUMBER") or "+919353683861"

# === INIT MODELS ===
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
torch.set_num_threads(1)

print("\U0001F680 Loading models...")
vad_model, utils = torch.hub.load(repo_or_dir="snakers4/silero-vad", model="silero_vad", force_reload=False)
(get_speech_timestamps, _, read_audio, _, _) = utils
encoder = VoiceEncoder()
whisper_model = whisper.load_model("base")

# === FLASK LOCATION SERVER ===
location_data = {"lat": None, "lon": None}
app = Flask(__name__)
html_page = '''
<!DOCTYPE html>
<html><head><title>Geolocation</title></head>
<body><h2>Allow Location Access</h2>
<script>
navigator.geolocation.getCurrentPosition(function(position) {
    fetch("/send_location", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({lat: position.coords.latitude, lon: position.coords.longitude})
    }).then(() => document.body.innerHTML = "<h3>✅ Location Sent. You may now close this tab.</h3>");
});
</script>
</body></html>
'''

@app.route('/')
def index():
    return render_template_string(html_page)

@app.route('/send_location', methods=['POST'])
def get_location():
    data = request.json
    location_data["lat"] = data.get("lat")
    location_data["lon"] = data.get("lon")
    return jsonify(status="success")

def start_location_server():
    threading.Thread(target=app.run, kwargs={"port": 5001, "debug": False}).start()

# === UTILITY FUNCTIONS ===
def get_location_details():
    try:
        start_location_server()
        webbrowser.open("http://localhost:5001")
        import time
        for _ in range(15):
            if location_data["lat"] and location_data["lon"]:
                lat = location_data["lat"]
                lon = location_data["lon"]
                maps_url = f"https://www.google.com/maps?q={lat},{lon}"
                return lat, lon, "Detected via Browser", "Detected via Browser", maps_url
            time.sleep(1)
        g = geocoder.ip('me')
        if g.ok and g.latlng:
            lat, lon = g.latlng
            return lat, lon, g.country or "Unknown", g.state or "Unknown", f"https://www.google.com/maps?q={lat},{lon}"
    except:
        pass
    return None, None, "Unknown", "Unknown", "Location unavailable."

def summarize_text(text, max_sentences=3):
    sentences = re.split(r'[.!?]', text)
    word_freq = Counter(re.findall(r'\w+', text.lower()))
    scored_sentences = [(sum(word_freq[word] for word in re.findall(r'\w+', sentence.lower())), sentence.strip()) for sentence in sentences if sentence.strip()]
    top_sentences = [s for _, s in sorted(scored_sentences, reverse=True)[:max_sentences]]
    return ' '.join(top_sentences)

def send_email_alert():
    subject = "\U0001F6A8 Distress Signal Detected"
    lat, lon, country, state, location_url = get_location_details()
    body = (
        "\U0001F6A8 Alert: A distress signal was detected from the registered user.\n\n"
        f"\U0001F30D Country: {country}\n"
        f"\U0001F3D9️ State: {state}\n"
        f"\U0001F4CD Latitude: {lat}\n"
        f"\U0001F4CD Longitude: {lon}\n"
        f"\U0001F5FA️ Google Maps Link: {location_url}\n\n"
        "Immediate attention may be required.\n"
        "An ambient audio recording and verbal distress report are attached."
    )
    msg = MIMEMultipart()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = TO_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    for attachment in [AMBIENT_AUDIO, DISTRESS_REPORT]:
        if os.path.exists(attachment):
            with open(attachment, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f"attachment; filename={attachment}")
                msg.attach(part)
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("📧 Email alert sent successfully.")
    except Exception as e:
        print("❌ Failed to send email:", e)

def generate_emergency_message():
    current_time = datetime.now().strftime("%I:%M %p")
    lat, lon, _, _, location_link = get_location_details()
    prompt = (
        f"Create a short emergency voice message from someone in danger. "
        f"Name is John, time is {current_time}, and location is shared in the link: {location_link}. "
        f"Make it sound human, natural, and urgent."
    )
    response = co.generate(model="command", prompt=prompt, max_tokens=100, temperature=0.8)
    return response.generations[0].text.strip()

def make_emergency_call(message):
    twilio_client = TwilioClient(TWILIO_SID, TWILIO_AUTH_TOKEN)
    call = twilio_client.calls.create(
        to=TO_NUMBER,
        from_=TWILIO_NUMBER,
        twiml=f'<Response><Say voice="alice">{message}</Say></Response>'
    )
    print(f"📞 Emergency call triggered. Call SID: {call.sid}")

def record_audio(filename, duration=RECORD_SECONDS):
    print(f"\n🎤 Recording for {duration} seconds...")
    audio = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='float32')
    sd.wait()
    sf.write(filename, audio, SAMPLE_RATE, format='WAV', subtype='PCM_16')
    print(f"✅ Audio saved: {filename}")

def record_distress_details():
    print("\n🎙️ Please describe your emergency situation (15 seconds)...")
    record_audio("detailed_report.wav", duration=15)
    try:
        audio, sr = librosa.load("detailed_report.wav", sr=16000, mono=True)
        audio_tensor = torch.from_numpy(audio).float()
        result = whisper_model.transcribe(audio_tensor.numpy(), language='en', fp16=False)
        transcript = result.get("text", "").strip()
        if not transcript:
            return None, None
        summary = summarize_text(transcript)
        with open(DISTRESS_REPORT, "w", encoding='utf-8') as f:
            f.write("Full Transcript:\n" + transcript + "\n\nSummary:\n" + summary)
        return transcript, summary
    except Exception as e:
        print("❌ Failed to transcribe or summarize:", e)
        return None, None

def listen_and_detect():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎙 Listening for distress keywords... Speak now.")
        audio = r.listen(source)
        try:
            text = r.recognize_google(audio).lower()
            print("🗣 You said:", text)
            if any(keyword in text for keyword in DISTRESS_KEYWORDS):
                print("🚨 Distress detected!")
                record_audio(AMBIENT_AUDIO, duration=AMBIENT_RECORD_SECONDS)
                transcript, summary = record_distress_details()
                send_email_alert()
                message = generate_emergency_message()
                make_emergency_call(message)
                for f in [AMBIENT_AUDIO, DISTRESS_REPORT]:
                    if os.path.exists(f): os.remove(f)
            else:
                print("✅ No distress signal detected.")
        except sr.UnknownValueError:
            print("❌ Could not understand audio.")
        except sr.RequestError as e:
            print("⚠ Speech recognition error:", e)

def simulate_power_button_press():
    press_count = 0
    print("🖲 Simulating Power Button... Press Enter to simulate each press.")
    while True:
        input("Press Enter (power button)...")
        press_count += 1
        print(f"Power button pressed {press_count} time(s)")
        if press_count == 3:
            print("🎯 Triple press detected! Activating voice detection...")
            listen_and_detect()
            break

# === MAIN ===
if __name__ == "__main__":
    simulate_power_button_press()




