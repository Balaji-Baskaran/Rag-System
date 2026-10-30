let isLoading = false, chatHistory = [];
const $ = id => document.getElementById(id);
const chatWindow = $("chat-window"), queryInput = $("query-input"),
      sendBtn = $("send-btn"), sendIcon = $("send-icon"),
      uploadZone = $("upload-zone"), fileInput = $("file-input"),
      uploadStatus = $("upload-status"), sourcesList = $("sources-list"),
      chunksBadge = $("status-chunks"), charCount = $("char-count");
const esc = s => String(s || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const trunc = (s, n = 24) => s.length > n ? "…" + s.slice(-(n - 1)) : s;
const scrollBot = () => chatWindow.scrollTop = chatWindow.scrollHeight;
const showUpload = (m, t) => { uploadStatus.textContent = m; uploadStatus.className = `upload-status ${t}`; };

async function refreshState() {
  try {
    const [h, s] = await Promise.all([fetch("/api/health").then(r => r.json()), fetch("/api/stats").then(r => r.json())]);
    chunksBadge.textContent = (h.total_chunks ?? 0).toLocaleString();
    sourcesList.innerHTML = s.sources?.length
      ? s.sources.map(src => `<li class="has-source" title="${esc(src)}"><svg class="file-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg><span class="file-name">${esc(trunc(src))}</span></li>`).join("")
      : '<li class="sources-empty">No sources indexed yet.</li>';
  } catch {}
}
refreshState();
setInterval(refreshState, 30000);

async function handleFiles(files) {
  const f = files?.[0];
  if (!f) return;
  if (!f.name.toLowerCase().endsWith(".pdf")) return showUpload("Only PDF files supported.", "error");
  showUpload(`Uploading & indexing ${f.name}…`, "");
  const fd = new FormData();
  fd.append("file", f);
  try {
    const res = await fetch("/api/upload-and-index", { method: "POST", body: fd });
    if (!res.ok) throw new Error((await res.json()).detail);
    showUpload(`✓ ${f.name} indexed successfully.`, "success");
    refreshState();
  } catch (e) { showUpload(`✗ ${e.message}`, "error"); }
  fileInput.value = "";
}

async function sendQuery() {
  const q = queryInput.value.trim();
  if (!q || isLoading) return;
  appendMsg("user-message", "U", `<p>${esc(q)}</p>`);
  queryInput.value = "";
  autoResize(queryInput);

  const prevTurns = chatHistory.slice(-6);
  chatHistory.push({ role: "human", content: q });
  setLoading(true);

  const botDiv = appendMsg("bot-message", "⬡", `<div class="answer-block streaming">Thinking…</div>`);
  const answerBlock = botDiv.querySelector(".answer-block");
  let full = "", meta = null;

  try {
    const res = await fetch("/api/query/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: q, history: prevTurns })
    });
    if (!res.ok) throw new Error((await res.json()).detail || "API error");

    const reader = res.body.getReader(), dec = new TextDecoder();
    let buf = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      const parts = buf.split("\n\n");
      buf = parts.pop();
      for (const block of parts) {
        if (!block.trim()) continue;
        const ev = block.match(/event:\s*(\w+)/)?.[1], data = block.match(/data:\s*(.+)/)?.[1];
        if (!ev || !data) continue;
        const p = JSON.parse(data);
        if (ev === "meta") meta = p;
        if (ev === "token") { full += p.token; answerBlock.innerHTML = marked.parse(full); scrollBot(); }
        if (ev === "error") throw new Error(p.detail || "Stream error");
      }
    }
    chatHistory.push({ role: "ai", content: full });
    if (meta?.sources?.length) {
      botDiv.querySelector(".message-body").insertAdjacentHTML("beforeend", `<div class="sources-row">${meta.sources.map(s => `<span class="source-tag">${esc(s)}</span>`).join("")}</div>`);
    }
  } catch (e) {
    answerBlock.classList.add("answer-not-found");
    answerBlock.innerHTML = `<p>${esc(e.message)}</p>`;
  } finally {
    answerBlock.classList.remove("streaming");
    setLoading(false);
    scrollBot();
  }
}

function appendMsg(cls, icon, html) {
  const d = document.createElement("div");
  d.className = `message ${cls}`;
  d.innerHTML = `<div class="message-icon">${icon}</div><div class="message-body">${html}</div>`;
  chatWindow.appendChild(d);
  scrollBot();
  return d;
}

function clearChat() {
  chatWindow.innerHTML = "";
  chatHistory = [];
  fetch("/api/chat/clear", { method: "POST" }).catch(() => {});
  appendMsg("system-message", "⬡", "<p>Hello! I'm <strong>StudentRAG</strong>. Upload a PDF and ask me anything. You can also ask follow-up questions!</p>");
}

function setLoading(v) { isLoading = v; sendBtn.disabled = v; sendIcon.textContent = v ? "…" : "→"; }
function autoResize(el) { el.style.height = "auto"; el.style.height = Math.min(el.scrollHeight, 140) + "px"; charCount.textContent = `${el.value.length} / 1000`; }
function handleKeyDown(e) { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendQuery(); } }

uploadZone.ondragover = e => { e.preventDefault(); uploadZone.classList.add("dragover"); };
uploadZone.ondragleave = () => uploadZone.classList.remove("dragover");
uploadZone.ondrop = e => { e.preventDefault(); uploadZone.classList.remove("dragover"); handleFiles(e.dataTransfer.files); };
fileInput.onchange = () => handleFiles(fileInput.files);