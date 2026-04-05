"""
================================================================================
WAKE CLAUDE - Voice + Clap Activated Browser Launcher
================================================================================

HOW TO SET UP AND RUN THIS SCRIPT
==================================

STEP 1 — Install Python
------------------------
1. Go to https://www.python.org/downloads/
2. Download the latest Python 3.x installer for Windows.
3. Run the installer. IMPORTANT: Check the box that says "Add Python to PATH"
   before clicking Install Now. If you missed this, uninstall and reinstall.
4. Open a Command Prompt (search "cmd" in the Start menu) and type:
       python --version
   You should see something like "Python 3.11.4". If you get an error,
   Python was not added to PATH — reinstall with that box checked.

STEP 2 — Install Required Libraries
-------------------------------------
Open Command Prompt and run these commands one at a time:

    pip install vosk
    pip install numpy

For PyAudio on Windows, try this first:
    pip install pyaudio

If that fails with a build error, use pipwin as a fallback:
    pip install pipwin
    pipwin install pyaudio

STEP 3 — Download the Vosk Speech Recognition Model
------------------------------------------------------
1. Go to this URL in your browser:
       https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
2. Download and unzip the file.
3. You should get a folder named:  vosk-model-small-en-us-0.15
4. Place that ENTIRE folder in the SAME folder as this script (wake_claude.py).

   Your folder should look like this:
       wake_claude.py
       vosk-model-small-en-us-0.15/
           am/
           conf/
           graph/
           ...

STEP 4 — Run the Script
------------------------
In Command Prompt, navigate to the folder containing this script:
    cd C:\path\to\your\folder

Then run:
    python wake_claude.py

STEP 5 — Use It
----------------
1. The script will print "Listening for 'wake up'..."
2. Say "wake up" clearly into your microphone.
3. You'll hear a beep — then clap your hands once within 5 seconds.
4. Claude.ai will open in your default browser!
5. There's a 5-second cooldown before it listens again.

To stop the script: press Ctrl+C in the Command Prompt window.

TROUBLESHOOTING
----------------
- "Mic not detected" or audio errors:
    Make sure your microphone is plugged in and set as the default input
    device in Windows Sound Settings (right-click speaker icon > Sounds >
    Recording tab). Try unplugging and replugging the mic, then restart.

- "Wake word not recognizing":
    Speak slowly and clearly: "WAKE UP". Make sure the vosk model folder
    is in the same directory as the script and named exactly:
        vosk-model-small-en-us-0.15
    Also ensure no other app is hogging the microphone (Discord, Teams, etc.).

- "Clap not detected — try lowering CLAP_THRESHOLD":
    Find the line near the top of this file that says:
        CLAP_THRESHOLD = 3000
    Lower it (e.g. 1500 or 1000) if your claps aren't being detected.
    Raise it (e.g. 5000 or 8000) if background noise is triggering false claps.
    Clap sharply once, fairly close to the microphone, for best results.

- PyAudio install fails:
    Use the pipwin method described in Step 2 above.

================================================================================
"""

import os
import sys
import time
import json
import wave
import struct
import webbrowser

import numpy as np
import pyaudio
import winsound
from vosk import Model, KaldiRecognizer

# ==============================================================================
# CONFIGURATION — Adjust these values to tune sensitivity
# ==============================================================================

# How loud a sound must be to count as a clap.
# The audio amplitude is measured 0–32767. A clap is a short, sharp spike.
# Try LOWERING this value (e.g. 1500 or 1000) if claps aren't being detected.
# Try RAISING this value (e.g. 5000 or 8000) if background noise triggers it.
CLAP_THRESHOLD = 3000

# How many seconds to listen for a clap after the wake word is detected.
CLAP_LISTEN_SECONDS = 5

# How many seconds to wait after opening Claude before listening again.
COOLDOWN_SECONDS = 5

# How many seconds to wait before retrying if the microphone disconnects.
MIC_RETRY_SECONDS = 5

# The name of the vosk model folder (must be in the same directory as this script).
MODEL_FOLDER = "vosk-model-small-en-us-0.15"

# Audio settings — these match what Vosk and PyAudio expect.
SAMPLE_RATE = 16000   # 16 kHz — required by the small vosk model
CHUNK_SIZE = 4000     # Number of audio frames read per loop iteration
AUDIO_FORMAT = pyaudio.paInt16  # 16-bit signed integers

# ==============================================================================
# MODEL LOADING
# ==============================================================================

