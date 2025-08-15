import os
import time
import json
import requests
import sounddevice as sd
from scipy.io.wavfile import write
import google.generativeai as genai
from google.api_core import exceptions

# -------------------------------
# Configuration and API Keys
# -------------------------------
ASSEMBLEAI_API_KEY = "be4c4760749a460093b792f543273909"
GEMINI_API_KEY = "AIzaSyDVqhEJLIUBTp8rs02pbgCyn_2RQFs8K0A"
ELEVENLABS_API_KEY = "sk_4e4f0baa756e33c4b15d58eda6501471bab3c87851c98701"

# AssemblyAI Configuration
ASSEMBLEAI_HEADERS = {"authorization": ASSEMBLEAI_API_KEY}
UPLOAD_ENDPOINT = "https://api.assemblyai.com/v2/upload"
TRANSCRIPT_ENDPOINT = "https://api.assemblyai.com/v2/transcript"

# ElevenLabs Configuration
ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Default voice ID (Rachel)
ELEVENLABS_TTS_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
ELEVENLABS_HEADERS = {
    "Accept": "audio/mpeg",
    "xi-api-key": ELEVENLABS_API_KEY,
    "Content-Type": "application/json"
}

# Gemini Configuration - FIXED
genai.configure(api_key=GEMINI_API_KEY)

# Store conversation context
conversation_context = []

