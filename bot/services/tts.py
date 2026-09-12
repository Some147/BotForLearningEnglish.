"""Синтез voice-вопросов бота через Azure TTS (тот же вендор, что и STT —
единый биллинг и нет лишней интеграции с третьим провайдером)."""

import asyncio
import uuid
from pathlib import Path

import azure.cognitiveservices.speech as speechsdk

from bot.config import settings

TMP_DIR = Path("/tmp_audio")
TMP_DIR.mkdir(exist_ok=True)

# Голос: en-US-AvaMultilingualNeural — естественный, поддерживает
# конверсационный стиль. Список актуальных голосов см. в Azure Speech Studio.
VOICE_NAME = "en-US-AvaMultilingualNeural"


def _synthesize_sync(text: str) -> Path:
    out_path = TMP_DIR / f"{uuid.uuid4().hex}.ogg"

    speech_config = speechsdk.SpeechConfig(
        subscription=settings.azure_speech_key,
        region=settings.azure_speech_region,
    )
    speech_config.speech_synthesis_voice_name = VOICE_NAME
    # OGG/OPUS 16kHz — формат, который Telegram принимает как voice-note
    # без дополнительной перекодировки на нашей стороне.
    speech_config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Ogg16Khz16BitMonoOpus
    )

    audio_config = speechsdk.audio.AudioOutputConfig(filename=str(out_path))
    synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config, audio_config=audio_config
    )

    result = synthesizer.speak_text(text)

    if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        raise RuntimeError(f"TTS synthesis failed: {result.reason}")

    return out_path


async def synthesize_voice(text: str) -> Path:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _synthesize_sync, text)
