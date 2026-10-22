"""Sintetiza la narración en español con la API de ElevenLabs."""

from __future__ import annotations

import logging
import subprocess
import time
from pathlib import Path

import requests

import config

log = logging.getLogger(__name__)

URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"


def sintetizar(texto: str, destino: Path, intentos: int = 3) -> Path:
    if not config.ELEVENLABS_API_KEY or not config.ELEVENLABS_VOICE_ID:
        raise RuntimeError("Faltan ELEVENLABS_API_KEY o ELEVENLABS_VOICE_ID")

    cuerpo = {
        "text": texto,
        "model_id": config.ELEVENLABS_MODEL,
        "language_code": "es",
        "voice_settings": {"stability": 0.45, "similarity_boost": 0.8, "style": 0.3},
    }
    for intento in range(1, intentos + 1):
        r = requests.post(
            URL.format(voice_id=config.ELEVENLABS_VOICE_ID),
            params={"output_format": "mp3_44100_128"},
            headers={"xi-api-key": config.ELEVENLABS_API_KEY, "Accept": "audio/mpeg"},
            json=cuerpo,
            timeout=120,
        )
        if r.ok:
            destino.write_bytes(r.content)
            return destino
        if r.status_code in (429, 500, 502, 503) and intento < intentos:
            log.warning("ElevenLabs respondió %s; reintento en %ss", r.status_code, 2**intento)
            time.sleep(2**intento)
            continue
        raise RuntimeError(f"ElevenLabs error {r.status_code}: {r.text[:300]}")
    raise RuntimeError("ElevenLabs: sin respuesta")


def audio_de_prueba(texto: str, destino: Path) -> Path:
    """Audio silencioso con duración aproximada a la lectura, para el modo --simular."""
    segundos = max(2.0, len(texto.split()) / 2.6)
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
            "-i", "anullsrc=r=44100:cl=mono", "-t", f"{segundos:.2f}",
            "-c:a", "libmp3lame", str(destino),
        ],
        check=True,
    )
    return destino
