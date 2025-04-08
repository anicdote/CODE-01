# CODE-01
Problem Statement: AI for Women’s Safety
Voice-Based Distress Detection System

This project is an AI-powered voice-activated emergency alert system built to help individuals in danger by automating safety responses. The system is triggered when the user presses the Enter key three times—this simulates a triple power button press on a phone, acting as a confirmation mechanism to avoid accidental triggers and ensure double verification.

Once activated, the system listens for specific distress keywords like “help”, “save me”, or “emergency”. On detecting such keywords, it:

🎤 Records ambient audio for 20 seconds to capture the environment.

🧠 Uses OpenAI's Whisper to transcribe the user's spoken emergency message.

✂ Summarizes the transcription using an AI-based summarizer.

📧 Sends an email alert (sms alert preferred but email is used due to paid versions constraint) to a trusted contact with:

Full transcript & summary

Live location (via Geocoder)

Audio recordings as attachments

🗣 Uses Cohere AI to generate a realistic, urgent voice message.

📞 Makes an automated phone call using Twilio to deliver the message to the trusted person for faster response to emergency.

The system also includes speaker verification via Resemblyzer to ensure the registered user is speaking. Built completely in Python and testable from VS Code, this project is a powerful prototype for voice-based emergency response tech.

AI & ML Tools Used in the Distress Detection System

🔊 Whisper by OpenAI

Purpose: Speech-to-text transcription of recorded audio (distress messages).

Usage: whisper.transcribe()

🧠 Torch (PyTorch)

Purpose: ML framework used for loading and running models (Silero VAD).

Usage: torch.hub.load(), torch.set_num_threads()

🗣 Resemblyzer (VoiceEncoder)

Purpose: Speaker verification via voice embeddings.

Usage: encoder.embed_utterance()

🎧 Silero VAD (Voice Activity Detection)

Source: torch.hub from snakers4/silero-vad

Purpose: Detects when someone is speaking to isolate voice segments.

📚 Cohere (cohere.Client)

Purpose: AI-powered text generation for emergency voice message.

Usage: co.generate()

📞 Twilio

Purpose: Triggers automated emergency phone calls using generated message.

Usage: twilio_client.calls.create()

🧠 SpeechRecognition + Google Speech API

Purpose: Live keyword detection using microphone input.

Usage: r.recognize_google()

🗺 Geocoder

Purpose: Gets user’s live location using IP-based geolocation.

Usage: geocoder.ip('me')

📊 Text Summarization (Custom using Counter)

Purpose: Extracts summary from transcribed text using word frequency analysis.
