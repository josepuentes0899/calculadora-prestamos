"""Genera guiones de video con la API de Claude (salida estructurada)."""

from __future__ import annotations

import logging

import anthropic
from pydantic import BaseModel, Field

import config
from noticias import Noticia

log = logging.getLogger(__name__)


class Escena(BaseModel):
    narracion: str = Field(description="Texto que se narra en voz alta, 1 a 3 frases cortas.")
    prompt_imagen: str = Field(
        description="Descripción en inglés de la imagen vertical para esta escena."
    )


class Guion(BaseModel):
    titulo: str
    gancho: str = Field(description="Primera frase, pensada para enganchar en 2 segundos.")
    escenas: list[Escena]
    descripcion_tiktok: str = Field(description="Texto de la publicación, máximo 150 caracteres.")
    hashtags: list[str]
    fuentes: list[str] = Field(description="Medios y enlaces usados. Vacío si no aplica.")


SISTEMA = """Eres guionista de videos cortos en español latino (Colombia) para TikTok.

Reglas del guion:
- Duración total de 45 a 75 segundos narrados (unas 120 a 180 palabras).
- Entre 5 y 7 escenas. La primera narración es el gancho.
- Lenguaje sencillo, frases cortas, ritmo ágil. Cierra con una pregunta o llamado a comentar.
- Los prompts de imagen van en inglés, estilo ilustración cinematográfica vertical 9:16,
  sin texto dentro de la imagen.
- Nunca pidas imágenes con el rostro o la apariencia de personas reales (políticos,
  famosos). Para política usa símbolos: el Capitolio Nacional, la bandera de Colombia,
  urnas, un recinto parlamentario vacío, documentos, etc.

Reglas para noticias y política:
- Usa únicamente los hechos que aparecen en los titulares entregados. Si un dato no está
  ahí, no lo digas.
- Atribuye la información ("según El Tiempo...").
- Tono neutral e informativo: no opines, no ataques ni favorezcas a ninguna persona o partido.
- Pon en "fuentes" cada medio y enlace que usaste.

Para salud y finanzas: información general y educativa, sin promesas ni consejos personalizados.
"""


def _cliente() -> anthropic.Anthropic:
    if not config.ANTHROPIC_API_KEY:
        raise RuntimeError("Falta ANTHROPIC_API_KEY")
    return anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)


def generar_guion(categoria: dict, noticias: list[Noticia], temas_recientes: list[str]) -> Guion:
    partes = [
        f"Categoría: {categoria['nombre']}",
        f"Instrucciones: {categoria['instrucciones']}",
    ]
    if noticias:
        lista = "\n".join(
            f"- {n.titulo} | medio: {n.medio} | fecha: {n.fecha} | enlace: {n.enlace}"
            for n in noticias
        )
        partes.append(
            "Titulares recientes (elige UNA noticia o un tema común entre varias):\n" + lista
        )
    if temas_recientes:
        partes.append(
            "No repitas estos temas ya publicados:\n- " + "\n- ".join(temas_recientes[-15:])
        )
    partes.append("Escribe el guion completo.")

    respuesta = _cliente().beta.messages.parse(
        model=config.CLAUDE_MODEL,
        max_tokens=16000,
        system=SISTEMA,
        messages=[{"role": "user", "content": "\n\n".join(partes)}],
        output_format=Guion,
        output_config={"effort": config.CLAUDE_EFFORT},
        # Si el modelo rechaza la solicitud, la API reintenta con un modelo de respaldo.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    )

    if respuesta.stop_reason == "refusal":
        raise RuntimeError(f"Claude rechazó generar el guion: {respuesta.stop_details}")
    if respuesta.stop_reason == "max_tokens" or respuesta.parsed_output is None:
        raise RuntimeError(f"Guion incompleto (stop_reason={respuesta.stop_reason})")

    guion = respuesta.parsed_output
    log.info("Guion generado: %s (%d escenas)", guion.titulo, len(guion.escenas))
    return guion


def guion_de_prueba(categoria: dict) -> Guion:
    """Guion fijo para el modo --simular (no llama a ninguna API)."""
    textos = [
        "¿Sabías que tu cerebro toma decisiones antes de que te des cuenta?",
        "Estudios muestran que muchas elecciones se preparan en segundos previos.",
        "Por eso los hábitos pesan más que la fuerza de voluntad.",
        "Si quieres cambiar algo, cambia tu entorno primero.",
        "¿Tú qué hábito quieres cambiar? Cuéntame en los comentarios.",
    ]
    return Guion(
        titulo=f"Prueba - {categoria['nombre']}",
        gancho=textos[0],
        escenas=[Escena(narracion=t, prompt_imagen="test") for t in textos],
        descripcion_tiktok="Video de prueba generado por el bot.",
        hashtags=["prueba", "bot"],
        fuentes=[],
    )
