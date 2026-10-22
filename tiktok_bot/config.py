"""Configuración del bot de videos para TikTok.

Las claves de API se leen de variables de entorno (o de un archivo .env).
Todo lo demás se puede ajustar aquí.
"""

import os
from pathlib import Path


def _cargar_env(ruta: Path) -> None:
    """Carga un archivo .env sencillo (CLAVE=valor) sin dependencias extra."""
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))


BASE_DIR = Path(__file__).resolve().parent
_cargar_env(BASE_DIR / ".env")

# --- Claves de API ---------------------------------------------------------
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")

# --- Modelos ---------------------------------------------------------------
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-5-5")
CLAUDE_EFFORT = os.getenv("CLAUDE_EFFORT", "medium")

# "dall-e-3" genera 1024x1792 (vertical). Si tu cuenta usa "gpt-image-1",
# cambia el modelo y el tamaño a 1024x1536.
IMAGE_MODEL = os.getenv("IMAGE_MODEL", "dall-e-3")
IMAGE_SIZE = os.getenv("IMAGE_SIZE", "1024x1792")

# Voz de ElevenLabs. Busca el ID de una voz en español en tu panel de
# ElevenLabs (Voice Library) y ponlo en ELEVENLABS_VOICE_ID.
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")
ELEVENLABS_MODEL = os.getenv("ELEVENLABS_MODEL", "eleven_multilingual_v2")

# --- Video -----------------------------------------------------------------
ANCHO, ALTO = 1080, 1920
FPS = 30
FUENTE_SUBTITULOS = os.getenv("FUENTE_SUBTITULOS", "DejaVu Sans")
MUSICA_FONDO = os.getenv("MUSICA_FONDO", "")  # ruta opcional a un mp3 libre de derechos
VOLUMEN_MUSICA = 0.12

SALIDA_DIR = Path(os.getenv("SALIDA_DIR", BASE_DIR / "salida"))
ESTADO_ARCHIVO = BASE_DIR / "estado.json"

# --- Programación diaria ---------------------------------------------------
# Horas (24h, hora local) en que el modo "programar" genera un video.
HORAS_PUBLICACION = os.getenv("HORAS_PUBLICACION", "09:00,18:30").split(",")

# --- Categorías ------------------------------------------------------------
# "peso" controla qué tan seguido sale cada categoría.
# "noticias" = consultas a Google News; si hay, el guion se basa SOLO en esos titulares.
CATEGORIAS = {
    "supervivencia_ficcion": {
        "nombre": "Supervivencia (ficción)",
        "peso": 2,
        "instrucciones": (
            "Una historia corta de supervivencia, claramente ficticia, con gancho fuerte, "
            "tensión y un consejo de supervivencia real y seguro al final."
        ),
        "noticias": [],
    },
    "finanzas_personales": {
        "nombre": "Finanzas personales",
        "peso": 2,
        "instrucciones": (
            "Un consejo práctico de finanzas personales para Colombia (ahorro, deudas, "
            "presupuesto, interés compuesto). Educativo, sin recomendar productos concretos "
            "ni prometer ganancias."
        ),
        "noticias": [],
    },
    "psicologia": {
        "nombre": "Psicología",
        "peso": 2,
        "instrucciones": (
            "Un dato o sesgo psicológico interesante, explicado con un ejemplo cotidiano. "
            "Basado en evidencia, sin diagnósticos."
        ),
        "noticias": [],
    },
    "salud": {
        "nombre": "Salud",
        "peso": 2,
        "instrucciones": (
            "Un hábito de salud respaldado por evidencia general. Nada de curas milagro; "
            "termina recordando consultar a un profesional de salud."
        ),
        "noticias": [],
    },
    "temas_generales": {
        "nombre": "Temas generales / curiosidades",
        "peso": 1,
        "instrucciones": "Una curiosidad sorprendente de ciencia, historia o geografía, verificable.",
        "noticias": [],
    },
    "politica_colombia": {
        "nombre": "Política actual de Colombia",
        "peso": 3,
        "instrucciones": (
            "Un resumen informativo y neutral de una noticia política reciente de Colombia. "
            "Usa SOLO los hechos de los titulares entregados, atribuye cada dato a su medio, "
            "no inventes cifras, citas ni acusaciones, y no tomes partido."
        ),
        "noticias": [
            "Congreso de Colombia",
            "Senado Colombia proyecto de ley",
            "Gustavo Petro expresidente",
            "presidente Abelardo de la Espriella",
            "Mauricio Gómez ministro de Comercio Industria y Turismo",
        ],
    },
}
