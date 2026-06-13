# voice/listen.py

import speech_recognition as sr
import sounddevice as sd
import numpy as np
import logging

# Initialize the speech recognition engine
recognizer = sr.Recognizer()

# Tweak recognition parameters for snappier responses
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 0.8  # Seconds of silence before finalizing a phrase


def listen(duration: int = None) -> str:
    """
    Captures ambient audio from the default microphone using sounddevice 
    and transcribes it into text via SpeechRecognition.
    """
    print("\nListening...", end="", flush=True)
    
    # Fallback to a default duration if none is passed
    listen_duration = duration if duration else 5
    sample_rate = 16000  # Google's Speech API works perfectly at 16kHz
    
    try:
        # Record audio block into a NumPy array using sounddevice
        # This replaces the dependency on PyAudio entirely
        recording = sd.rec(
            int(listen_duration * sample_rate), 
            samplerate=sample_rate, 
            channels=1, 
            dtype="int16"
        )
        sd.wait()  # Wait until the recording finishes
        print("\rProcessing...", end="", flush=True)
        
        # Convert raw audio data into a format SpeechRecognition understands
        raw_bytes = recording.tobytes()
        audio_data = sr.AudioData(raw_bytes, sample_rate, 2)  # 2 bytes per sample for int16
        
        # Transcribe using Google's free cloud speech infrastructure
        text = recognizer.recognize_google(audio_data)
        return text
        
    except sr.UnknownValueError:
        # Sound was heard, but it couldn't be parsed into words
        return ""
        
    except sr.RequestError as e:
        logging.error(f"Speech recognition service connectivity drop: {e}")
        return ""
        
    except Exception as e:
        logging.error(f"Unexpected error in audio listening matrix: {e}")
        return ""
    finally:
        # Clear the processing line in the terminal smoothly
        print("\r", end="", flush=True)