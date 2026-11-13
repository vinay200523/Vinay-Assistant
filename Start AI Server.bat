@echo off
cd /d "%~dp0runtime"
curl.exe -s http://127.0.0.1:8080/v1/models | findstr /i "image" >nul 2>&1
if %errorlevel%==0 (
  echo Local vision model is already running.
  exit /b 0
)
taskkill /IM llama-server.exe /F >nul 2>&1
start "Local Vision Server" /min llama-server.exe -hf ggml-org/Qwen2.5-VL-3B-Instruct-GGUF:Q4_K_M --host 127.0.0.1 --port 8080 -c 2048 -t 8 --no-mmproj-offload
echo Free local vision model is starting. Wait until Vinay Assistant shows Local AI ready.
