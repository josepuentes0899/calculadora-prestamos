"""Obtiene titulares recientes desde Google News (RSS) para Colombia."""

from __future__ import annotations

import logging
import urllib.parse
from dataclasses import dataclass

import feedparser

log = logging.getLogger(__name__)


@dataclass
class Noticia:
    titulo: str
    medio: str
    enlace: str
    fecha: str


def buscar_noticias(consulta: str, maximo: int = 5) -> list[Noticia]:
    """Busca titulares de los últimos días sobre `consulta` en Google News Colombia."""
    q = urllib.parse.quote(f"{consulta} when:3d")
    url = f"https://news.google.com/rss/search?q={q}&hl=es-419&gl=CO&ceid=CO:es-419"
    feed = feedparser.parse(url)
    if feed.bozo and not feed.entries:
        log.warning("No se pudo leer el RSS para %r: %s", consulta, feed.bozo_exception)
        return []

    noticias = []
    for entrada in feed.entries[:maximo]:
        medio = getattr(getattr(entrada, "source", None), "title", "") or ""
        noticias.append(
            Noticia(
                titulo=entrada.get("title", "").strip(),
                medio=medio,
                enlace=entrada.get("link", ""),
                fecha=entrada.get("published", ""),
            )
        )
    return noticias


def noticias_para_categoria(consultas: list[str], usados: set[str]) -> list[Noticia]:
    """Junta titulares de todas las consultas, quitando los ya usados en videos anteriores."""
    vistos: set[str] = set()
    resultado: list[Noticia] = []
    for consulta in consultas:
        for n in buscar_noticias(consulta):
            if n.enlace in usados or n.titulo in vistos:
                continue
            vistos.add(n.titulo)
            resultado.append(n)
    return resultado