def load_vosk_model():
    """
    Load the Vosk speech recognition model from the folder next to this script.
    If the folder doesn't exist, print a helpful error and exit.
    """
    # Build the path to the model folder relative to this script's location.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(script_dir, MODEL_FOLDER)

    # Check if the folder exists before trying to load it.
    if not os.path.exists(model_path):
        print()
        print("=" * 60)
        print("ERROR: Vosk model folder not found!")
        print("=" * 60)
        print(f"Expected folder at: {model_path}")
        print()
        print("To fix this:")
        print("  1. Download the model zip from:")
        print("     https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip")
        print("  2. Unzip the file — you'll get a folder called:")
        print(f"     {MODEL_FOLDER}")
        print(f"  3. Move that folder to the same directory as this script:")
        print(f"     {script_dir}")
        print()
        sys.exit(1)

    print(f"Loading speech recognition model from: {model_path}")
    model = Model(model_path)
    print("Model loaded successfully.")
    return model


# ==============================================================================
# MICROPHONE HELPERS
# ==============================================================================

def open_microphone(audio_interface):
    """
    Open the default microphone input stream.
    Returns the stream object, or None if it fails.
    """
    try:
        stream = audio_interface.open(
            format=AUDIO_FORMAT,
            channels=1,           # Mono audio — one channel is enough for speech
            rate=SAMPLE_RATE,
            input=True,           # We are recording (input), not playing (output)
            frames_per_buffer=CHUNK_SIZE
        )
        return stream
    except OSError as e:
        print(f"  Could not open microphone: {e}")
        return None


def read_audio_chunk(stream):
    """
    Read one chunk of audio from the microphone stream.
    Returns the raw bytes, or None if the read fails.
    """
    try:
        data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
        return data
    except OSError as e:
        print(f"  Microphone read error: {e}")
        return None


# ==============================================================================
# WAKE WORD DETECTION
# ==============================================================================

def listen_for_wake_word(stream, recognizer):
    """
    Continuously read audio and run it through Vosk speech recognition.
    Returns True when the phrase "wake up" is detected in the transcript.
    Returns False if a microphone error occurs (so we can retry the mic).
    """
    while True:
        data = read_audio_chunk(stream)

        # If reading failed, signal the caller to reconnect the mic.
        if data is None:
            return False

        # Feed the audio chunk into the Vosk recognizer.
        # AcceptWaveform() returns True when it has a complete utterance ready.
        if recognizer.AcceptWaveform(data):
            # Parse the JSON result from Vosk.
            result = json.loads(recognizer.Result())
            text = result.get("text", "").lower()

            # Print what was heard so the user can see the recognizer is working.
            if text:
                print(f"  Heard: \"{text}\"")

            # Check if "wake up" appears anywhere in what was said.
            if "wake up" in text:
                return True

        else:
            # Partial result — the recognizer is still processing a phrase.
            # We can check partial results to print live feedback (optional).
            partial = json.loads(recognizer.PartialResult())
            partial_text = partial.get("partial", "").lower()

            # Only print partials that have content, to avoid spamming the console.
            if partial_text and partial_text != "the":
                # Uncomment the line below if you want to see live partial results:
                # print(f"  (partial): {partial_text}", end="\r")
                pass


# ==============================================================================
# CLAP DETECTION
# ==============================================================================

