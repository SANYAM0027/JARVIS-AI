# wakeword/porcupine.py

import time
import numpy as np
import sounddevice as sd
from voice.listen import listen

SAMPLE_RATE = 16000
BLOCK_SIZE = 1024

# CALIBRATION: Raised to 0.25 to completely ignore ambient noise / fan hums
AUDIO_SPIKE_LIMIT = 0.25  
TARGET_WAKEPADS = {"jarvis", "hey jarvis", "hello jarvis"}

class WakeWordEngine:
    def __init__(self):
        self.spike_tripped = False

    def _audio_stream_callback(self, indata, frames, time_info, status):
        if self.spike_tripped:
            return
        rms = np.sqrt(np.mean(indata**2))
        if rms > AUDIO_SPIKE_LIMIT:
            self.spike_tripped = True

    def listen_for_wake(self) -> bool:
        """Sits silently in the background waiting for a real vocal noise spike."""
        self.spike_tripped = False
        
        with sd.InputStream(callback=self._audio_stream_callback, channels=1, samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE):
            while not self.spike_tripped:
                time.sleep(0.1)

        # Audio threshold passed
        print("\n[WAKE CORE]: Noise threshold crossed. Syncing audio frame...")
        phrase = listen(duration=2)
        
        if phrase:
            # This line will show you exactly what words Google thinks you said!
            print(f"[WAKE CORE]: Recognized phrase -> '{phrase}'")
            if any(word in phrase.lower() for word in TARGET_WAKEPADS):
                return True
        else:
            print("[WAKE CORE]: Captured static or silence.")
        
        print("[WAKE CORE]: Wake verification failed. Re-arming standby matrix...")
        return False