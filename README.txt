================================================================================
WAKE CLAUDE - Voice Activated Browser Launcher
================================================================================

Say "wake up" into your microphone and Claude.ai opens automatically in your
browser. That's it!

--------------------------------------------------------------------------------
STEP 1 — Install Python
--------------------------------------------------------------------------------

1. Go to: https://www.python.org/downloads/
2. Click the big yellow "Download Python 3.x.x" button.
3. Run the installer.
4. IMPORTANT: On the first screen, check the box that says:
       "Add Python to PATH"
   If you miss this, Python won't work from the command line.
5. Click "Install Now" and let it finish.
6. Verify it worked — open Command Prompt (search "cmd" in Start menu) and type:
       python --version
   You should see something like:  Python 3.11.4
   If you get "'python' is not recognized..." — reinstall with "Add to PATH" checked.

--------------------------------------------------------------------------------
STEP 2 — Install Required Libraries
--------------------------------------------------------------------------------

Open Command Prompt and run:

    py -m pip install vosk pyaudio

>>> If pyaudio gives an error (common on Windows), use pipwin instead:

    py -m pip install pipwin
    pipwin install pyaudio

(winsound is built into Python on Windows — no install needed.)

--------------------------------------------------------------------------------
STEP 3 — Download the Vosk Speech Recognition Model
--------------------------------------------------------------------------------

The script needs a small AI model to understand speech. Here's how to get it:

1. Open this URL in your browser:
       https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip

2. The file is about 40 MB. Wait for it to download.

3. Unzip/extract the file.
   - Right-click the .zip file > "Extract All..." > Extract
   - You'll get a folder named:  vosk-model-small-en-us-0.15

4. Move that ENTIRE folder so it sits next to wake_claude.py.

   Your folder should look exactly like this:

       [your folder]/
           wake_claude.py          <-- the script
           README.txt              <-- this file
           vosk-model-small-en-us-0.15/   <-- the model folder
               am/
               conf/
               graph/
               ivector/
               ...

   The model folder name must be exactly:  vosk-model-small-en-us-0.15
   Do not rename it.

--------------------------------------------------------------------------------
STEP 4 — Run the Script
--------------------------------------------------------------------------------

1. Open Command Prompt.
2. Navigate to the folder where wake_claude.py is saved. For example:
       cd C:\Users\YourName\Downloads\wakeclaude
   (Replace the path with wherever you saved the files.)
3. Run the script:
       python wake_claude.py
4. You should see:
       Loading speech recognition model...
       Model loaded successfully.
       Microphone connected.
       Listening for 'wake up'...

--------------------------------------------------------------------------------
STEP 5 — Using the Script
--------------------------------------------------------------------------------

1. Make sure the script is running and shows "Listening for 'wake up'..."
2. Speak clearly into your microphone: "wake up"
3. You'll hear a beep and Claude.ai opens immediately in your browser!
4. There's a 5-second cooldown, then it goes back to listening.

To stop the script: press Ctrl+C in the Command Prompt window.

--------------------------------------------------------------------------------
TROUBLESHOOTING
--------------------------------------------------------------------------------

PROBLEM: "Mic not detected" or "Could not open microphone"
SOLUTION:
  - Make sure your microphone is plugged in and working.
  - Set it as the default recording device:
    Right-click the speaker icon in the taskbar > Sounds > Recording tab
    > right-click your mic > Set as Default Device.
  - Make sure no other app is exclusively using the mic (Discord, Teams, etc.).
  - Try unplugging and replugging the mic, then restart the script.

PROBLEM: Wake word not being recognized
SOLUTION:
  - Speak clearly and at a normal pace: "WAKE... UP"
  - Make sure the vosk model folder is in the same directory as the script
    and named exactly:  vosk-model-small-en-us-0.15
  - The script prints what it hears — watch the output to see if it's
    picking up your voice at all.
  - Try speaking a bit louder or closer to the mic.
  - Reduce background noise (TV, music, fans).


PROBLEM: PyAudio fails to install
SOLUTION:
  - Use the pipwin fallback method described in Step 2:
        pip install pipwin
        pipwin install pyaudio

PROBLEM: "No module named 'vosk'" or similar import error
SOLUTION:
  - Make sure you ran:  pip install vosk
  - If you have multiple Python versions installed, try:
        py -m pip install vosk pyaudio numpy
    then run the script with:
        py wake_claude.py

--------------------------------------------------------------------------------
ADJUSTING SETTINGS
--------------------------------------------------------------------------------

Open wake_claude.py in any text editor (Notepad works fine) and look for the
CONFIGURATION section near the top. You can change:

    COOLDOWN_SECONDS = 5      --> How long to pause after opening Claude

Save the file and re-run the script for changes to take effect.

--------------------------------------------------------------------------------
FILES IN THIS PACKAGE
--------------------------------------------------------------------------------

    wake_claude.py                  Main script — run this with Python
    README.txt                      This file
    vosk-model-small-en-us-0.15/   (You download this — see Step 3)

================================================================================
