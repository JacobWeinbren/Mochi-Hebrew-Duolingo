import csv
import os
import time
from google.cloud import texttospeech
from google.api_core.exceptions import RetryError

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service_account.json"


def generate_audio_with_retry(text, filename, max_retries=5):
    if os.path.exists(filename):
        print(f"Audio file already exists for: {text}")
        return

    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="he-IL", name="he-IL-Wavenet-A"
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    for attempt in range(max_retries):
        try:
            response = client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )

            with open(filename, "wb") as out:
                out.write(response.audio_content)

            print(f"Generated audio for: {text}")
            return
        except RetryError:
            wait_time = 2**attempt
            print(f"Rate limit hit, retrying in {wait_time} seconds...")
            time.sleep(wait_time)

    print(f"Failed to generate audio for {text} after {max_retries} attempts")


def process_csv():
    os.makedirs("audio", exist_ok=True)
    with open(
        "Duolingo Hebrew Vocab COMPLETE - Words.csv", "r", encoding="utf-8"
    ) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            hebrew_word = row["Niqqud"]
            filename = f"audio/{hebrew_word}.mp3"
            generate_audio_with_retry(hebrew_word, filename)


if __name__ == "__main__":
    process_csv()
