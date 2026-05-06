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

This repository provides an **ONNX exported version** of the excellent German Kokoro TTS model [kikiri-german-martin](https://huggingface.co/kikiri-tts/kikiri-german-martin). 

By using the ONNX format, you can run this high-quality Text-to-Speech model without needing PyTorch. This results in significantly faster inference times, a lower memory footprint, and easier integration into various environments like C++, Rust, mobile apps, or web servers using the ONNX Runtime.

## Model Details

### Model Description

This is an acoustic Text-to-Speech model based on the Kokoro architecture, specifically tailored for the German language featuring the single male voice "Martin". It has been exported to the ONNX graph format to maximize compatibility and performance.

- **Developed by:** Original model by `kikiri-tts`, ONNX conversion by huggingFresse
- **Model type:** Text-to-Speech (Acoustic Model)
- **Language(s) (NLP):** German (de)
- **License:** Apache 2.0
- **Finetuned from model:** [kikiri-tts/kikiri-german-martin](https://huggingface.co/kikiri-tts/kikiri-german-martin)

### Model Sources

- **Original Repository:** [kikiri-tts/kikiri-german-martin](https://huggingface.co/kikiri-tts/kikiri-german-martin)
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

## How to Get Started with the Model

I included a Dockerfile and a main.py file, so you can simply use docker compose to get it started:

docker-compose.yml
```yml
services:
  kokoro-onnx:
    build: .
    container_name: kokoro-onnx
    restart: unless-stopped
    ports:
      - "8881:8881"
    environment:
      - KOKORO_ONNX_THREADS=4
      - KOKORO_ONNX_VOICE=martin
      - KOKORO_ONNX_LANG=de
      - OMP_NUM_THREADS=4
      - OPENBLAS_NUM_THREADS=4
      - MKL_NUM_THREADS=4
      - NUMEXPR_NUM_THREADS=4
      - OMP_WAIT_POLICY=PASSIVE
```

If you want to use it in Home Assistant, this is an easy way to make it wyoming-ready (just add this into your docker-compose.yml):

```yml
  wyoming_openai_onnx:
    image: ghcr.io/roryeckel/wyoming_openai:latest
    container_name: wyoming_openai_onnx
    ports:
      - "10203:10203"
    restart: unless-stopped
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
    depends_on:
      - kokoro-onnx
```

## Training Details
This repository only contains a format conversion. No additional training or fine-tuning was performed. For details regarding the training data, hyperparameters, and procedures, please refer to the base model: [kikiri-tts/kikiri-german-martin](https://huggingface.co/kikiri-tts/kikiri-german-martin).

## Citation
If you use this model, please credit the original authors:
```
@misc{kikiri-german-martin,
  author = {kikiri-tts},
  title = {Kokoro German Voice - Martin},
  year = {2025},
  publisher = {Hugging Face},
  howpublished = {\url{[https://huggingface.co/kikiri-tts/kikiri-german-martin](https://huggingface.co/kikiri-tts/kikiri-german-martin)}}
}

@misc{kokoro-82m,
  author = {hexgrad},
  title = {Kokoro-82M},
  year = {2024},
  publisher = {Hugging Face},
  howpublished = {\url{[https://huggingface.co/hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M)}}
}
```