# -------------------------------
# Audio Recording and Playback
# -------------------------------
def record_audio(duration, filename):
    """Records audio from the microphone for a given duration (in seconds)."""
    fs = 44100  # Sample rate
    print("Recording audio...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()  # Wait until recording is finished
    write(filename, fs, recording)
    print(f"Audio recording saved as {filename}")

def play_audio(filename):
    """Plays an audio file using sounddevice."""
    import soundfile as sf
    data, fs = sf.read(filename)
    print("Playing audio...")
    sd.play(data, fs)
    sd.wait()  # Wait until playback is finished
    print("Audio playback complete")

# -------------------------------
# 1. Speech-to-Text via AssemblyAI
# -------------------------------
def transcribe_audio(filename):
    """Uploads the audio file to AssemblyAI and returns the transcript text."""
    # Step 1: Upload the audio file
    print("Uploading audio for transcription...")
    with open(filename, "rb") as audio_file:
        try:
            upload_response = requests.post(
                UPLOAD_ENDPOINT, 
                headers=ASSEMBLEAI_HEADERS, 
                data=audio_file
            )
            upload_response.raise_for_status()  # Raise exception for HTTP errors
            audio_url = upload_response.json()["upload_url"]
            print("Upload successful")
        except Exception as e:
            print(f"Error during upload: {e}")
            return "Transcription failed due to upload error."

    # Step 2: Request a transcript
    try:
        transcript_request = {
            "audio_url": audio_url,
            "language_code": "en"  # You can change this for other languages
        }
        transcript_response = requests.post(
            TRANSCRIPT_ENDPOINT, 
            headers=ASSEMBLEAI_HEADERS, 
            json=transcript_request
        )
        transcript_response.raise_for_status()
        transcript_id = transcript_response.json()["id"]
    except Exception as e:
        print(f"Error initiating transcription: {e}")
        return "Transcription failed during initialization."

    # Step 3: Poll for transcription result
    polling_url = f"{TRANSCRIPT_ENDPOINT}/{transcript_id}"
    print("Transcribing... please wait")
    
    while True:
        try:
            polling_response = requests.get(polling_url, headers=ASSEMBLEAI_HEADERS)
            polling_response.raise_for_status()
            result = polling_response.json()
            status = result.get("status")
            
            if status == "completed":
                print("Transcription completed successfully.")
                return result.get("text", "")
            elif status == "error":
                print(f"Error during transcription: {result}")
                return "Transcription failed due to processing error."
            
            # If not completed or error, wait and continue polling
            print("Waiting for transcription to complete...")
            time.sleep(2)
        except Exception as e:
            print(f"Error during transcription polling: {e}")
            return "Transcription failed during processing."

# -------------------------------
# 2. Text Processing via Gemini API - FIXED IMPLEMENTATION
# -------------------------------
def process_with_gemini(transcription, is_first_interaction=False):
    """Process the transcription with Google's Gemini AI."""
    global conversation_context
    
    print("Processing with Gemini AI...")
    try:
        # Updated to use the correct model and API structure
        # First, get available models to verify what's accessible
        available_models = [m.name for m in genai.list_models()]
        print(f"Available Gemini models: {available_models}")
        
        # Find the appropriate model (the naming might differ)
        model_name = None
        for model in available_models:
            if 'gemini' in model.lower():
                model_name = model
                break
        
        if not model_name:
            print("No Gemini model found. Using a fallback response.")
            return "Thanks for sharing. Could you tell me more about your experience?"
        
        print(f"Using Gemini model: {model_name}")
        model = genai.GenerativeModel(model_name)
        
        if is_first_interaction:
            interview_system_prompt = """
            You are an AI interview assistant conducting a job interview. Be professional, 
            ask relevant follow-up questions, and build upon the candidate's responses.
            Keep your responses concise (2-3 sentences) and end with a question.
            """
            
            # Set up the initial chat
            chat = model.start_chat(history=[])
            response = chat.send_message(
                f"{interview_system_prompt}\n\nThe candidate said: {transcription}\n\nRespond and ask a follow-up question."
            )
            
            # Save context for future interactions
            conversation_context = chat.history
        else:
            # If we have existing context, use it
            if conversation_context:
                chat = model.start_chat(history=conversation_context)
                response = chat.send_message(f"The candidate said: {transcription}\n\nRespond and ask a follow-up question.")
                conversation_context = chat.history
            else:
                # Fallback if context was lost
                chat = model.start_chat(history=[])
                response = chat.send_message(
                    f"You are conducting a job interview. The candidate said: {transcription}\n\nRespond and ask a follow-up question."
                )
                conversation_context = chat.history
        
        print("Gemini processed successfully")
        return response.text
        
    except Exception as e:
        print(f"Error processing with Gemini: {e}")
        # Provide a fallback response that feels natural in an interview context
        fallback_responses = [
            "That's interesting. Tell me about a challenging project you've worked on recently.",
            "I appreciate your background. What motivates you in your career?",
            "Thank you for sharing. How do you approach problem-solving in a team environment?",
            "Good to know. What are your long-term career goals?",
            "Thanks for that information. Can you describe your ideal work environment?",
        ]
        import random
        return random.choice(fallback_responses)

# -------------------------------
# 3. Text-to-Speech via ElevenLabs
# -------------------------------
def text_to_speech(text, output_filename="response.mp3"):
    """Converts text to speech using ElevenLabs API."""
    print("Converting text to speech...")
    try:
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5,
                "style": 0.0,
                "use_speaker_boost": True
            }
        }
        
        response = requests.post(
            ELEVENLABS_TTS_URL,
            json=data,
            headers=ELEVENLABS_HEADERS
        )
        
        if response.status_code == 200:
            with open(output_filename, "wb") as f:
                f.write(response.content)
            print(f"Speech saved to {output_filename}")
            return output_filename
        else:
            print(f"Error from ElevenLabs API: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        print(f"Error with ElevenLabs TTS: {e}")
        return None

# -------------------------------
# Main Interview Bot Logic
# -------------------------------
def run_interview():
    print("\n=== AI Interview Bot ===\n")
    
    # Initial greeting
    greeting = "Hello, welcome to your interview. Please introduce yourself and tell me about your background."
    print("Interview Bot: " + greeting)
    
    # Convert greeting to speech and play it
    speech_file = text_to_speech(greeting)
    if speech_file:
        play_audio(speech_file)
    
    interview_count = 0
    max_interviews = 5  # Limit to 5 interactions
    
    while interview_count < max_interviews:
        # Record user's response
        audio_file = f"response_{interview_count}.wav"
        record_duration = 15  # seconds - can be adjusted
        record_audio(record_duration, audio_file)
        
        # Transcribe user's audio
        transcription = transcribe_audio(audio_file)
        print(f"\nYou said: {transcription}\n")
        
        # Process with Gemini
        is_first = (interview_count == 0)
        gemini_response = process_with_gemini(transcription, is_first)
        print("Interview Bot: " + gemini_response)
        
        # Convert to speech and play
        speech_file = text_to_speech(gemini_response)
        if speech_file:
            play_audio(speech_file)
        
        interview_count += 1
    
    # End of interview
    end_message = "Thank you for participating in this interview. We've completed our questions for today. We'll be in touch about next steps."
    print("\nInterview Bot: " + end_message)
    
    speech_file = text_to_speech(end_message)
    if speech_file:
        play_audio(speech_file)

if __name__ == "__main__":
    run_interview()