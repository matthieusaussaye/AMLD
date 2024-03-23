import openai
import tempfile
import wave

OPENAI_API_KEY = "t"
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

class Config:
    channels = 2
    sample_width = 2
    sample_rate = 44100

def save_wav_file(file_path, wav_bytes):
    with wave.open(file_path, 'wb') as wav_file:
        wav_file.setnchannels(Config.channels)
        wav_file.setsampwidth(Config.sample_width)
        wav_file.setframerate(Config.sample_rate)
        wav_file.writeframes(wav_bytes)

def convert(path_to_speech):
    audio_file = open(path_to_speech, "rb")
    openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
    transcript = openai_client.audio.transcriptions.create(model="whisper-1",
                                                           file=audio_file)
    return transcript.text

def convert_openai(text, language_code="fr-FR"):
    response = openai_client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=text
        )

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        temp_file_path = temp_file.name
        response.stream_to_file(temp_file_path)

    return temp_file_path