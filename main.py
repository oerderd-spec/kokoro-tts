from __future__ import annotations

import io
import os
import threading
import time
import wave

import numpy as np
from fastapi import FastAPI, Request
from fastapi.responses import Response
from kokoro_onnx import Kokoro

MODEL_PATH = os.getenv("KOKORO_ONNX_MODEL", "/app/kokoro-martin.onnx")
VOICES_PATH = "/app/voices-martin.npz"
DEFAULT_VOICE = os.getenv("KOKORO_ONNX_VOICE", "martin")
DEFAULT_LANG = os.getenv("KOKORO_ONNX_LANG", "de")
SAMPLE_RATE = 24000

os.environ.setdefault("OMP_NUM_THREADS", os.getenv("KOKORO_ONNX_THREADS", "4"))
os.environ.setdefault("OPENBLAS_NUM_THREADS", os.getenv("KOKORO_ONNX_THREADS", "4"))
os.environ.setdefault("MKL_NUM_THREADS", os.getenv("KOKORO_ONNX_THREADS", "4"))
os.environ.setdefault("NUMEXPR_NUM_THREADS", os.getenv("KOKORO_ONNX_THREADS", "4"))

app = FastAPI()
tts_lock = threading.Lock()
kokoro: Kokoro | None = None


def wav_bytes(samples: np.ndarray, sample_rate: int = SAMPLE_RATE) -> bytes:
    samples = np.asarray(samples, dtype=np.float32)
    samples = np.clip(samples, -1.0, 1.0)
    pcm = (samples * 32767.0).astype(np.int16)

    output = io.BytesIO()
    with wave.open(output, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm.tobytes())
    return output.getvalue()


def get_tts() -> Kokoro:
    global kokoro
    if kokoro is None:
        print("Loading Kokoro ONNX model...", flush=True)
        kokoro = Kokoro(MODEL_PATH, VOICES_PATH)
        print(f"Kokoro ONNX ready: voices={kokoro.get_voices()}", flush=True)
    return kokoro


@app.get("/v1/audio/voices")
async def list_voices():
    return {"voices": [DEFAULT_VOICE]}


@app.post("/v1/audio/speech")
async def generate_speech(request: Request):
    data = await request.json()
    text = str(data.get("input") or "")
    voice = str(data.get("voice") or DEFAULT_VOICE)
    speed = float(data.get("speed") or 1.0)
    lang = str(data.get("lang") or data.get("language") or DEFAULT_LANG)

    if voice != DEFAULT_VOICE:
        voice = DEFAULT_VOICE

    print(f"Generiere ONNX: {text[:40]}... [{voice}, lang={lang}]", flush=True)
    try:
        started = time.perf_counter()
        with tts_lock:
            samples, sample_rate = get_tts().create(text, voice=voice, speed=speed, lang=lang)
        elapsed = time.perf_counter() - started
        print(f"Kokoro ONNX fertig in {elapsed:.3f}s, samples={len(samples)}", flush=True)
        return Response(content=wav_bytes(samples, sample_rate), media_type="audio/wav")
    except Exception as err:
        print(f"Kokoro ONNX Fehler: {err!r}", flush=True)
        return Response(status_code=500, content=str(err))


print(
    "Initialisiere Kokoro-ONNX-Service: "
    f"threads={os.getenv('KOKORO_ONNX_THREADS', '4')}, "
    f"voice={DEFAULT_VOICE}, lang={DEFAULT_LANG}",
    flush=True,
)
get_tts()
