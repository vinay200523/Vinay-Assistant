import json, os, threading, subprocess, urllib.request, urllib.error, webbrowser, base64, io, uuid
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

ROOT = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.join(ROOT, "qwen2.5-3b-instruct-q4_k_m.gguf")
SERVER = os.path.join(ROOT, "runtime", "llama-server.exe")
LOG = os.path.join(ROOT, "server.log")
OUTPUTS = os.path.join(ROOT, "generated_images")
SD_ROOT = r"C:\AI\VinayAssistant\imagegen"
SD_CLI = os.path.join(SD_ROOT, "runtime", "sd-cli.exe")
SD_MODEL = os.path.join(SD_ROOT, "models", "v1-5-pruned_Q4_0.gguf")
SD_LOG = os.path.join(SD_ROOT, "image-generation.log")
os.makedirs(OUTPUTS, exist_ok=True)
HEALTH = "http://127.0.0.1:8080/health"
API = "http://127.0.0.1:8080/v1/chat/completions"
SYSTEM = ("You are Vinay Assistant, a helpful personal AI. Explain clearly, "
          "show steps when useful, and admit uncertainty. You run locally and are not ChatGPT.")
PORT = 8765

PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Vinay Assistant</title>
<style>
:root{color-scheme:dark;--bg:#212121;--panel:#171717;--panel2:#303030;--line:#414141;--muted:#aaa;--accent:#19a37a}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:#eee;font:15px "Segoe UI",Arial,sans-serif;height:100vh;display:flex;overflow:hidden}
.sidebar{width:250px;background:var(--panel);display:flex;flex-direction:column;padding:16px 12px;border-right:1px solid #292929;flex-shrink:0}
.logo{display:flex;align-items:center;gap:10px;font-size:18px;font-weight:700;padding:8px 10px 22px}.logo-mark{width:32px;height:32px;border-radius:11px;background:#e8e8e8;color:#151515;display:grid;place-items:center;font-size:20px}
.newchat{background:transparent;color:#eee;border:1px solid #555;border-radius:10px;padding:12px;text-align:left;font-size:14px;cursor:pointer}
.side-note{margin-top:auto;color:#888;font-size:12px;line-height:1.6;padding:12px}.app{flex:1;min-width:0;display:flex;flex-direction:column}
header{height:62px;display:flex;align-items:center;justify-content:space-between;padding:0 25px;border-bottom:1px solid #343434}
.brand{font-size:16px;font-weight:650}.status{font-size:12px;color:#a8cdb8}
main{flex:1;overflow:auto;width:100%;max-width:960px;margin:0 auto;padding:25px 26px 24px}
.welcome{margin:12vh auto 30px;text-align:center;max-width:620px}.welcome .spark{font-size:34px}.welcome h1{font-size:31px;font-weight:600;margin:14px 0 10px}.welcome p{color:#aaa;line-height:1.65}
.msg{padding:17px 20px;margin:14px 0;border-radius:16px;line-height:1.65;white-space:pre-wrap;overflow-wrap:anywhere}.user{background:#303030;margin-left:12%}.assistant{background:transparent;margin-right:5%}.who{font-size:12px;color:#9ec5fe;font-weight:700;margin-bottom:6px}.assistant .who{color:#9bd6a5}
.msg img{display:block;max-width:300px;max-height:240px;object-fit:contain;border-radius:10px;margin:8px 0}
.composer-wrap{padding:10px 22px 18px;background:linear-gradient(transparent,#212121 16%)}.composer{max-width:880px;margin:auto;background:#303030;border:1px solid #555;border-radius:22px;padding:10px 12px 9px;box-shadow:0 8px 28px #0003}
textarea{display:block;width:100%;resize:vertical;min-height:44px;max-height:150px;border:0;outline:0;background:transparent;color:white;font:15px "Segoe UI",Arial;padding:8px}
.composer-actions{display:flex;align-items:center;gap:8px;flex-wrap:wrap}.toolbtn{height:38px;min-width:38px;border:0;border-radius:50%;background:transparent;color:#ddd;font-size:19px;cursor:pointer}.toolbtn:hover{background:#454545}.toolbtn.recording{color:#ff7777;background:#4a2929}
.spacer{flex:1}.send,.action{height:36px;padding:0 14px;border:0;border-radius:18px;background:#eee;color:#171717;font-weight:650;cursor:pointer}.action{background:#454545;color:#eee}.send:disabled,.action:disabled{opacity:.5;cursor:wait}
.hint{max-width:880px;margin:8px auto 0;text-align:center;color:#858585;font-size:11px}
.preview{display:flex;gap:9px;padding:5px 8px 10px;flex-wrap:wrap}.preview-item{position:relative}.preview img{width:64px;height:64px;object-fit:cover;border-radius:9px;border:1px solid #666}.remove{position:absolute;right:-6px;top:-6px;border:0;border-radius:50%;background:#555;color:white;width:21px;height:21px;cursor:pointer}
#file{display:none}select{background:#454545;color:#eee;border:1px solid #666;border-radius:12px;padding:8px;max-width:150px}
.output-image{max-width:min(100%,640px);border-radius:12px;margin-top:12px;border:1px solid #555}.tiny{font-size:11px;color:#999}
@media(max-width:700px){.sidebar{width:58px;padding:12px 7px}.logo{padding:6px 5px 18px}.logo span:not(.logo-mark){display:none}.newchat{font-size:0;text-align:center;padding:11px 2px}.side-note{display:none}header{padding:0 14px}main{padding:18px 13px}.user{margin-left:3%}.assistant{margin-right:0}.welcome{margin-top:10vh}.welcome h1{font-size:25px}.composer-wrap{padding:8px 10px 14px}}
</style></head><body>
<aside class="sidebar"><div class="logo"><span class="logo-mark">*</span><span>Vinay Assistant</span></div><button class="newchat" id="newchat">+ &nbsp; New chat</button><div class="side-note">Personal AI on this laptop.<br>Local Qwen  |  Image tools  |  No paid API</div></aside>
<section class="app"><header><div class="brand">Vinay Assistant</div><div class="status" id="status">Connecting to local AI...</div></header>
<main id="chat"><div class="welcome" id="welcome"><div class="spark">*</div><h1>What can I help you with?</h1><p>Chat, upload a picture, analyze it, or create an image.</p></div></main>
<div class="composer-wrap"><div class="composer"><div class="preview" id="preview"></div>
<textarea id="prompt" rows="1" placeholder="Message Vinay Assistant..."></textarea>
<div class="composer-actions">
<button class="toolbtn" id="attach" title="Attach image">+</button><input id="file" type="file" accept="image/png,image/jpeg,image/webp" multiple><button class="action" id="docattach" title="Attach PDF, DOCX, TXT or Markdown">Attach document</button><input id="docfile" type="file" accept=".pdf,.docx,.txt,.md" style="display:none">
<button class="toolbtn" id="mic" title="Voice input">Mic</button>
<select id="operation" title="Image processing"><option value="enhance">Enhance</option><option value="grayscale">Grayscale</option><option value="sharpen">Sharpen</option><option value="blur">Soft blur</option><option value="edges">Edge map</option><option value="rotate">Rotate 90 deg</option><option value="thumbnail">Resize (max 1200px)</option></select>
<button class="action" id="process">Process image</button><button class="action" id="analyze">Analyze</button>
<span class="spacer"></span><select id="imageSize" title="Generated image resolution"><option value="512x512">512 square</option><option value="640x384">Landscape</option><option value="384x640">Portrait</option></select><button class="action" id="generate">Create image</button><button class="action" id="stopvoice">Stop voice</button><button class="action" id="export">Export chat</button><button class="send" id="send">Send </button>
</div></div><div class="hint" id="hint">Enter to send  |  Shift + Enter for a new line  |  Image analysis and generation run locally  |  CPU image generation may take several minutes</div></div>
</section>
<script>
const chat=document.getElementById('chat'),box=document.getElementById('prompt'),send=document.getElementById('send'),statusEl=document.getElementById('status'),fileInput=document.getElementById('file'),preview=document.getElementById('preview'),mic=document.getElementById('mic'),hint=document.getElementById('hint');
let history=[],attachments=[],recognition=null,busy=false;
function welcome(){chat.innerHTML='<div class="welcome" id="welcome"><div class="spark">*</div><h1>What can I help you with?</h1><p>Chat, upload a picture, analyze it, or create an image.</p></div>'}
function add(role,text,images=[]){document.getElementById('welcome')?.remove();const d=document.createElement('div');d.className='msg '+role;const who=document.createElement('div');who.className='who';who.textContent=role==='user'?'You':'Vinay Assistant';const body=document.createElement('div');body.textContent=text;d.append(who,body);images.forEach(src=>{const im=document.createElement('img');im.src=src;d.append(im)});if(role==='assistant'){const speak=document.createElement('button');speak.className='action';speak.textContent='Read aloud';speak.style.marginTop='10px';speak.onclick=()=>{if('speechSynthesis' in window){speechSynthesis.cancel();speechSynthesis.speak(new SpeechSynthesisUtterance(text))}};d.append(speak)}chat.append(d);chat.scrollTop=chat.scrollHeight;return d}
async function poll(){try{const r=await fetch('/status');const s=await r.json();if(!busy){statusEl.textContent=s.ready?'Local AI ready':'Starting local AI...';statusEl.style.color=s.ready?'#9bd6a5':'#f5c66b';document.getElementById('generate').disabled=!s.image_generation_available}}catch{if(!busy)statusEl.textContent='Connecting...'}setTimeout(poll,3000)}poll();
function renderPreview(){preview.innerHTML='';attachments.forEach((a,i)=>{const wrap=document.createElement('div');wrap.className='preview-item';const im=document.createElement('img');im.src=a.url;const b=document.createElement('button');b.className='remove';b.textContent='x';b.onclick=()=>{URL.revokeObjectURL(a.url);attachments.splice(i,1);renderPreview()};wrap.append(im,b);preview.append(wrap)})}
document.getElementById('attach').onclick=()=>fileInput.click();
document.getElementById('docattach').onclick=()=>document.getElementById('docfile').click();
document.getElementById('docfile').onchange=async e=>{const f=e.target.files[0];if(!f)return;if(f.size>8*1024*1024){hint.textContent='Document too large (8 MB maximum).';return}setBusy(true,'Reading document locally?');try{const b64=await new Promise((ok,no)=>{const r=new FileReader();r.onload=()=>ok(r.result);r.onerror=no;r.readAsDataURL(f)});const data=await postJSON('/read-document',{name:f.name,data:b64});history.push({role:'user',content:'I uploaded document '+f.name+'. Here is its extracted text. Use it as context for my next question:\n'+data.text});add('assistant','Document read locally: '+f.name+' ('+data.characters+' characters extracted). Now ask me questions about it.');hint.textContent='Document processed locally. Its text is now in this conversation context.'}catch(err){hint.textContent=err.message}finally{setBusy(false);e.target.value=''}};
document.getElementById('export').onclick=()=>{const blob=new Blob([history.map(m=>(m.role==='user'?'You':'Vinay Assistant')+':\n'+m.content).join('\n\n')],{type:'text/plain'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='vinay-assistant-chat.txt';a.click();URL.revokeObjectURL(a.href)};
document.getElementById('stopvoice').onclick=()=>{if('speechSynthesis' in window)speechSynthesis.cancel()};
fileInput.onchange=()=>{Array.from(fileInput.files||[]).forEach(f=>{if(f.type.startsWith('image/')&&attachments.length<4){const reader=new FileReader();reader.onload=()=>{attachments.push({file:f,url:URL.createObjectURL(f),data:reader.result});renderPreview()};reader.readAsDataURL(f)}});fileInput.value='';hint.textContent='Images attached. Press Send or Analyze to understand the photo, or Process image to edit it.'};
function setBusy(v,msg){busy=v;send.disabled=v;['process','analyze','generate'].forEach(id=>document.getElementById(id).disabled=v);statusEl.textContent=msg|| (v?'Working':'Checking local AI...')}
async function postJSON(path,payload){const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const data=await r.json();if(!r.ok)throw new Error(data.error||'Request failed');return data}
async function submit(){
 const text=box.value.trim();
 if((!text&&!attachments.length)||busy)return;
 if(attachments.length){
  const imageData=attachments[0].data;
  const imageUrls=attachments.map(a=>a.url);
  add('user',text||'Please analyze this image.',imageUrls);
  setBusy(true,'Checking image analysis...');
  try{
   const status=await fetch('/status').then(r=>r.json());
   if(!status.vision_available)throw new Error('The free local vision model is still loading. Your image is still attached; please try again shortly.');
   setBusy(true,'Analyzing image...');
   const data=await postJSON('/analyze-image',{image:imageData,prompt:text||'Describe this image and explain its important details.'});
   history.push({role:'user',content:'Image attached. '+(text||'Please analyze this image.')});
   history.push({role:'assistant',content:data.answer});
   add('assistant',data.answer);
   box.value='';
   attachments.forEach(a=>URL.revokeObjectURL(a.url));attachments=[];renderPreview();
   hint.textContent='Image analysis completed.';
  }catch(e){
   add('assistant','I could not analyze the image: '+e.message);
   hint.textContent=e.message;
  }finally{setBusy(false)}
  return;
 }
 box.value='';
 add('user',text);
 history.push({role:'user',content:text});
 setBusy(true,'Thinking...');
 try{
  const data=await postJSON('/chat',{messages:history});
  history.push({role:'assistant',content:data.answer});
  add('assistant',data.answer);
  setBusy(false);
 }catch(e){
  add('assistant','I could not respond: '+e.message);
  setBusy(false,'Connection issue');
 }
}
send.onclick=submit;box.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();submit()}});
document.getElementById('process').onclick=async()=>{if(!attachments.length){hint.textContent='Attach an image first.';return}setBusy(true,'Processing image...');try{const a=attachments[0],data=await postJSON('/process-image',{image:a.data,operation:document.getElementById('operation').value});const d=add('assistant','Image processed: '+data.operation);const im=document.createElement('img');im.className='output-image';im.src=data.image;im.alt='Processed image';d.append(im);const link=document.createElement('a');link.href=data.download;link.download='vinay-processed.png';link.textContent='Download processed image';link.style.display='block';link.style.color='#9bd6a5';d.append(link);hint.textContent='Processed image saved in the FreeAI/generated_images folder.'}catch(e){hint.textContent=e.message}finally{setBusy(false)}};
document.getElementById('analyze').onclick=async()=>{if(!attachments.length){hint.textContent='Attach an image first.';return}const prompt=box.value.trim()||'Describe this image and explain its important details.';add('user',prompt,[attachments[0].url]);history.push({role:'user',content:'Image attached. '+prompt});setBusy(true,'Analyzing image locally');try{const data=await postJSON('/analyze-image',{image:attachments[0].data,prompt});history.push({role:'assistant',content:data.answer});add('assistant',data.answer);hint.textContent='Image analysis completed locally. No API key or paid service used.';box.value=''}catch(e){add('assistant','I could not analyze the image: '+e.message);hint.textContent=e.message}finally{setBusy(false)}};
document.getElementById('generate').onclick=async()=>{const prompt=box.value.trim();if(!prompt){hint.textContent='Type a description of the image you want to create.';box.focus();return}add('user','Create an image: '+prompt);history.push({role:'user',content:'Create an image: '+prompt});setBusy(true,'Generating locally on CPU... this may take several minutes');try{const size=document.getElementById('imageSize').value;const data=await postJSON('/generate-image',{prompt,size});const d=add('assistant','Created image ('+data.size+') for: '+prompt);const im=document.createElement('img');im.className='output-image';im.src=data.image;im.alt='AI generated image';d.append(im);const link=document.createElement('a');link.href=data.download;link.download='vinay-generated.png';link.textContent='Download image';link.style.display='block';link.style.color='#9bd6a5';d.append(link);box.value=''}catch(e){add('assistant','Image generation failed: '+e.message);hint.textContent=e.message}finally{setBusy(false)}};
document.getElementById('newchat').onclick=()=>{history=[];attachments.forEach(a=>URL.revokeObjectURL(a.url));attachments=[];renderPreview();welcome();box.value='';hint.textContent='Enter to send  |  Shift + Enter for a new line';box.focus()};
const SpeechRecognition=window.SpeechRecognition||window.webkitSpeechRecognition;
if(SpeechRecognition){recognition=new SpeechRecognition();recognition.lang='en-IN';recognition.interimResults=true;recognition.continuous=false;recognition.onstart=()=>{mic.classList.add('recording');hint.textContent='Listening... speak now'};recognition.onresult=e=>{let t='';for(let i=e.resultIndex;i<e.results.length;i++)t+=e.results[i][0].transcript;box.value=box.value?box.value+' '+t:t};recognition.onerror=e=>{hint.textContent='Microphone: '+e.error+'. Check browser permission.'};recognition.onend=()=>{mic.classList.remove('recording');box.focus()};mic.onclick=()=>{try{mic.classList.contains('recording')?recognition.stop():recognition.start()}catch(e){hint.textContent='Microphone is busy. Try again.'}}}else{mic.onclick=()=>hint.textContent='Voice input is not supported in this browser. Use Chrome.'}
</script></body></html>"""

VISION_REPO = "ggml-org/Qwen2.5-VL-3B-Instruct-GGUF:Q4_K_M"

def server_started():
    try:
        with urllib.request.urlopen(HEALTH, timeout=2) as r: return r.status == 200
    except Exception: return False

def ready():
    try:
        with urllib.request.urlopen("http://127.0.0.1:8080/v1/models", timeout=3) as r:
            info = json.loads(r.read().decode("utf-8"))
        models = info.get("data", [])
        return any("image" in m.get("architecture", {}).get("input_modalities", []) for m in models)
    except Exception: return False

def start_model():
    if ready() or not os.path.exists(SERVER): return
    if server_started():
        try:
            with urllib.request.urlopen("http://127.0.0.1:8080/v1/models", timeout=3) as r:
                info = json.loads(r.read().decode("utf-8"))
            models = info.get("data", [])
            if any("image" in m.get("architecture", {}).get("input_modalities", []) for m in models):
                return
            subprocess.run(["taskkill", "/IM", "llama-server.exe", "/F"],
                           capture_output=True, text=True, timeout=10)
        except Exception:
            return
    log = open(os.path.join(ROOT, "vision-server.log"), "a", encoding="utf-8")
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    subprocess.Popen([SERVER, "-hf", VISION_REPO, "--host", "127.0.0.1", "--port", "8080", "-c", "2048", "-t", "8", "--no-mmproj-offload"],
                     cwd=os.path.join(ROOT, "runtime"), stdout=log, stderr=subprocess.STDOUT, creationflags=flags)

def decode_image(data_url):
    if not isinstance(data_url, str) or "," not in data_url or len(data_url) > 15_000_000:
        raise ValueError("Invalid image or image is too large (limit about 10 MB).")
    raw = base64.b64decode(data_url.split(",",1)[1])
    img = Image.open(io.BytesIO(raw))
    img.load()
    if img.width * img.height > 25_000_000: raise ValueError("Image dimensions are too large.")
    return img.convert("RGB")

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    def send_json(self, code, obj):
        raw = json.dumps(obj).encode()
        self.send_response(code); self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Content-Length",str(len(raw))); self.send_header("Cache-Control","no-store")
        self.end_headers(); self.wfile.write(raw)
    def do_GET(self):
        if self.path == "/":
            raw = PAGE.encode("utf-8"); self.send_response(200)
            self.send_header("Content-Type","text/html; charset=utf-8"); self.send_header("Content-Length",str(len(raw)))
            self.end_headers(); self.wfile.write(raw)
        elif self.path == "/status":
            vision_ready = ready()
            image_gen_ready = os.path.isfile(SD_CLI) and os.path.isfile(SD_MODEL) and os.path.getsize(SD_MODEL) >= 3_000_000_000
            self.send_json(200,{"ready":vision_ready,"vision_available":vision_ready,"image_generation_available":image_gen_ready})
        elif self.path.startswith("/images/"):
            name=os.path.basename(self.path)
            if name != self.path[len("/images/"):] or not name.endswith(".png"): self.send_error(404); return
            path=os.path.join(OUTPUTS,name)
            if not os.path.isfile(path): self.send_error(404); return
            self.send_response(200); self.send_header("Content-Type","image/png"); self.send_header("Content-Length",str(os.path.getsize(path))); self.end_headers()
            with open(path,"rb") as f: self.wfile.write(f.read())
        else: self.send_error(404)
    def do_POST(self):
        try:
            size=int(self.headers.get("Content-Length","0"))
            if size<=0 or size>16_000_000: self.send_json(413,{"error":"Request too large. Use an image smaller than 10 MB."}); return
            data=json.loads(self.rfile.read(size))
            if self.path == "/read-document":
                name=os.path.basename(str(data.get("name","document.txt")))
                raw=base64.b64decode(data.get("data","").split(",",1)[-1])
                if len(raw)>8*1024*1024: raise ValueError("Document exceeds 8 MB.")
                ext=os.path.splitext(name)[1].lower()
                if ext==".pdf":
                    from pypdf import PdfReader
                    reader=PdfReader(io.BytesIO(raw)); parts=[page.extract_text() or "" for page in reader.pages[:80]]; content="\n\n".join(parts)
                elif ext==".docx":
                    from docx import Document
                    doc=Document(io.BytesIO(raw)); content="\n".join(p.text for p in doc.paragraphs)+"\n"+"\n".join(" | ".join(c.text for c in row.cells) for table in doc.tables for row in table.rows)
                elif ext in (".txt",".md"): content=raw.decode("utf-8-sig",errors="replace")
                else: raise ValueError("Supported documents: PDF, DOCX, TXT and Markdown.")
                content=content[:100000]
                if not content.strip(): raise ValueError("No selectable text found. Scanned PDFs need OCR, which is not installed yet.")
                self.send_json(200,{"text":content,"characters":len(content)}); return
            if self.path == "/chat":
                if not ready(): self.send_json(503,{"error":"The local AI model is still starting. Please wait and try again."}); return
                msgs=data.get("messages",[])[-16:]
                payload={"model":"local-qwen","messages":[{"role":"system","content":SYSTEM}]+msgs,"stream":False,"temperature":0.7,"max_tokens":900}
                req=urllib.request.Request(API,data=json.dumps(payload).encode(),headers={"Content-Type":"application/json"})
                with urllib.request.urlopen(req,timeout=600) as response: result=json.loads(response.read().decode("utf-8"))
                self.send_json(200,{"answer":result["choices"][0]["message"]["content"]}); return
            if self.path == "/process-image":
                img=decode_image(data.get("image")); op=data.get("operation","enhance")
                if op=="grayscale": img=ImageOps.grayscale(img).convert("RGB")
                elif op=="sharpen": img=img.filter(ImageFilter.UnsharpMask(radius=2,percent=160,threshold=3))
                elif op=="blur": img=img.filter(ImageFilter.GaussianBlur(radius=2))
                elif op=="edges": img=img.filter(ImageFilter.FIND_EDGES)
                elif op=="rotate": img=img.rotate(90,expand=True)
                elif op=="thumbnail": img.thumbnail((1200,1200))
                else: img=ImageEnhance.Contrast(ImageEnhance.Sharpness(ImageOps.autocontrast(img)).enhance(1.25)).enhance(1.08)
                name="processed_"+uuid.uuid4().hex+".png"; path=os.path.join(OUTPUTS,name); img.save(path,"PNG")
                with open(path,"rb") as f: encoded=base64.b64encode(f.read()).decode()
                self.send_json(200,{"operation":op,"image":"data:image/png;base64,"+encoded,"download":"/images/"+name}); return
            if self.path == "/analyze-image":
                if not ready():
                    raise RuntimeError("The local vision model is not ready yet. Please wait for it to finish loading.")
                img=data.get("image","")
                if not isinstance(img,str) or not img.startswith("data:image/"):
                    raise ValueError("Please attach a valid image first.")
                prompt=data.get("prompt") or "Describe this image and explain its important details."
                payload={"model":"vinay-local-vision","messages":[{"role":"system","content":SYSTEM},{"role":"user","content":[{"type":"text","text":prompt},{"type":"image_url","image_url":{"url":img}}]}],"max_tokens":1000,"temperature":0.2}
                req=urllib.request.Request(API,data=json.dumps(payload).encode(),headers={"Content-Type":"application/json"})
                with urllib.request.urlopen(req,timeout=600) as response:
                    result=json.loads(response.read().decode("utf-8"))
                answer=result["choices"][0]["message"]["content"]
                self.send_json(200,{"answer":answer,"model":"local Qwen2.5-VL 3B"}); return
            if self.path == "/generate-image":
                prompt=str(data.get("prompt","")).strip()
                if not prompt or len(prompt)>3000: self.send_json(400,{"error":"Enter an image prompt (up to 3000 characters)."}); return
                if not os.path.isfile(SD_CLI) or not os.path.isfile(SD_MODEL) or os.path.getsize(SD_MODEL)<3_000_000_000:
                    self.send_json(503,{"error":"The free local image-generation model is still downloading or is not installed yet."}); return
                size=str(data.get("size","512x512"))
                dimensions={"512x512":(512,512),"640x384":(640,384),"384x640":(384,640)}
                if size not in dimensions: raise ValueError("Choose 512x512, 640x384, or 384x640.")
                width,height=dimensions[size]
                name="generated_"+uuid.uuid4().hex+".png"
                path=os.path.join(OUTPUTS,name)
                # The laptop has 16 GB RAM, so unload the vision model while the CPU image model runs.
                subprocess.run(["taskkill","/IM","llama-server.exe","/F"],capture_output=True,text=True,timeout=10)
                try:
                    cmd=[SD_CLI,"-m",SD_MODEL,"-p",prompt,"-o",path,"-W",str(width),"-H",str(height),
                         "--steps","8","--sampling-method","euler_a","--backend","cpu","-t","8","--rng","cpu"]
                    os.makedirs(SD_ROOT,exist_ok=True)
                    with open(SD_LOG,"a",encoding="utf-8") as log:
                        log.write("\n--- New local image generation ---\n")
                        result=subprocess.run(cmd,cwd=os.path.join(SD_ROOT,"runtime"),stdout=log,
                                              stderr=subprocess.STDOUT,text=True,timeout=2400)
                    if result.returncode!=0 or not os.path.isfile(path):
                        try:
                            with open(SD_LOG,"r",encoding="utf-8",errors="replace") as log:
                                detail="\n".join(log.readlines()[-35:])
                        except Exception: detail="No generation log available."
                        raise RuntimeError("Local image generation failed. "+detail[-1800:])
                    with open(path,"rb") as f: encoded=base64.b64encode(f.read()).decode()
                    self.send_json(200,{"image":"data:image/png;base64,"+encoded,"download":"/images/"+name,
                                        "size":f"{width}x{height}","model":"Stable Diffusion 1.5 Q4 (local CPU)"})
                finally:
                    start_model()
                return
            self.send_error(404)
        except urllib.error.HTTPError as e:
            try: detail=e.read().decode("utf-8")[:1200]
            except Exception: detail=str(e)
            self.send_json(e.code,{"error":"Image service error: "+detail})
        except Exception as e: self.send_json(500,{"error":str(e)})

def main():
    threading.Thread(target=start_model,daemon=True).start()
    httpd=ThreadingHTTPServer(("127.0.0.1",PORT),Handler)
    threading.Timer(1.2,lambda:webbrowser.open("http://127.0.0.1:"+str(PORT))).start()
    httpd.serve_forever()

if __name__=="__main__": main()


