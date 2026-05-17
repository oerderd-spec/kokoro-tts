FROM python:3.11-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends wget curl espeak-ng libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
    numpy \
    kokoro-onnx==0.5.0

# Download model files from HuggingFace (Git LFS not supported on Railway)
RUN wget -q --show-progress -O /app/kokoro-martin.onnx \
    "https://huggingface.co/huggingFresse/Kokoro-82M-ONNX-German-Martin/resolve/main/kokoro-martin.onnx" \
    && wget -q --show-progress -O /app/voices-martin.npz \
    "https://huggingface.co/huggingFresse/Kokoro-82M-ONNX-German-Martin/resolve/main/voices-martin.npz"

COPY german_text_rules.py /app/german_text_rules.py
COPY onnx-docker/main.py /app/main.py
COPY onnx-docker/tts_normalizer.py /app/tts_normalizer.py

EXPOSE 8881

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8881", "--loop", "uvloop", "--http", "httptools"]
