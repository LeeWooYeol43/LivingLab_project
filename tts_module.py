# tts_module.py
import subprocess
from google.cloud import texttospeech

def synthesize_and_play(text_to_speak, client):
    try:
        ssml_text = f"<speak><prosody rate='90%'>{text_to_speak}</prosody></speak>"
        synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)
        
        voice = texttospeech.VoiceSelectionParams(
            language_code="ko-KR",
            name="ko-KR-Wavenet-D"
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            sample_rate_hertz=16000
        )
        
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        subprocess.run(
            ["mpg123", "-q", "-"],
            input=response.audio_content,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
    except Exception as e:
        print(f"TTS 오류: {e}")