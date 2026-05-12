from __future__ import annotations

import io
import os
import time
import wave
import re
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, Request
from fastapi.responses import Response
from kokoro_onnx import Kokoro


# ====================== CONFIG ======================
MODEL_PATH = os.getenv("KOKORO_ONNX_MODEL", "/app/kokoro-martin.onnx")
VOICES_PATH = "/app/voices-martin.npz"
DEFAULT_VOICE = os.getenv("KOKORO_ONNX_VOICE", "martin")
DEFAULT_LANG = os.getenv("KOKORO_ONNX_LANG", "de")
SAMPLE_RATE = 24000

# Pause aus Docker-Compose laden (Standard: 0.25 Sekunden, vielen Dank an notimp für den Pausen-Code, siehe https://github.com/hexgrad/kokoro/issues/290#issuecomment-4415522841)
PAUSE_DURATION = float(os.getenv("KOKORO_PAUSE_DURATION", "0.25"))
MAX_WORKERS = int(os.getenv("KOKORO_MAX_WORKERS", "4"))

# ONNX / CPU Optimierung
os.environ.setdefault("OMP_NUM_THREADS", os.getenv("KOKORO_ONNX_THREADS", "1"))
os.environ.setdefault("OPENBLAS_NUM_THREADS", os.getenv("KOKORO_ONNX_THREADS", "1"))
os.environ.setdefault("MKL_NUM_THREADS", os.getenv("KOKORO_ONNX_THREADS", "1"))
os.environ.setdefault("NUMEXPR_NUM_THREADS", os.getenv("KOKORO_ONNX_THREADS", "1"))
os.environ.setdefault("ONNXRUNTIME_EXECUTION_MODE", "PARALLEL")


app = FastAPI()
kokoro: Kokoro | None = None


# ==================== HELPER FUNKTIONEN ====================


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


def split_into_sentences(text: str):
    """Trennt den Text an echten Satzgrenzen (.  !  ?  Zeilenumbruch)."""
    # Mehrfache Leerzeilen normalisieren
    text = re.sub(r"\n\s*\n", "\n\n", text)

    # Splitte nur an echten Satzenden: . ! ? gefolgt von Leerzeichen + Nicht-Leerzeichen.
    # Doppelpunkt und " werden bewusst NICHT als Trenner verwendet.
    sentences = re.split(r"(?<=[.!?])\s+(?=\S)", text)

    # Zeilenumbrüche innerhalb der Segmente weiter aufteilen
    result = []
    for segment in sentences:
        for line in segment.split("\n"):
            line = line.strip()
            if line and len(line) > 1:
                result.append(line)

    return result


def process_sentence(item):
    """Wird im ThreadPool ausgeführt."""
    idx, sentence, voice, speed, lang, tts_instance = item

    # 1. Zeilenumbrüche entfernen, da diese intern bei kokoro-onnx
    #    zu "input=2" führen, wenn der Satz damit endet.
    sentence = sentence.replace("\n", " ").strip()

    # 2. Problematische typografische Sonderzeichen entschärfen.
    safe_sentence = re.sub(r'[«‹–""]', ",", sentence).strip()

    if not safe_sentence:
        return idx, None, None, "Satz leer oder nur Sonderzeichen"

    try:
        samples, sr = tts_instance.create(
            text=safe_sentence,
            voice=voice,
            speed=speed,
            lang=lang,
        )
        return idx, samples, sr, None

    except ValueError as e:
        err_str = str(e)
        if "number of lines in input and output must be equal" in err_str:
            # ROBUSTER FALLBACK: Wenn espeak abstürzt (z. B. bei unbekannten
            # Abkürzungen), entfernen wir exotische Zeichen, behalten aber
            # normale Satzzeichen für eine natürliche Aussprache.
            very_safe = re.sub(r"[^\w\säöüßÄÖÜ.,:;!?\"'\-]", " ", safe_sentence).strip()
            if very_safe:
                try:
                    samples, sr = tts_instance.create(
                        text=very_safe,
                        voice=voice,
                        speed=speed,
                        lang=lang,
                    )
                    return idx, samples, sr, None
                except Exception as e2:
                    return idx, None, None, f"Fallback fehlgeschlagen: {e2}"
        return idx, None, None, f"Fehler für Satz '{sentence}': {err_str}"

    except Exception as e:
        return idx, None, None, f"Fehler für Satz '{sentence}': {e}"


# ==================== API ENDPUNKTE ====================


@app.get("/v1/audio/voices")
async def list_voices():
    return {"voices": [DEFAULT_VOICE]}


@app.post("/v1/audio/speech")
async def generate_speech(request: Request):
    data = await request.json()
    text = str(data.get("input") or "")
    voice = str(data.get("voice") or DEFAULT_VOICE)
    speed = float(data.get("speed") or 1.125)
    lang = str(data.get("lang") or data.get("language") or DEFAULT_LANG)
    req_pause_duration = float(data.get("pause_duration", PAUSE_DURATION))

    if voice != DEFAULT_VOICE:
        voice = DEFAULT_VOICE

    print(f"Generiere ONNX: {text[:40]}... [{voice}, pause={req_pause_duration}s]", flush=True)

    try:
        started = time.perf_counter()
        tts_instance = get_tts()

        sentences = split_into_sentences(text)

        if not sentences:
            return Response(status_code=400, content="Kein verarbeitbarer Text gefunden.")

        results = [None] * len(sentences)
        tasks = [(i, s, voice, speed, lang, tts_instance) for i, s in enumerate(sentences)]

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            for idx, samples, sr, error in executor.map(process_sentence, tasks):
                if error:
                    print(f"Fehler in Satz {idx + 1}: {error}", flush=True)
                else:
                    results[idx] = samples

        # === PAUSEN-LOGIK ===
        all_audio = []

        # BUGFIX: Fehlgeschlagene Sätze werden nicht mehr komplett gedroppt,
        # sondern durch eine kurze Stille ersetzt. So bleibt die zeitliche
        # Struktur erhalten und kein Text wird "zusammengezogen".
        valid_samples = []
        for s in results:
            if s is not None:
                valid_samples.append(s)
            else:
                valid_samples.append(
                    np.zeros(int(SAMPLE_RATE * req_pause_duration), dtype=np.float32)
                )

        num_sentences = len(valid_samples)

        for i, samples in enumerate(valid_samples):
            all_audio.append(samples)
            if req_pause_duration > 0:
                if i < num_sentences - 1:
                    # Pause zwischen den Sätzen
                    pause = np.zeros(int(SAMPLE_RATE * req_pause_duration), dtype=np.float32)
                    all_audio.append(pause)
                elif i == num_sentences - 1:
                    # Diese Pause hilft dem I2S-Puffer des Speakers (z. B. ESPHome)
                    # zu leeren und die Status-LED geht aus.
                    pause = np.zeros(int(SAMPLE_RATE * req_pause_duration), dtype=np.float32)
                    all_audio.append(pause)

        if not all_audio:
            raise ValueError("Ich hab alles gegeben, aber es konnte kein Audio generiert werden.")

        final_audio = np.concatenate(all_audio)

        elapsed = time.perf_counter() - started
        print(
            f"Kokoro ONNX fertig in {elapsed:.3f}s, samples={len(final_audio)}, Sätze={num_sentences}",
            flush=True,
        )

        return Response(content=wav_bytes(final_audio, SAMPLE_RATE), media_type="audio/wav")

    except Exception as err:
        print(f"Kokoro ONNX Fehler: {err!r}", flush=True)
        return Response(status_code=500, content=str(err))


print("Initialisiere Kokoro-ONNX-Service...", flush=True)
get_tts()