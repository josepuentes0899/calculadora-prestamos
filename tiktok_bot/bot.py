#!/usr/bin/env python3
"""Bot que genera videos verticales para TikTok.

Flujo por video:
  1. Elige una categoría (sin repetir la anterior).
  2. Si es de noticias, busca titulares recientes en Google News.
  3. Claude escribe el guion (escenas + prompts de imagen).
  4. OpenAI genera una imagen por escena.
  5. ElevenLabs narra cada escena en español.
  6. FFmpeg une todo con zoom, subtítulos y música opcional.

Uso:
  python bot.py generar               # 1 video ahora
  python bot.py generar -n 2          # 2 videos ahora
  python bot.py generar -c politica_colombia
  python bot.py generar --simular     # prueba FFmpeg sin gastar APIs
  python bot.py programar             # corre siempre y genera a las HORAS_PUBLICACION
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import re
import time
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path

import config
import guiones
import imagenes
import noticias as noticias_mod
import video
import voz

log = logging.getLogger("bot")


# --- Estado (historial de videos) -----------------------------------------

def cargar_estado() -> dict:
    if config.ESTADO_ARCHIVO.exists():
        return json.loads(config.ESTADO_ARCHIVO.read_text(encoding="utf-8"))
    return {"historial": [], "enlaces_usados": []}


def guardar_estado(estado: dict) -> None:
    estado["historial"] = estado["historial"][-200:]
    estado["enlaces_usados"] = estado["enlaces_usados"][-500:]
    config.ESTADO_ARCHIVO.write_text(
        json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def slug(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")[:50] or "video"


# --- Selección de categoría -----------------------------------------------

def elegir_categoria(estado: dict, excluir: set[str]) -> str:
    ultima = estado["historial"][-1]["categoria"] if estado["historial"] else None
    opciones = [k for k in config.CATEGORIAS if k not in excluir and k != ultima]
    if not opciones:
        opciones = [k for k in config.CATEGORIAS if k not in excluir]
    pesos = [config.CATEGORIAS[k]["peso"] for k in opciones]
    return random.choices(opciones, weights=pesos, k=1)[0]


# --- Generación de un video ------------------------------------------------

def generar_video(estado: dict, categoria_id: str | None = None, simular: bool = False) -> Path:
    probadas: set[str] = set()
    titulares = []
    while True:
        cid = categoria_id or elegir_categoria(estado, probadas)
        cat = config.CATEGORIAS[cid]
        if not cat["noticias"] or simular:
            break
        titulares = noticias_mod.noticias_para_categoria(
            cat["noticias"], set(estado["enlaces_usados"])
        )
        if titulares:
            break
        log.warning("Sin noticias nuevas para %s.", cid)
        if categoria_id:
            raise RuntimeError(f"No hay noticias recientes para {cid}")
        probadas.add(cid)

    log.info("Categoría: %s", cat["nombre"])
    temas_previos = [h["titulo"] for h in estado["historial"] if h["categoria"] == cid]

    guion = (guiones.guion_de_prueba(cat) if simular
             else guiones.generar_guion(cat, titulares, temas_previos))

    marca = datetime.now().strftime("%Y%m%d-%H%M")
    carpeta = config.SALIDA_DIR / f"{marca}_{cid}_{slug(guion.titulo)}"
    trabajo = carpeta / "trabajo"
    trabajo.mkdir(parents=True, exist_ok=True)
    (carpeta / "guion.json").write_text(guion.model_dump_json(indent=2), encoding="utf-8")

    clips, duraciones, textos = [], [], []
    for i, escena in enumerate(guion.escenas):
        log.info("Escena %d/%d", i + 1, len(guion.escenas))
        img = trabajo / f"img_{i:02}.png"
        aud = trabajo / f"voz_{i:02}.mp3"
        clip = trabajo / f"clip_{i:02}.mp4"
        if simular:
            imagenes.imagen_de_prueba(i, img)
            voz.audio_de_prueba(escena.narracion, aud)
        else:
            imagenes.generar_imagen(escena.prompt_imagen, img)
            voz.sintetizar(escena.narracion, aud)
        duraciones.append(video.clip_escena(img, aud, clip, i))
        clips.append(clip)
        textos.append(escena.narracion)

    subs = trabajo / "subtitulos.srt"
    video.escribir_subtitulos(textos, duraciones, subs)
    salida = video.ensamblar(clips, subs, carpeta / "video.mp4", trabajo)

    # Texto listo para copiar al publicar. TikTok exige marcar el contenido hecho con IA.
    hashtags = " ".join("#" + h.lstrip("#").replace(" ", "") for h in guion.hashtags)
    publicacion = [guion.descripcion_tiktok, "", hashtags + " #IA",
                   "", "Contenido generado con IA: activa la etiqueta 'Contenido generado por IA'."]
    if guion.fuentes:
        publicacion += ["", "Fuentes:", *guion.fuentes]
    (carpeta / "publicacion.txt").write_text("\n".join(publicacion), encoding="utf-8")

    estado["historial"].append({
        "fecha": datetime.now().isoformat(timespec="minutes"),
        "categoria": cid,
        "titulo": guion.titulo,
        "carpeta": str(carpeta),
    })
    estado["enlaces_usados"] += [n.enlace for n in titulares]
    guardar_estado(estado)

    log.info("Listo: %s (%.0f s)", salida, sum(duraciones))
    return salida


# --- Programación diaria ---------------------------------------------------

def proxima_hora(ahora: datetime) -> datetime:
    candidatas = []
    for h in config.HORAS_PUBLICACION:
        hh, mm = (int(x) for x in h.strip().split(":"))
        t = ahora.replace(hour=hh, minute=mm, second=0, microsecond=0)
        candidatas.append(t if t > ahora else t + timedelta(days=1))
    return min(candidatas)


def programar(simular: bool) -> None:
    log.info("Modo programado. Horas: %s", ", ".join(config.HORAS_PUBLICACION))
    while True:
        siguiente = proxima_hora(datetime.now())
        log.info("Próximo video: %s", siguiente.strftime("%Y-%m-%d %H:%M"))
        time.sleep(max(0, (siguiente - datetime.now()).total_seconds()))
        try:
            generar_video(cargar_estado(), simular=simular)
        except Exception:
            log.exception("Falló la generación; se intentará en la próxima hora programada.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Bot de videos para TikTok")
    sub = parser.add_subparsers(dest="comando", required=True)

    g = sub.add_parser("generar", help="Genera videos ahora")
    g.add_argument("-n", "--cantidad", type=int, default=1)
    g.add_argument("-c", "--categoria", choices=list(config.CATEGORIAS))
    g.add_argument("--simular", action="store_true", help="Sin APIs, solo prueba FFmpeg")

    p = sub.add_parser("programar", help="Genera videos todos los días a las horas configuradas")
    p.add_argument("--simular", action="store_true")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if args.comando == "generar":
        estado = cargar_estado()
        for _ in range(args.cantidad):
            generar_video(estado, args.categoria, args.simular)
    else:
        programar(args.simular)


if __name__ == "__main__":
    main()
