"""
Акустическая оценка речи через Azure AI Speech — Pronunciation Assessment
в unscripted-режиме (reference_text="").

Даёт три метрики без привязки к эталонному тексту: Accuracy, Fluency, Prosody.
Content-метрики (Grammar/Vocabulary) Azure больше не считает нативно (фича
retired с SDK 1.46+) — их считает LLM поверх транскрипта, см. grading.py.
"""

from pathlib import Path

import azure.cognitiveservices.speech as speechsdk

from bot.config import settings
from bot.models import PronunciationScores


def _run_assessment_sync(wav_path: Path) -> PronunciationScores:
    speech_config = speechsdk.SpeechConfig(
        subscription=settings.azure_speech_key,
        region=settings.azure_speech_region,
    )
    speech_config.speech_recognition_language = "en-US"

    audio_config = speechsdk.audio.AudioConfig(filename=str(wav_path))

    # reference_text="" включает unscripted-режим — оценка идёт по тому,
    # что человек сказал сам, а не по сравнению с заданной фразой.
    pronunciation_config = speechsdk.PronunciationAssessmentConfig(
        reference_text="",
        grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
        granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
        enable_miscue=False,
    )
    pronunciation_config.enable_prosody_assessment()

    recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        audio_config=audio_config,
    )
    pronunciation_config.apply_to(recognizer)

    result = recognizer.recognize_once()

    if result.reason != speechsdk.ResultReason.RecognizedSpeech:
        raise RuntimeError(
            f"Azure Speech recognition failed: {result.reason}, "
            f"details: {getattr(result, 'no_match_details', None)}"
        )

    assessment = speechsdk.PronunciationAssessmentResult(result)

    return PronunciationScores(
        accuracy=round(assessment.accuracy_score),
        fluency=round(assessment.fluency_score),
        prosody=round(assessment.prosody_score or 0),
        transcript=result.text,
    )


async def assess_pronunciation(wav_path: Path) -> PronunciationScores:
    """Async-обёртка: Azure Speech SDK синхронный, уводим в threadpool."""
    import asyncio

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _run_assessment_sync, wav_path)
