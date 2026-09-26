const API = "";
let isLoading = false, sessionId = null;
const $ = id => document.getElementById(id);
const chatWindow = $("chat-window"), queryInput = $("query-input"), sendBtn = $("send-btn"),
      uploadZone = $("upload-zone"), fileInput = $("file-input"), uploadStatus = $("upload-status"),
      sourcesList = $("sources-list"), chatsList = $("chats-list");
const esc = s => String(s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
const trunc = (s,n) => s.length > n ? "…"+s.slice(-(n-1)) : s;

window.addEventListener("DOMContentLoaded", () => {
  checkHealth(); setInterval(checkHealth, 30000); initSession(); loadSessions();
  uploadZone.addEventListener("dragover", e => { e.preventDefault(); uploadZone.classList.add("dragover"); });
  uploadZone.addEventListener("dragleave", () => uploadZone.classList.remove("dragover"));
  uploadZone.addEventListener("drop", e => { e.preventDefault(); uploadZone.classList.remove("dragover"); handleFiles(e.dataTransfer.files); });
  fileInput.addEventListener("change", () => handleFiles(fileInput.files));
});

// Session
async function initSession() {
  try { sessionId = (await (await fetch(`${API}/api/session/new`, {method:"POST"})).json()).session_id; }
  catch { sessionId = crypto.randomUUID().slice(0,8); }
}
async function newSession() {
  await initSession(); clearChat();
  document.querySelectorAll("#chats-list li").forEach(el => el.classList.remove("active"));
  appendMsg("system-message", "⬡", `<p>Hello! I'm <strong>StudentRAG</strong>. Upload a PDF and ask me anything.</p>`);
  loadSessions();
}

async function loadSessions() {
  try {
    const {sessions=[]} = await fetch(`${API}/api/sessions`).then(r=>r.json());
    if (!chatsList) return;
    chatsList.innerHTML = sessions.length
      ? sessions.map(s=>`
        <li class="${s.session_id===sessionId?'active':''}" onclick="switchSession('${s.session_id}')" title="${esc(s.title)}">
          <svg class="chat-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          <span class="chat-title">${esc(s.title)}</span>
        </li>`).join("")
      : '<li class="chats-empty">No previous chats.</li>';
  } catch {}
}

async function switchSession(sid) {
  if (sessionId === sid) return;
  sessionId = sid; clearChat();
  document.querySelectorAll("#chats-list li").forEach(el => el.classList.toggle("active", el.getAttribute("onclick")?.includes(sid)));
  try {
    const {messages=[]} = await fetch(`${API}/api/session/${sid}/history`).then(r=>r.json());
    if (!messages.length) {
      appendMsg("system-message", "⬡", `<p>Empty session.</p>`);
    } else {
      for (const m of messages) {
        if (m.role === "human") appendMsg("user-message", "U", `<p>${esc(m.content)}</p>`);
        else appendMsg("bot-message", "⬡", `<div class="answer-block">${marked.parse(m.content)}</div>`);
      }
    }
  } catch(e) {
    appendMsg("system-message", "!", `<p>Failed to load session: ${esc(e.message)}</p>`);
  }
}

// Health
async function checkHealth() {
  try {
    const d = await fetch(`${API}/api/health`).then(r=>r.json());
    const el = $("status-chunks");
    if (el) el.textContent = (d.total_chunks??0).toLocaleString();
    if (d.collection_status==="ready") updateSources();
  } catch {}
}
async function updateSources() {
  try {
    const {sources=[]} = await fetch(`${API}/api/stats`).then(r=>r.json());
    sourcesList.innerHTML = sources.length
      ? sources.map(s=>`
        <li class="has-source" title="${esc(s)}">
          <svg class="file-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          <span class="file-name">${esc(trunc(s,24))}</span>
        </li>`).join("")
      : '<li class="sources-empty">No sources indexed yet.</li>';
  } catch {}
}

// Chat
function handleKeyDown(e) { if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();sendQuery();} }

