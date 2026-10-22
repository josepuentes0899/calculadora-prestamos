"""Ensambla imágenes, voz y subtítulos en un video vertical con FFmpeg."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

import config

log = logging.getLogger(__name__)


def _ffmpeg(args: list[str], cwd: Path | None = None) -> None:
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *args]
    resultado = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if resultado.returncode != 0:
        raise RuntimeError(f"FFmpeg falló: {resultado.stderr.strip()[-800:]}")


def duracion(archivo: Path) -> float:
    salida = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(archivo)],
        capture_output=True, text=True, check=True,
    )
    return float(salida.stdout.strip())


def clip_escena(imagen: Path, audio: Path, destino: Path, indice: int) -> float:
    """Crea un clip con efecto de zoom lento (Ken Burns) sobre la imagen + su narración."""
    dur = duracion(audio) + 0.25  # pequeña pausa entre escenas
    frames = int(dur * config.FPS)
    w, h = config.ANCHO, config.ALTO
    # Alterna zoom de entrada y de salida para dar variedad.
    zoom = "min(1.0+0.12*on/{f},1.12)" if indice % 2 == 0 else "max(1.12-0.12*on/{f},1.0)"
    filtro = (
        f"scale={w * 3 // 2}:{h * 3 // 2}:force_original_aspect_ratio=increase,"
        f"crop={w * 3 // 2}:{h * 3 // 2},"
        f"zoompan=z='{zoom.format(f=frames)}':d={frames}"
        f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={config.FPS},"
        "format=yuv420p"
    )
    _ffmpeg([
        "-i", str(imagen), "-i", str(audio),
        "-filter_complex", f"[0:v]{filtro}[v];[1:a]apad=pad_dur=0.25,aresample=44100[a]",
        "-map", "[v]", "-map", "[a]", "-t", f"{dur:.3f}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "aac", "-b:a", "160k", "-ac", "2",
        str(destino),
    ])
    return dur


def _tiempo_srt(seg: float) -> str:
    ms = int(round(seg * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def escribir_subtitulos(textos: list[str], duraciones: list[float], destino: Path,
                        palabras_por_linea: int = 5) -> None:
    """Divide cada narración en trozos cortos y reparte el tiempo según su longitud."""
    bloques, inicio = [], 0.0
    for texto, dur in zip(textos, duraciones):
        palabras = texto.split()
        trozos = [" ".join(palabras[i:i + palabras_por_linea])
                  for i in range(0, len(palabras), palabras_por_linea)] or [""]
        total = sum(len(t) for t in trozos) or 1
        t = inicio
        for trozo in trozos:
            d = (dur - 0.25) * len(trozo) / total
            bloques.append((t, t + d, trozo))
            t += d
        inicio += dur

    lineas = []
    for n, (a, b, txt) in enumerate(bloques, 1):
        lineas += [str(n), f"{_tiempo_srt(a)} --> {_tiempo_srt(b)}", txt.upper(), ""]
    destino.write_text("\n".join(lineas), encoding="utf-8")


def ensamblar(clips: list[Path], subtitulos: Path, destino: Path, trabajo: Path) -> Path:
    lista = trabajo / "clips.txt"
    lista.write_text("".join(f"file '{c.name}'\n" for c in clips), encoding="utf-8")

    estilo = (
        f"FontName={config.FUENTE_SUBTITULOS},FontSize=14,Bold=1,"
        "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,"
        "Outline=3,Shadow=0,Alignment=2,MarginV=90"
    )
    filtro_v = f"[0:v]subtitles={subtitulos.name}:force_style='{estilo}'[v]"
    args = ["-f", "concat", "-safe", "0", "-i", lista.name]

    if config.MUSICA_FONDO and Path(config.MUSICA_FONDO).exists():
        args += ["-stream_loop", "-1", "-i", str(Path(config.MUSICA_FONDO).resolve())]
        filtro_a = (f"[1:a]volume={config.VOLUMEN_MUSICA}[m];"
                    "[0:a][m]amix=inputs=2:duration=first:dropout_transition=0[a]")
    else:
        filtro_a = "[0:a]anull[a]"

    args += [
        "-filter_complex", f"{filtro_v};{filtro_a}",
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart",
        str(destino.resolve()),
    ]
    # Se ejecuta dentro de la carpeta de trabajo para no tener que escapar rutas.
    _ffmpeg(args, cwd=trabajo)
    return destino
