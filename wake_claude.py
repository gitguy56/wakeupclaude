r"""
================================================================================
WAKE CLAUDE - Voice Activated Browser Launcher
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

    py -m pip install vosk pyaudio

If pyaudio fails on Windows, use pipwin as a fallback:
    py -m pip install pipwin
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
       vosk-model-small-en-us-0.15\
           am\
           conf\
           graph\
           ...

STEP 4 — Run the Script
------------------------
In Command Prompt, navigate to the folder containing this script:
    cd C:\Users\YourName\Desktop\wakeupclaude

Then run:
    py wake_claude.py

STEP 5 — Use It
----------------
1. The script will print "Listening for 'wake up'..."
2. Say "wake up" clearly into your microphone.
3. Claude.ai opens immediately in your default browser!
4. There's a 5-second cooldown before it listens again.

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

- PyAudio install fails:
    Use the pipwin method described in Step 2 above.
    Always install with:  py -m pip install  (not just pip install)

================================================================================
"""

import os
import sys
import time
import json
import subprocess

import pyaudio
import winsound
from vosk import Model, KaldiRecognizer

# ==============================================================================
# FIREFOX LAUNCHER
# ==============================================================================

# Common places Firefox gets installed on Windows.
# If yours is somewhere else, add the path to this list.
FIREFOX_PATHS = [
    r"C:\Program Files\Mozilla Firefox\firefox.exe",
    r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Mozilla Firefox\firefox.exe"),
    os.path.expandvars(r"%PROGRAMFILES%\Mozilla Firefox\firefox.exe"),
    os.path.expandvars(r"%PROGRAMFILES(X86)%\Mozilla Firefox\firefox.exe"),
]

def find_firefox():
    """
    Search common install locations for firefox.exe.
    Returns the full path if found, or None if Firefox isn't installed.
    """
    for path in FIREFOX_PATHS:
        if os.path.isfile(path):
            return path
    return None

def open_url(url):
    """
    Open the given URL in Firefox. Works whether Firefox is already open or not.
    If Firefox can't be found, falls back to the system default browser.
    """
    firefox = find_firefox()
    if firefox:
        # Launch Firefox with the URL directly. subprocess.Popen starts it in
        # the background so this script doesn't wait for the browser to close.
        subprocess.Popen([firefox, url])
    else:
        # Firefox not found — warn the user and use the default browser instead.
        print("  Warning: Firefox not found. Opening in default browser.")
        print("  If Firefox is installed in a non-standard location, add its")
        print("  path to the FIREFOX_PATHS list near the top of this script.")
        import webbrowser
        webbrowser.open(url)

# ==============================================================================
# CONFIGURATION
# ==============================================================================

# How many seconds to wait after opening Claude before listening again.
# Prevents it from opening multiple tabs if it catches the phrase twice.
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


# ==============================================================================
# MAIN LOOP
# ==============================================================================

def main():
    """
    Main program loop:
      1. Load the speech model.
      2. Open the microphone.
      3. Listen for "wake up".
      4. Open Claude.ai immediately.
      5. Cooldown, then repeat.
    """

    print()
    print("=" * 60)
    print("  WAKE CLAUDE — Voice Activated Launcher")
    print("=" * 60)
    print()

    # Load the speech recognition model once at startup.
    model = load_vosk_model()

    # Create the PyAudio interface. This manages all audio I/O.
    audio_interface = pyaudio.PyAudio()

    print()
    print("Say 'wake up' to open Claude.ai")
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

            # Inner loop: listen for wake word, then open Claude.
            while True:

                # --- Listen for "wake up" ---
                print("Listening for 'wake up'...")
                wake_detected = listen_for_wake_word(stream, recognizer)

                if not wake_detected:
                    # The microphone had an error — break inner loop to reconnect.
                    print("Microphone disconnected. Reconnecting...")
                    break  # Break to outer loop to reopen the mic

                # Wake word detected — open Claude.ai right away.
                print()
                print("Wake word detected! Opening Claude.ai...")

                # Play a short beep as audio confirmation.
                # Frequency: 800 Hz, Duration: 200 milliseconds
                try:
                    winsound.Beep(800, 200)
                except RuntimeError:
                    pass  # Some systems can't beep — just skip it

                open_url("https://claude.ai")

                # Cooldown: wait before listening again to prevent double-opens.
                print(f"Cooldown... back to listening in {COOLDOWN_SECONDS} seconds.")
                time.sleep(COOLDOWN_SECONDS)
                print()

                # Reset the recognizer so old audio doesn't bleed into next round.
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

if __name__ == "__main__":
    main()
