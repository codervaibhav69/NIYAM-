# NIYAM — Local AI Desktop Assistant

NIYAM is a Python-based personal AI assistant designed to run locally on Windows. It combines conversational AI, voice interaction, user-controlled persistent memory, and a small allowlist of desktop actions.

## Features

- Local conversational AI using Qwen through Ollama
- Speech recognition using faster-whisper
- Spoken responses using pyttsx3 and Windows SAPI5
- Continuous voice conversation mode
- Explicitly saved personal memories with commands to list and delete them
- Restricted desktop actions, including opening Notepad and Calculator, checking the local time, and opening YouTube
- PowerShell-based startup workflow

## Technology Stack

Python, Ollama, Qwen, faster-whisper, NumPy, sounddevice, and pyttsx3.

## Requirements

- Windows 11
- Python 3.13
- Git
- Ollama
- A compatible local Qwen model

## Setup

Install Python and Ollama first.

Open PowerShell and clone this repository, or open the folder if you already downloaded it.

Create a virtual environment:

```powershell
py -3.13 -m venv .venv
```

Install the Python dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Download the model used by this project:

```powershell
ollama pull qwen3.5:4b
```

Start NIYAM:

```powershell
.\.venv\Scripts\python.exe .\main.py
```

Make sure Ollama is running locally before starting a conversation.

## Memory and Privacy

NIYAM stores persistent memory locally. Personal memory data and the local workspace are excluded from version control by `.gitignore`.

Do not commit personal memory files, credentials, audio recordings, or downloaded model binaries.

Voice features require microphone access. The first use of speech recognition may download its model, depending on local model availability.

## Project Status

NIYAM is a work in progress. Reliability, memory correctness, error handling, and safe desktop automation remain active development priorities.

The experimental ARISE wake-word feature is paused and is not included in this version.

## Safety

Desktop actions are restricted to predefined operations. Do not add unrestricted command execution without a separate permission and confirmation design.
