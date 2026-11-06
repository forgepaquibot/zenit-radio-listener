
import os
import subprocess
import time
import NotificationManager
import speech_recognition as sr
from dotenv import load_dotenv

load_dotenv()

stream_url = os.getenv("STREAM_URL")
keyword = os.getenv("KEYWORD", "")
chunk_duration = int(os.getenv("CHUNK_DURATION_SECONDS", "10"))
recognition_language = os.getenv("RECOGNITION_LANGUAGE", "en-CA")

SAMPLE_RATE = 16000
SAMPLE_WIDTH = 2

def read_exact(pipe, size):
    """Read the requested number of bytes from the audio stream."""

    data = bytearray()
    while len(data) < size:
        chunk = pipe.read(size - len(data))
        if not chunk:
            break

        data.extend(chunk)

    return bytes(data)

def listen_and_transcribe():

    if not stream_url:
        raise ValueError("STREAM_URL is missing from your .env file.")

    if chunk_duration <= 0:
        raise ValueError("CHUNK_DURATION_SECONDS must be greater than zero.")

    recognizer = sr.Recognizer()

    ffmpeg_cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "error",

        # HLS / HTTP reconnection options
        "-reconnect", "1",
        "-reconnect_streamed", "1",
        "-reconnect_delay_max", "5",

        # Radio stream
        "-i", stream_url,

        # Audio conversion
        "-vn",
        "-f", "s16le",
        "-acodec", "pcm_s16le",
        "-ac", "1",
        "-ar", "16000",

        "pipe:1"
    ]

    print("Opening radio stream...")

    process = subprocess.Popen(
        ffmpeg_cmd,
        stdout=subprocess.PIPE
    )

    chunk_byte_size = SAMPLE_RATE * SAMPLE_WIDTH * chunk_duration

    try:
        while True:
            raw_audio_data = read_exact(
                process.stdout,
                chunk_byte_size
            )

            if not raw_audio_data:
                print("Lost stream connection!")
                break

            # Ensure the audio contains complete samples.
            raw_audio_data = raw_audio_data[:len(raw_audio_data) -
                                            (len(raw_audio_data) % SAMPLE_WIDTH)]

            if not raw_audio_data:
                continue

            timestamp = time.strftime("%H:%M:%S")
            try:
                # Convert raw PCM audio into SpeechRecognition audio.
                audio_content = sr.AudioData(
                    raw_audio_data,
                    SAMPLE_RATE,
                    SAMPLE_WIDTH
                )

                # Transcribe audio using Google Speech Recognition.
                text = recognizer.recognize_google(
                    audio_content,
                    language=recognition_language
                )

                print(f"[{timestamp}] {text}")

                # Check whether the specified keyword was mentioned.
                if keyword and keyword.casefold() in text.casefold():
                    print("Found keyword! Writing to file...")

                    with open("codes.txt", "a", encoding="utf-8") as file:
                        file.write(f"[{timestamp}] {text}\n")

                    NotificationManager.sendEmail(f"[{timestamp}] {text}") # Send email notification with code
            except sr.UnknownValueError:
                print(
                    f"[{timestamp}] Could not understand audio "
                    "(possibly music, silence, or unclear speech)."
                )
            except sr.RequestError as e:
                print(f"[{timestamp}] Google API connectivity error: {e}")
                time.sleep(3)
    except KeyboardInterrupt:
        print("\nStopping Zenit Radio Listener")
    finally:
        if process.stdout:
            process.stdout.close()
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

if __name__ == "__main__":
    listen_and_transcribe()