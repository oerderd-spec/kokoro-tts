---
license: apache-2.0
language:
- de
base_model:
- kikiri-tts/kikiri-german-martin
pipeline_tag: text-to-speech
tags:
- onnx
- single-speaker
- kokoro
- text-to-speech
- german
---

# 🗣️ Kokoro TTS - German Voice 'Martin' (ONNX)

This repository provides an **ONNX exported version** with **German text normalization** of the German Kokoro TTS model [kikiri-german-martin](https://huggingface.co/kikiri-tts/kikiri-german-martin). It is a "German single-speaker TTS model fine-tuned on the **Martin Harbecke** voice using [StyleTTS2](https://github.com/yl4579/StyleTTS2) Stage 2. Built on top of [kikiri-german-base-51speakers-synthetic](https://huggingface.co/kikiri-tts/kikiri-german-base-51speakers-synthetic)."

By using the ONNX format, you can run this german Text-to-Speech model without needing PyTorch. This results in significantly faster inference times (x2), a lower memory footprint, and easier integration into various environments like C++, Rust, mobile apps, or web servers using the ONNX Runtime.

## Audio Samples

### Main sample: v1.1 German normalization

This sample demonstrates the v1.1 normalization layer for dates, times, decimal numbers, units, abbreviations, ordinals and Euro amounts.

<audio controls>
  <source src="https://huggingface.co/huggingFresse/Kokoro-82M-ONNX-German-Martin/resolve/main/martin-onnx-beispiel-v1.1.mp3" type="audio/mpeg">
  Your browser says no to audio (but at least it rhymes)
</audio>

Spoken text (v1.1):

> Zum 14.05.2026 um 18:20 Uhr ist das Abendessen geplant. Für den Auflauf brauchen wir 1,5 kg Kartoffeln, 500 g Quark, 2 Eier, 1 ltr. Milch und ggf. 3 cm mehr Backpapier. Prof. Klein sagt: "Bitte stelle die Form auf die 2. Schiene, backe alles für 45 Min. und lass es danach 1 Min. oder auch 2 Min. ruhen." Die Kosten liegen bei ca. 12,80 EUR zzgl. Pfand.


### Legacy samples: v1.0

These older samples were generated with the initial v1.0 service setup before the v1.1 German normalization layer.

Sample: default (0.25s pause between sentences, speed = 1.125)
<audio controls>
  <source src="https://huggingface.co/huggingFresse/Kokoro-82M-ONNX-German-Martin/resolve/main/martin-onnx-beispiel-0.25pause.mp3" type="audio/mpeg">
  Your browser says no to audio (but at least it rhymes)
</audio>

Sample: no additional pauses, speed = 1.0
<audio controls>
  <source src="https://huggingface.co/huggingFresse/Kokoro-82M-ONNX-German-Martin/resolve/main/martin-onnx-beispiel.mp3" type="audio/mpeg">
  Your browser says no to audio (but at least it rhymes)
</audio>

## Model Details

### Model Description

This is an acoustic Text-to-Speech model based on the Kokoro architecture, specifically tailored for the German language featuring the single male voice "Martin". It has been exported to the ONNX graph format to maximize compatibility and performance.

- **Developed by:** Original model by `dida-80b` and `kikiri-tts`, ONNX conversion by `huggingFresse`
- **Model type:** Text-to-Speech (Acoustic Model)
- **Language(s) (NLP):** German (de)
- **License:** Apache 2.0
- **Finetuned from model:** [kikiri-tts/kikiri-german-martin](https://huggingface.co/kikiri-tts/kikiri-german-martin)

### Model Sources

- **Original Repository:** [kikiri-tts/kikiri-german-martin](https://huggingface.co/kikiri-tts/kikiri-german-martin)
- **Base Model:** [dida-80b/kokoro-german-hui-multispeaker-base](https://huggingface.co/dida-80b/kokoro-german-hui-multispeaker-base)
- **Kokoro Architecture:** [hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M)

## Uses

This model is intended to be used with the ONNX Runtime to synthesize German speech from phonemized text. It is ideal for:
- Local offline text-to-speech generation.
- Integration into low-resource environments (Edge devices, Raspberry Pi).
- Building high-performance TTS microservices.

## Bias, Risks, and Limitations

As with any TTS model, the output quality heavily relies on the quality of the input text and the phonemizer used. 
- **Pronunciation:** The model might mispronounce rare words, foreign names, or complex compound nouns if they are not correctly converted to phonemes first.
- **Emotion:** While the model sounds very natural, precise control over specific emotions (like shouting, crying, or whispering) is limited by the training data of the base model.

## How to run it yourself

The repository now contains the same two-service setup I use with Home Assistant Assist:

- `onnx-docker/`: the Kokoro ONNX FastAPI service. It exposes an OpenAI-compatible `/v1/audio/speech` endpoint and applies the v1.1 German text normalization before synthesis.
- `wyoming_openai_german_separator/`: a small overlay image for the Wyoming OpenAI bridge. It patches German sentence segmentation so streaming TTS does not split too early after dotted abbreviations such as `Prof.`, `Min.`, `Stck.` or `ltr.`.
- `german_text_rules.py`: the essential shared rule file. It is mounted into both containers, so abbreviation expansion, unit handling and Wyoming sentence-boundary protection use the same source of truth. Keep this file next to `docker-compose.yml` unless you also adjust the volume mounts.

### 1. Clone the model repository

This is a Hugging Face model repository with Git LFS files, so make sure Git LFS is installed.

```bash
git lfs install
git clone https://huggingface.co/huggingFresse/Kokoro-82M-ONNX-German-Martin
cd Kokoro-82M-ONNX-German-Martin
```

### 2. Start Kokoro ONNX and the Wyoming bridge

The included `docker-compose.yml` starts both the TTS service and the Wyoming bridge:

```bash
docker compose up -d --build
```

Full compose file:

```yml
services:
  # German Kokoro ONNX FastAPI service with v1.1 text normalization.
  kokoro-onnx:
    build:
      context: .
      dockerfile: onnx-docker/Dockerfile
    container_name: kokoro-onnx
    restart: unless-stopped
    ports:
      - "8881:8881"
    environment:
      - KOKORO_ONNX_THREADS=2
      - KOKORO_ONNX_INTRA_OP_THREADS=2
      - KOKORO_ONNX_INTER_OP_THREADS=2
      - KOKORO_ONNX_EXECUTION_MODE=sequential
      - KOKORO_ONNX_GRAPH_OPT=all
      - KOKORO_ONNX_SPEED=1.125
      - KOKORO_ONNX_TRIM=true
      - KOKORO_ONNX_VOICE=martin
      - KOKORO_ONNX_LANG=de
      - OMP_NUM_THREADS=2
      - OPENBLAS_NUM_THREADS=2
      - MKL_NUM_THREADS=2
      - NUMEXPR_NUM_THREADS=2
      - OMP_WAIT_POLICY=PASSIVE
      - KOKORO_PAUSE_DURATION=0.25
      - KOKORO_MAX_WORKERS=2 # use 1 if you encounter problems in correct word-order, a better fix will be released soon
    volumes:
      - ./german_text_rules.py:/app/german_text_rules.py:ro

  # Wyoming bridge for Home Assistant Assist.
  wyoming_openai_onnx:
    build: ./wyoming_openai_german_separator
    image: wyoming_openai_german_separator:latest
    container_name: wyoming_openai_onnx
    restart: unless-stopped
    ports:
      - "10203:10203"
    command:
      - python3
      - -m
      - wyoming_openai
      - --uri
      - tcp://0.0.0.0:10203
      - --languages
      - de
      - --tts-openai-url
      - http://kokoro-onnx:8881/v1
      - --tts-models
      - kokoro
      - --tts-streaming-models
      - kokoro
      - --tts-backend
      - KOKORO_FASTAPI
    volumes:
      - ./german_text_rules.py:/app/german_text_rules.py:ro
    depends_on:
      - kokoro-onnx
```

### 3. Check that the services are reachable

The Kokoro service should answer on port `8881`:

```bash
curl http://localhost:8881/v1/audio/voices
```

For Home Assistant, add the Wyoming integration and point it to the host running Docker:

```text
Host: <your-docker-host>
Port: 10203
```

### Notes on performance

The compose file uses conservative thread settings that work well on small machines such as an Intel NUC. If you run on a larger CPU, you can try increasing `KOKORO_ONNX_THREADS`, `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS` and `NUMEXPR_NUM_THREADS`.

## Changelog

### v1.1 (May 14, 2026)

- Added German text normalization before synthesis in the included FastAPI service.
- Decimal numbers with units are spoken correctly, for example "2,5 kWh" as "zwei komma fünf Kilowattstunden".
- Added singular/plural handling for units, for example "1 Kilowattstunde" vs. "2 Kilowattstunden".
- Added and improved abbreviations and units such as `zzgl.`, `mAh`, `mA`, `g`, `Stck.`, `Min.` and `ltr.`.
- Added better handling for Euro amounts such as "49,99 EUR" as "neunundvierzig Euro neunundneunzig".
- Improved German ordinal/cardinal handling in contexts such as dates, quarters, tracks, chapters and numbered labels.
- Fixed sentence pauses around common German abbreviations and dotted unit abbreviations.
- Added a v1.1 audio sample and the exact spoken text used for it.

### v1.0 (initial release)

- Initial ONNX conversion of the German Martin voice.
- Included the basic Docker/FastAPI service files.
- Fixed pauses after common abbreviations in the initial service setup.

## Training Details
This repository only contains a format conversion. No additional training or fine-tuning was performed. For details regarding the training data, hyperparameters, and procedures, please refer to the base model: [kikiri-tts/kikiri-german-martin](https://huggingface.co/kikiri-tts/kikiri-german-martin).

## Citation
If you use this model, please credit the original authors:
```
@misc{kikiri-german-martin,
  author = {kikiri-tts},
  title = {Kokoro German Voice - Martin},
  year = {2026},
  publisher = {Hugging Face},
  howpublished = {\url{https://huggingface.co/kikiri-tts/kikiri-german-martin}}
}

@misc{kokoro-german-hui-multispeaker-base,
  author = {dida-80b},
  title = {Kokoro German — HUI Multispeaker Base (Stage 1)},
  year = {2026},
  publisher = {Hugging Face},
  howpublished = {\url{https://huggingface.co/dida-80b/kokoro-german-hui-multispeaker-base/tree/main}}
}

@misc{kokoro-82m,
  author = {hexgrad},
  title = {Kokoro-82M},
  year = {2024},
  publisher = {Hugging Face},
  howpublished = {\url{https://huggingface.co/hexgrad/Kokoro-82M}}
}

@misc{kokoro-82m-onnx-german-martin,
  author = {huggingFresse},
  title = {Kokoro-82M ONNX German Martin},
  year = {2026},
  publisher = {Hugging Face},
  howpublished = {\url{https://huggingface.co/huggingFresse/Kokoro-82M-ONNX-German-Martin}}
}
```
