import json, os, sys, time, threading, subprocess, urllib.request, urllib.error, tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText

ROOT = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.join(ROOT, "qwen2.5-3b-instruct-q4_k_m.gguf")
SERVER = os.path.join(ROOT, "runtime", "llama-server.exe")
LOG = os.path.join(ROOT, "server.log")
HISTORY = os.path.join(ROOT, "chat_history.json")
HEALTH = "http://127.0.0.1:8080/health"
API = "http://127.0.0.1:8080/v1/chat/completions"
SYSTEM = ("You are a helpful, accurate personal AI assistant. Explain clearly, "
          "show steps when useful, and admit uncertainty. You are a local AI, not ChatGPT.")
messages = []
busy = False

def load_history():
    try:
        with open(HISTORY, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []

def save_history():
    try:
        with open(HISTORY, "w", encoding="utf-8") as f:
            json.dump(messages[-40:], f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def ready():
    try:
        with urllib.request.urlopen(HEALTH, timeout=2) as r:
            return r.status == 200
    except Exception:
        return False

def ask(history):
    payload = {"model":"local-qwen", "messages":[{"role":"system","content":SYSTEM}] + history[-16:],
               "stream":False, "temperature":0.7, "max_tokens":900}
    req = urllib.request.Request(API, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=600) as response:
        result = json.loads(response.read().decode("utf-8"))
    return result["choices"][0]["message"]["content"]

root = tk.Tk()
root.title("My AI Assistant")
root.geometry("900x700")
root.minsize(650, 500)
root.configure(bg="#202123")

header = tk.Frame(root, bg="#202123", padx=18, pady=13)
header.pack(fill="x")
tk.Label(header, text="My AI Assistant", bg="#202123", fg="#f4f4f5",
         font=("Segoe UI", 17, "bold")).pack(side="left")
status = tk.Label(header, text="Starting AI model…", bg="#202123", fg="#f5c66b",
                  font=("Segoe UI", 9))
status.pack(side="right")

chat = ScrolledText(root, wrap="word", state="disabled", bg="#343541", fg="#ececf1",
                    insertbackground="white", relief="flat", borderwidth=0,
                    padx=22, pady=18, font=("Segoe UI", 11), spacing1=5, spacing3=10)
chat.pack(fill="both", expand=True, padx=14, pady=(0,10))
chat.tag_config("you", foreground="#8ab4f8", font=("Segoe UI", 10, "bold"))
chat.tag_config("ai", foreground="#9bd6a5", font=("Segoe UI", 10, "bold"))
chat.tag_config("body", foreground="#ececf1", font=("Segoe UI", 11))
chat.tag_config("muted", foreground="#a1a1aa", font=("Segoe UI", 9))

def add_message(who, text):
    chat.configure(state="normal")
    chat.insert("end", who + "\n", "you" if who == "You" else "ai")
    chat.insert("end", text.strip() + "\n\n", "body")
    chat.configure(state="disabled")
    chat.see("end")

def show_welcome():
    chat.configure(state="normal")
    chat.insert("end", "Welcome! Your local AI assistant is ready.\n", "ai")
    chat.insert("end", "Ask a question below to start chatting. Your chat history is saved on this laptop.\n\n", "body")
    for m in messages:
        if m.get("role") == "user":
            chat.insert("end", "You\n", "you")
        elif m.get("role") == "assistant":
            chat.insert("end", "AI\n", "ai")
        else:
            continue
        chat.insert("end", m.get("content","") + "\n\n", "body")
    chat.configure(state="disabled")
    chat.see("end")

def set_busy(value, message=None):
    global busy
    busy = value
    send_btn.configure(state=("disabled" if value else "normal"))
    entry.configure(state=("disabled" if value else "normal"))
    status.configure(text=message or ("Thinking…" if value else "Ready"),
                     fg="#f5c66b" if value else "#9bd6a5")

def send_message(event=None):
    global messages
    if busy:
        return "break"
    prompt = entry.get().strip()
    if not prompt or prompt == PLACEHOLDER:
        return "break"
    entry.delete(0, "end")
    add_message("You", prompt)
    messages.append({"role":"user","content":prompt})
    save_history()
    set_busy(True, "Thinking…")
    threading.Thread(target=reply_worker, daemon=True).start()
    return "break"

def reply_worker():
    try:
        answer = ask(messages.copy())
        messages.append({"role":"assistant","content":answer})
        save_history()
        root.after(0, lambda: add_message("AI", answer))
        root.after(0, lambda: set_busy(False, "Ready"))
    except Exception as e:
        root.after(0, lambda: add_message("AI", "I couldn't get a response. Please try again. Details: " + str(e)))
        root.after(0, lambda: set_busy(False, "Connection issue"))

def clear_chat():
    global messages
    if messagebox.askyesno("Clear conversation", "Delete the saved conversation on this laptop?"):
        messages = []
        save_history()
        chat.configure(state="normal")
        chat.delete("1.0", "end")
        chat.configure(state="disabled")
        add_message("AI", "Conversation cleared. What would you like to discuss?")

controls = tk.Frame(root, bg="#202123", padx=14, pady=12)
controls.pack(fill="x")
PLACEHOLDER = "Ask anything?"
entry = tk.Entry(controls, bg="#40414f", fg="#b8b8c5", insertbackground="white",
                 relief="flat", font=("Segoe UI", 12), borderwidth=0)
entry.insert(0, PLACEHOLDER)
entry.pack(side="left", fill="x", expand=True, ipady=13, padx=(0,10))
def entry_focus_in(event):
    if entry.get() == PLACEHOLDER:
        entry.delete(0, "end")
        entry.configure(fg="#ffffff")
def entry_focus_out(event):
    if not entry.get().strip():
        entry.insert(0, PLACEHOLDER)
        entry.configure(fg="#b8b8c5")
entry.bind("<FocusIn>", entry_focus_in)
entry.bind("<FocusOut>", entry_focus_out)
entry.bind("<Return>", send_message)
send_btn = tk.Button(controls, text="Send", command=send_message, bg="#19a37a",
                     fg="white", activebackground="#168866", activeforeground="white",
                     relief="flat", padx=20, pady=10, font=("Segoe UI", 10, "bold"), cursor="hand2")
send_btn.pack(side="left")
clear_btn = tk.Button(controls, text="Clear chat", command=clear_chat, bg="#40414f",
                      fg="#eeeeee", relief="flat", padx=12, pady=10, font=("Segoe UI", 9), cursor="hand2")
clear_btn.pack(side="left", padx=(8,0))
tk.Label(root, text="Local AI • Qwen 2.5 3B • Runs on this laptop",
         bg="#202123", fg="#8e8ea0", font=("Segoe UI", 8)).pack(pady=(0,8))

messages = load_history()
show_welcome()
entry.focus_set()

def startup_worker():
    try:
        if not ready():
            if not os.path.exists(SERVER) or not os.path.exists(MODEL):
                raise FileNotFoundError("The AI model or server files are missing from the FreeAI folder.")
            log = open(LOG, "a", encoding="utf-8")
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            subprocess.Popen([SERVER, "-m", MODEL, "--host", "127.0.0.1",
                              "--port", "8080", "-c", "4096", "-t", "8"],
                             cwd=os.path.join(ROOT, "runtime"), stdout=log,
                             stderr=subprocess.STDOUT, creationflags=flags)
            for _ in range(180):
                if ready():
                    break
                time.sleep(1)
            else:
                raise RuntimeError("The model took too long to start. Please close and reopen the app.")
        root.after(0, lambda: status.configure(text="Ready", fg="#9bd6a5"))
    except Exception as e:
        root.after(0, lambda: status.configure(text="Couldn't start", fg="#ff8a8a"))
        root.after(0, lambda: messagebox.showerror("AI startup problem", str(e)))

threading.Thread(target=startup_worker, daemon=True).start()
root.mainloop()
