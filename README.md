# Beethoven

*Beethoven may have been deaf, but this project “hears” a piano through sight – turning visual cues into music.*

![Beethoven Demo](demo.gif)

## Introduction

**Beethoven** is a computer vision project that analyzes video of a piano keyboard to identify which keys are being pressed, effectively transcribing music without any audio input. It uses AI models to first determine the **relative positions of the piano keys** in the camera view, and then to **detect pressed keys (white or black)** in real-time. In homage to the composer Beethoven – who continued to create music after losing his hearing – this system doesn't need ears to recognize a melody. Instead, it "listens" with its eyes, watching the keys and predicting the notes being played.

At its core, Beethoven leverages **Roboflow** object-detection models to run inference on video frames. Two models are used: one model calibrates the layout of the keyboard (finding all keys in the frame), and another model identifies when keys are pressed. By combining these, the system can map physical key presses to specific piano notes. The application is built with a modern web tech stack: a Python **FastAPI** server (for running inference and coordinating data) and a React frontend (for live visualization). These components communicate via WebSockets to stream detection results instantly to the browser. The entire setup runs in Docker containers for easy deployment and consistency across environments.

## Roboflow Universe

*   [**Beethoven - Keys Pressed**](https://universe.roboflow.com/mjs-personal/beethoven-keys-pressed)
*   [**Beethoven - Relative Position**](https://universe.roboflow.com/mjs-personal/beethoven-relative-position)

## Documentation

*   [**Setup and Requirements**](./docs/setup.md)
*   [**Docker Compose Architecture**](./docs/architecture.md)
*   [**Configuration Details**](./docs/config.md)

## Roadmap

Beethoven is a work in progress with ambitious goals. Here are a couple of key features on the roadmap that will make the system even more powerful and musical:

* **Automatic Transcription to Sheet Music:** *Turning a series of key presses into written music, Beethoven-style.* With the ability to identify notes and the timing of each press, the project aims to generate a musical score from the video. Essentially, as the system "listens" to the pianist by watching the keys, it will record the sequence of notes and durations, then compile them into a readable format (such as a MIDI file or even rendered sheet music). This would allow someone to record themselves playing the piano (on video) and get back a transcription of what they played – all without any microphone. Achieving this will require tracking the timing between key press events (to determine rhythm and note length) and grouping notes into measures, applying music theory rules for notation. It's an ambitious feature, but fitting – Beethoven the AI could write out music the way Beethoven the composer might have, without ever hearing a sound.

---

With these components in place, Beethoven provides a novel way to **"hear" music through images**. From setting up cameras and containers to processing predictions in real-time, the project brings together computer vision, orchestration, and a bit of musical theory. We hope you find it useful or inspiring – and remember, even if you can't hear the melody, the eyes and AI of Beethoven are here to help translate those piano performances into notes and lines. Enjoy making music visible!
