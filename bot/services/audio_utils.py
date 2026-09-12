import asyncio
import uuid
from pathlib import Path

TMP_DIR = Path("/tmp_audio")
TMP_DIR.mkdir(exist_ok=True)


async def ogg_to_wav(ogg_bytes: bytes) -> Path:
    """Конвертирует telegram voice (ogg/opus) в WAV 16kHz mono PCM.

    Azure Speech SDK и большинство STT/pronunciation-assessment API ожидают
    16kHz mono PCM WAV — Telegram присылает opus в ogg-контейнере, поэтому
    без ffmpeg тут не обойтись.
    """
    session_id = uuid.uuid4().hex
    ogg_path = TMP_DIR / f"{session_id}.ogg"
    wav_path = TMP_DIR / f"{session_id}.wav"

    ogg_path.write_bytes(ogg_bytes)

    proc = await asyncio.create_subprocess_exec(
        "ffmpeg",
        "-y",
        "-i", str(ogg_path),
        "-ar", "16000",
        "-ac", "1",
        "-sample_fmt", "s16",
        str(wav_path),
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    returncode = await proc.wait()

    ogg_path.unlink(missing_ok=True)

    if returncode != 0 or not wav_path.exists():
        raise RuntimeError("ffmpeg conversion failed — voice message could not be processed")

    return wav_path


def cleanup(path: Path) -> None:
    path.unlink(missing_ok=True)