async function sendQuery() {
  const q = queryInput.value.trim();
  if (!q||isLoading) return;
  appendMsg("user-message","U",`<p>${esc(q)}</p>`);
  queryInput.value=""; updateCharCount(queryInput); autoResize(queryInput); setLoading(true);
  const {messageDiv,answerBlock} = createStreamMsg();
  try {
    const res = await fetch(`${API}/api/query/stream`, {method:"POST", headers:{"Content-Type":"application/json"},
      body:JSON.stringify({question:q, top_k:5, min_score:0.1, session_id:sessionId})});
    if (!res.ok) throw new Error((await res.json()).detail||"API error");
    const reader=res.body.getReader(), dec=new TextDecoder(); let buf="",full="",meta=null;
    while(true) {
      const {done,value}=await reader.read(); if(done) break;
      buf+=dec.decode(value,{stream:true});
      const parts=buf.split("\n\n"); buf=parts.pop();
      for (const block of parts) {
        if(!block.trim()) continue;
        let ev="",data="";
        for(const ln of block.split("\n")){if(ln.startsWith("event:"))ev=ln.slice(6).trim();if(ln.startsWith("data:"))data=ln.slice(5).trim();}
        if(!ev||!data) continue;
        if(ev==="meta"){meta=JSON.parse(data); sessionId=meta.session_id||sessionId;}
        if(ev==="token"){full+=JSON.parse(data).token; answerBlock.innerHTML=marked.parse(full); scrollBot();}
        if(ev==="done"&&meta) finishStream(messageDiv,meta,JSON.parse(data),full);
        if(ev==="error"){answerBlock.classList.add("answer-not-found"); answerBlock.querySelector(".streaming-cursor")?.remove(); answerBlock.innerHTML=`<p>${esc(JSON.parse(data).detail)}</p>`;}
      }
    }
  } catch(e){answerBlock.classList.add("answer-not-found"); answerBlock.querySelector(".streaming-cursor")?.remove(); answerBlock.innerHTML=`<p>${esc(e.message)}</p>`;
  } finally{setLoading(false); scrollBot();}
}

function createStreamMsg() {
  const div=document.createElement("div"); div.className="message bot-message";
  div.innerHTML=`<div class="message-icon">⬡</div><div class="message-body"></div>`;
  const ab=document.createElement("div"); ab.className="answer-block streaming";
  const cur=document.createElement("span"); cur.className="streaming-cursor"; cur.textContent="▊";
  ab.appendChild(cur); div.querySelector(".message-body").appendChild(ab);
  chatWindow.appendChild(div); scrollBot();
  return {messageDiv:div, answerBlock:ab};
}

function finishStream(div,meta,done,full) {
  const body=div.querySelector(".message-body"), ab=body.querySelector(".answer-block");
  ab.classList.remove("streaming"); ab.querySelector(".streaming-cursor")?.remove();
  if(!done.answer_found) ab.classList.add("answer-not-found");
  ab.innerHTML=marked.parse(full);
  const src=(meta.sources||[]).map(s=>`<span class="source-tag">${esc(s)}</span>`).join("");
  if(src){const r=document.createElement("div"); r.className="sources-row"; r.innerHTML=src; body.appendChild(r);}
  scrollBot();
  loadSessions();
}

function appendMsg(cls,icon,html) {
  const d=document.createElement("div"); d.className=`message ${cls}`;
  d.innerHTML=`<div class="message-icon">${icon}</div><div class="message-body">${html}</div>`;
  chatWindow.appendChild(d); scrollBot();
}

function appendBotAnswer(data) {
  const src=(data.sources||[]).map(s=>`<span class="source-tag">${esc(s)}</span>`).join("");
  const d=document.createElement("div"); d.className="message bot-message";
  d.innerHTML=`<div class="message-icon">⬡</div><div class="message-body">
    <div class="answer-block ${data.answer_found?"":"answer-not-found"}">${marked.parse(data.answer)}</div>
    ${src?`<div class="sources-row">${src}</div>`:""}</div>`;
  chatWindow.appendChild(d); scrollBot();
}

// Upload
async function handleFiles(files) {
  if(!files?.length) return;
  const f=files[0];
  if(!f.name.toLowerCase().endsWith(".pdf")){showUpload("Only PDF supported.","error");return;}
  showUpload(`Uploading ${f.name}…`,"");
  const fd=new FormData(); fd.append("file",f);
  try {
    const r=await fetch(`${API}/api/upload-and-index`,{method:"POST",body:fd}), d=await r.json();
    if(!r.ok) throw new Error(d.detail);
    showUpload(`✓ ${f.name} uploaded. Indexing…`,"success");
    setTimeout(checkHealth,5000); setTimeout(checkHealth,15000);
  } catch(e){showUpload(`✗ ${e.message}`,"error");}
  fileInput.value="";
}
function showUpload(msg,type){uploadStatus.textContent=msg; uploadStatus.className=`upload-status ${type}`;}

// Utils
function setLoading(v){isLoading=v; sendBtn.disabled=v; $("send-icon").textContent=v?"…":"→";}
function scrollBot(){chatWindow.scrollTop=chatWindow.scrollHeight;}
function autoResize(el){el.style.height="auto"; el.style.height=Math.min(el.scrollHeight,140)+"px";}
function updateCharCount(el){const c=$("char-count"); if(c) c.textContent=`${el.value.length} / 1000`;}
function clearChat(){chatWindow.innerHTML="";}
