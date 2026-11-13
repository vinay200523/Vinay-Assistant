import json
import os
import urllib.request
import urllib.error

API = "http://127.0.0.1:8080/v1/chat/completions"
HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chat_history.json")
SYSTEM = ("You are a helpful, accurate personal AI assistant. Explain clearly, "
         "show steps when useful, and admit uncertainty. Do not claim to be ChatGPT.")

def load_history():
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []

def save_history(messages):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(messages[-40:], f, ensure_ascii=False, indent=2)

def ask(messages):
    payload = {"model": "local-qwen", "messages": [{"role": "system", "content": SYSTEM}] + messages[-16:],
               "stream": False, "temperature": 0.7, "max_tokens": 900}
    req = urllib.request.Request(API, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as response:
        result = json.loads(response.read().decode("utf-8"))
    return result["choices"][0]["message"]["content"]

def main():
    messages = load_history()
    print("\n=== MY FREE LOCAL AI ===")
    print("Model: Qwen 2.5 3B | Runs on this laptop | Type /help or /exit")
    print("Chat history is saved locally in chat_history.json.\n")
    while True:
        try:
            prompt = input("You: ").strip()
            if not prompt:
                continue
            if prompt.lower() in ("/exit", "/quit"):
                print("Chat saved. Goodbye!")
                break
            if prompt.lower() == "/help":
                print("Commands: /help, /clear, /exit")
                continue
            if prompt.lower() == "/clear":
                messages = []
                save_history(messages)
                print("Conversation cleared.\n")
                continue
            messages.append({"role": "user", "content": prompt})
            print("\nAI: ", end="", flush=True)
            answer = ask(messages)
            print(answer, "\n")
            messages.append({"role": "assistant", "content": answer})
            save_history(messages)
        except urllib.error.URLError:
            print("\nAI server is not running. Double-click Start AI Server.bat, wait 20 seconds, then try again.\n")
        except KeyboardInterrupt:
            print("\nChat interrupted.")
            break
        except Exception as exc:
            print("\nError:", exc)

if __name__ == "__main__":
    main()