def listen_for_clap(stream):
    """
    Listen for a loud, short audio spike (clap) for up to CLAP_LISTEN_SECONDS.
    Returns True if a clap is detected, False if time runs out or mic fails.

    How it works:
      Audio is made up of numbers (amplitudes). Normal room noise is low.
      A clap produces a sudden, large spike in amplitude. We measure the
      maximum amplitude in each small chunk and compare it to CLAP_THRESHOLD.
    """
    print(f"  Listening for a clap for {CLAP_LISTEN_SECONDS} seconds...")
    deadline = time.time() + CLAP_LISTEN_SECONDS

    while time.time() < deadline:
        data = read_audio_chunk(stream)

        if data is None:
            # Mic error — tell caller to reconnect
            return None  # None signals a mic error, False signals timeout

        # Convert the raw bytes into a numpy array of 16-bit integers.
        # Each integer is one audio sample; negative values are fine (it's a wave).
        samples = np.frombuffer(data, dtype=np.int16)

        # Find the loudest sample in this chunk (absolute value = volume).
        peak_amplitude = int(np.max(np.abs(samples)))

        # Show a simple volume meter so the user can see it's working.
        bar_length = min(40, peak_amplitude // 400)
        bar = "#" * bar_length
        seconds_left = max(0, deadline - time.time())
        print(f"  Volume: [{bar:<40}] {peak_amplitude:5d}  ({seconds_left:.1f}s left)", end="\r")

        # If the peak is louder than our threshold, it's probably a clap!
        if peak_amplitude > CLAP_THRESHOLD:
            print()  # Move to next line after the volume meter
            return True

    print()  # Move to next line after the volume meter
    return False  # Timed out without detecting a clap


# ==============================================================================
# MAIN LOOP
# ==============================================================================

def main():
    """
    Main program loop:
      1. Load the speech model.
      2. Open the microphone.
      3. Listen for "wake up".
      4. Beep and listen for a clap.
      5. Open Claude.ai if both detected.
      6. Cooldown, then repeat.
    """

    print()
    print("=" * 60)
    print("  WAKE CLAUDE — Voice + Clap Activated Launcher")
    print("=" * 60)
    print()

    # Load the speech recognition model once at startup.
    model = load_vosk_model()

    # Create the PyAudio interface. This manages all audio I/O.
    audio_interface = pyaudio.PyAudio()

    print()
    print("Say 'wake up' then clap to open Claude.ai")
    print("Press Ctrl+C to stop.")
    print()

    try:
        # Outer loop: keeps the script running even if the mic disconnects.
        while True:

            # --- Open the microphone ---
            print("Connecting to microphone...")
            stream = open_microphone(audio_interface)

            if stream is None:
                # Mic failed to open — wait and retry.
                print(f"  Microphone not available. Retrying in {MIC_RETRY_SECONDS} seconds...")
                time.sleep(MIC_RETRY_SECONDS)
                continue  # Go back to the top of the outer loop

            print("Microphone connected.")
            print()

            # Create a fresh Vosk recognizer tied to our model and sample rate.
            recognizer = KaldiRecognizer(model, SAMPLE_RATE)

            # Inner loop: listen for wake word, then clap, then open Claude.
            while True:

                # --- Phase 1: Listen for "wake up" ---
                print("Listening for 'wake up'...")
                wake_detected = listen_for_wake_word(stream, recognizer)

                if not wake_detected:
                    # The microphone had an error — break inner loop to reconnect.
                    print("Microphone disconnected. Reconnecting...")
                    break  # Break to outer loop to reopen the mic

                # Wake word was detected!
                print()
                print("Wake word detected! Clap your hands now...")

                # Play a short beep to signal the user to clap.
                # Frequency: 800 Hz, Duration: 200 milliseconds
                try:
                    winsound.Beep(800, 200)
                except RuntimeError:
                    # winsound.Beep can fail on some systems — just skip it.
                    print("  (Could not play beep sound — continuing anyway)")

                # Reset the recognizer so partial results from the wake word
                # don't bleed into the next listening session.
                recognizer = KaldiRecognizer(model, SAMPLE_RATE)

                # --- Phase 2: Listen for a clap ---
                clap_result = listen_for_clap(stream)

                if clap_result is None:
                    # Mic error during clap detection — reconnect.
                    print("Microphone disconnected during clap detection. Reconnecting...")
                    break  # Break to outer loop

                if clap_result:
                    # Clap detected! Open Claude.ai.
                    print()
                    print("Clap detected! Opening Claude.ai...")
                    webbrowser.open("https://claude.ai")

                    # Cooldown: wait before listening again to prevent double-opens.
                    print(f"Cooldown... back to listening in {COOLDOWN_SECONDS} seconds.")
                    time.sleep(COOLDOWN_SECONDS)
                    print()

                else:
                    # No clap heard within the time limit.
                    print("No clap detected within the time limit. Resuming listening...")
                    print()

                # Reset the recognizer after each activation attempt.
                recognizer = KaldiRecognizer(model, SAMPLE_RATE)

            # Cleanly close the stream before trying to reopen it.
            try:
                stream.stop_stream()
                stream.close()
            except Exception:
                pass  # Ignore errors when closing a broken stream

            # Wait a moment before retrying so we don't spin too fast.
            print(f"Waiting {MIC_RETRY_SECONDS} seconds before reconnecting...")
            time.sleep(MIC_RETRY_SECONDS)

    except KeyboardInterrupt:
        # The user pressed Ctrl+C — exit cleanly.
        print()
        print("Stopped by user. Goodbye!")

    finally:
        # Always clean up the PyAudio interface when exiting.
        audio_interface.terminate()


# ==============================================================================
# ENTRY POINT
# ==============================================================================

# This is the standard Python way to run the main() function when the script
# is executed directly (as opposed to being imported as a module).
if __name__ == "__main__":
    main()
