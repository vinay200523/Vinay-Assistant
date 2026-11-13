# Vinay Assistant

A local-first desktop/web AI assistant prototype built with Python.

## Features
- Local text chat using a Qwen GGUF model through llama.cpp
- Local image understanding using Qwen2.5-VL through llama.cpp
- Basic image processing with Pillow
- Browser-based voice input where supported
- Local chat history and generated-image storage

## Requirements
- Windows 10/11
- Python 3.10+ (64-bit)
- llama.cpp Windows release containing llama-server.exe and its DLLs
- Internet connection for first-time model downloads

## Setup
1. Install Python and select Add Python to PATH.
2. Install dependencies: py -m pip install -r requirements.txt
3. Obtain a Windows llama.cpp release and place llama-server.exe plus its required DLLs in a folder named runtime beside webapp.py.
4. Run Run Assistant.bat.
5. The first launch may download model files and take several minutes.

## Run
Double-click Run Assistant.bat, or run: py launcher.py

## Important notes
- Large model weights are intentionally not included to avoid a multi-gigabyte ZIP and GitHub file-size limits.
- chat_history.json, logs, generated images, cached models, backups, and local runtime binaries are intentionally excluded.
- Image generation in the current local build depends on a separate Stable Diffusion setup at C:\AI\VinayAssistant\imagegen; that path is specific to the original development machine and must be configured for another computer.
- This is a development snapshot. Test and adjust dependencies/runtime paths on another PC before relying on it.
