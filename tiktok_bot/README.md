# Bot de videos para TikTok

Genera de 1 a 2 videos verticales (1080x1920) al día, listos para subir a TikTok.

| Paso | Servicio |
|---|---|
| Guion (escenas, texto, hashtags) | Claude API (Anthropic) |
| Imágenes | OpenAI (DALL-E 3 o gpt-image-1) |
| Voz en español | ElevenLabs |
| Noticias de Colombia | Google News RSS (gratis) |
| Montaje, zoom, subtítulos, música | FFmpeg |

Categorías: supervivencia (ficción), finanzas personales, psicología, salud, temas
generales y política actual de Colombia (Congreso, expresidente Petro, presidente
Abelardo de la Espriella, ministro de Comercio Mauricio Gómez). Se editan en `config.py`.

## Instalación

```bash
# FFmpeg: sudo apt install ffmpeg   (macOS: brew install ffmpeg)
cd tiktok_bot
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # y pon tus claves
```

Para `ELEVENLABS_VOICE_ID`, elige una voz en español en la Voice Library de ElevenLabs y copia su ID.

## Uso

```bash
python bot.py generar --simular          # prueba el montaje sin gastar en APIs
python bot.py generar                    # 1 video
python bot.py generar -n 2               # 2 videos
python bot.py generar -c politica_colombia
python bot.py programar                  # se queda corriendo y genera a las HORAS_PUBLICACION
```

O con cron (2 videos diarios, 9:00 y 18:30):

```
0 9  * * * cd /ruta/tiktok_bot && .venv/bin/python bot.py generar >> bot.log 2>&1
30 18 * * * cd /ruta/tiktok_bot && .venv/bin/python bot.py generar >> bot.log 2>&1
```

Cada video queda en `salida/<fecha>_<categoria>_<titulo>/`:
- `video.mp4` – el video final
- `publicacion.txt` – descripción, hashtags y fuentes para copiar al publicar
- `guion.json` – el guion completo

## Política y noticias

- Los guiones políticos se escriben **solo** con titulares reales de los últimos 3 días;
  si no hay noticias nuevas, el bot cambia de categoría en vez de inventar.
- Tono neutral, con atribución a cada medio y fuentes en `publicacion.txt`.
- Las imágenes nunca muestran a políticos reales (usa símbolos: Capitolio, bandera, urnas).
  OpenAI además rechaza imágenes de personas reales.
- Revisa cada video antes de publicarlo: la IA puede equivocarse.

## Al publicar en TikTok

- Activa la etiqueta **"Contenido generado por IA"** (TikTok la exige para este tipo de video).
- La subida es manual. Subir automáticamente requiere la Content Posting API de TikTok,
  que pide registrar una app y pasar su revisión.

## Costo aproximado por video

6 imágenes DALL-E 3 (~0,24 USD) + ~1.000 caracteres de ElevenLabs + 1 llamada a Claude.
