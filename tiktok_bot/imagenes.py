"""Genera imágenes con la API de OpenAI (DALL-E / gpt-image)."""

from __future__ import annotations

import base64
import logging
import subprocess
from pathlib import Path

from openai import OpenAI, BadRequestError

import config

log = logging.getLogger(__name__)

ESTILO = (
    "Vertical 9:16 cinematic digital illustration, dramatic lighting, rich colors, "
    "high detail, no text, no letters, no watermark. Scene: "
)
RESPALDO = "Abstract cinematic background with soft light and the colors of Colombia's flag"


def generar_imagen(prompt: str, destino: Path) -> Path:
    if not config.OPENAI_API_KEY:
        raise RuntimeError("Falta OPENAI_API_KEY")
    cliente = OpenAI(api_key=config.OPENAI_API_KEY)

    extra = {"response_format": "b64_json"} if config.IMAGE_MODEL.startswith("dall-e") else {}
    if config.IMAGE_MODEL == "dall-e-3":
        extra["quality"] = "standard"

    def _pedir(texto: str):
        return cliente.images.generate(
            model=config.IMAGE_MODEL, prompt=ESTILO + texto, size=config.IMAGE_SIZE, n=1, **extra
        )

    try:
        resultado = _pedir(prompt)
    except BadRequestError as e:
        # Suele pasar cuando el filtro de contenido rechaza el prompt.
        log.warning("Imagen rechazada (%s). Uso un fondo genérico.", e)
        resultado = _pedir(RESPALDO)

    destino.write_bytes(base64.b64decode(resultado.data[0].b64_json))
    return destino


def imagen_de_prueba(indice: int, destino: Path) -> Path:
    """Imagen de color sólido para el modo --simular."""
    colores = ["0x1e3a8a", "0x7c2d12", "0x14532d", "0x581c87", "0x713f12", "0x0f172a"]
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
            "-i", f"color=c={colores[indice % len(colores)]}:s=1024x1792",
            "-frames:v", "1", str(destino),
        ],
        check=True,
    )
    return destino
