# config/api_keys.py

import os
from dotenv import load_dotenv

# Load the .env file once globally
load_dotenv()

# Centralized System Configurations
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
JARVIS_MODEL = os.getenv("JARVIS_MODEL", "qwen/qwen-2.5-7b-instruct:free")

# Audio/Voice Settings (Makes it easy to tweak system-wide defaults)
SAMPLE_RATE = 16000
PAUSE_THRESHOLD = 0.8

# Verification Layer
if not OPENROUTER_API_KEY:
    print("[WARNING]: OPENROUTER_API_KEY is missing from your .env file!")