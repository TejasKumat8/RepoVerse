// ==========================================================================
// RepoMind AI — Frontend Application Logic (with Stretch Features)
// ==========================================================================

document.addEventListener("DOMContentLoaded", () => {
  // State variables
  let currentRepoId = null;
  let currentSummary = null;
  let activeTab = "chatTab";
  let historyLogs = [];

  // DOM Elements
  const repoUrlInput = document.getElementById("repoUrlInput");
  const importBtn = document.getElementById("importBtn");
  const heroRepoUrlInput = document.getElementById("heroRepoUrlInput");
  const heroImportBtn = document.getElementById("heroImportBtn");
  
  const welcomeView = document.getElementById("welcomeView");
  const processingView = document.getElementById("processingView");
  const activeRepoBadge = document.getElementById("activeRepoBadge");
  const activeRepoName = document.getElementById("activeRepoName");
  
  const chatMessages = document.getElementById("chatMessages");
  const chatInput = document.getElementById("chatInput");
  const sendChatBtn = document.getElementById("sendChatBtn");
  const exportChatBtn = document.getElementById("exportChatBtn");
  const llmProviderSelect = document.getElementById("llmProviderSelect");

  const settingsBtn = document.getElementById("settingsBtn");
  const settingsModal = document.getElementById("settingsModal");
  const closeSettingsBtn = document.getElementById("closeSettingsBtn");
  const saveSettingsBtn = document.getElementById("saveSettingsBtn");
  
  const settingsGhToken = document.getElementById("settingsGhToken");
  const settingsGeminiKey = document.getElementById("settingsGeminiKey");
  const settingsOpenAIKey = document.getElementById("settingsOpenAIKey");
  const settingsGroqKey = document.getElementById("settingsGroqKey");

  const codeModal = document.getElementById("codeModal");
  const closeModalBtn = document.getElementById("closeModalBtn");
  const modalFileName = document.getElementById("modalFileName");
  const modalCodeSnippet = document.getElementById("modalCodeSnippet");

  const generateReadmeBtn = document.getElementById("generateReadmeBtn");
  const auditRepoBtn = document.getElementById("auditRepoBtn");
  const readmeModal = document.getElementById("readmeModal");
  const closeReadmeBtn = document.getElementById("closeReadmeBtn");
  const readmeContent = document.getElementById("readmeContent");

  // Load Saved Settings from LocalStorage
  const savedGhToken = localStorage.getItem("repomind_gh_token") || "";
  const savedGeminiKey = localStorage.getItem("repomind_gemini_key") || "";
  const savedOpenAIKey = localStorage.getItem("repomind_openai_key") || "";
  const savedGroqKey = localStorage.getItem("repomind_groq_key") || "";

  if (settingsGhToken) settingsGhToken.value = savedGhToken;
  if (settingsGeminiKey) settingsGeminiKey.value = savedGeminiKey;
  if (settingsOpenAIKey) settingsOpenAIKey.value = savedOpenAIKey;
  if (settingsGroqKey) settingsGroqKey.value = savedGroqKey;

  // Configure Marked markdown renderer
  marked.setOptions({
    highlight: function(code, lang) {
      if (lang && hljs.getLanguage(lang)) {
        return hljs.highlight(code, { language: lang }).value;
      }
      return hljs.highlightAuto(code).value;
    },
    breaks: true
  });

  // Configure Mermaid.js
  mermaid.initialize({ startOnLoad: false, theme: 'dark' });

  // --------------------------------------------------------------------------
  // Tab Switching
  // --------------------------------------------------------------------------
  document.querySelectorAll(".nav-tab").forEach(tab => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".nav-tab").forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      
      const targetTab = tab.getAttribute("data-tab");
      activeTab = targetTab;

      document.querySelectorAll(".tab-content").forEach(c => c.classList.add("hidden"));
      const activeEl = document.getElementById(targetTab);
      if (activeEl) activeEl.classList.remove("hidden");

      if (targetTab === "diagramTab" && currentRepoId) {
        renderArchitectureDiagram();
      }
    });
  });

  // Sample buttons click
  document.querySelectorAll(".sample-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const url = btn.getAttribute("data-url");
      heroRepoUrlInput.value = url;
      triggerImport(url);
    });
  });

  // Prompt chips click
  document.addEventListener("click", (e) => {
    if (e.target.classList.contains("chip-btn") || e.target.closest(".chip-btn")) {
      const chip = e.target.classList.contains("chip-btn") ? e.target : e.target.closest(".chip-btn");
      const question = chip.innerText.trim();
      chatInput.value = question;
      handleSendMessage();
    }
  });

  // --------------------------------------------------------------------------
  // Import Repository Event Handlers
  // --------------------------------------------------------------------------
  importBtn.addEventListener("click", () => triggerImport(repoUrlInput.value));
  heroImportBtn.addEventListener("click", () => triggerImport(heroRepoUrlInput.value));

  repoUrlInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") triggerImport(repoUrlInput.value);
  });

  heroRepoUrlInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") triggerImport(heroRepoUrlInput.value);
  });

  async function triggerImport(url) {
    if (!url || !url.trim()) {
      alert("Please enter a valid GitHub repository URL or slug (e.g., owner/repo).");
      return;
    }

    welcomeView.classList.add("hidden");
    processingView.classList.remove("hidden");

    try {
      const payload = {
        url: url.trim(),
        github_token: localStorage.getItem("repomind_gh_token") || null
      };

      const res = await fetch("/api/repo/import", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to import repository.");

      currentRepoId = data.repo_id;
      currentSummary = data.summary;

      // Update Header Badge
      activeRepoName.innerText = `${data.summary.owner}/${data.summary.repo}`;
      activeRepoBadge.classList.remove("hidden");

      // Update Overview Tab
      renderRepoSummary(data.summary);

      // Switch to Chat Tab
      processingView.classList.add("hidden");
      document.querySelector('[data-tab="chatTab"]').click();

      // Log to history
      historyLogs.unshift({
        time: new Date().toLocaleTimeString(),
        repo: `${data.summary.owner}/${data.summary.repo}`,
        action: `Imported repository (${data.summary.total_files} files indexed)`
      });
      renderHistory();

    } catch (err) {
      processingView.classList.add("hidden");
      welcomeView.classList.remove("hidden");
      alert("Error: " + err.message);
    }
  }

  // --------------------------------------------------------------------------
  // AI Chat Logic
  // --------------------------------------------------------------------------
  sendChatBtn.addEventListener("click", handleSendMessage);
  chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  });

  async function handleSendMessage() {
    const question = chatInput.value.trim();
    if (!question) return;

    if (!currentRepoId) {
      alert("Please import a GitHub repository first!");
      return;
    }

    appendChatMessage("user", question);
    chatInput.value = "";

    const botMsgId = "msg-" + Date.now();
    appendChatMessage("assistant", "<i class='fa-solid fa-spinner fa-spin'></i> Analyzing codebase and vector chunks...", botMsgId);

    try {
      const selectedProvider = llmProviderSelect.value;
      let apiKey = null;
      if (selectedProvider === "gemini") apiKey = localStorage.getItem("repomind_gemini_key");
      else if (selectedProvider === "openai") apiKey = localStorage.getItem("repomind_openai_key");
      else if (selectedProvider === "groq") apiKey = localStorage.getItem("repomind_groq_key");

      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          repo_id: currentRepoId,
          query: question,
          api_provider: selectedProvider,
          api_key: apiKey
        })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to generate answer.");

      updateChatMessage(botMsgId, data.answer, data.citations);

      historyLogs.unshift({
        time: new Date().toLocaleTimeString(),
        repo: currentRepoId,
        action: `Asked: "${question}"`
      });
      renderHistory();

    } catch (err) {
      updateChatMessage(botMsgId, "❌ Error generating response: " + err.message);
    }
  }

  function appendChatMessage(sender, htmlContent, id = null) {
    const msgDiv = document.createElement("div");
    msgDiv.className = `chat-message ${sender}-message`;
    if (id) msgDiv.id = id;

    const icon = sender === "user" ? "fa-user" : "fa-brain";
    msgDiv.innerHTML = `
      <div class="avatar"><i class="fa-solid ${icon}"></i></div>
      <div class="message-body">${htmlContent}</div>
    `;

    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function updateChatMessage(msgId, markdownText, citations = []) {
    const msgDiv = document.getElementById(msgId);
    if (!msgDiv) return;

    let parsedHtml = marked.parse(markdownText);

    if (citations && citations.length > 0) {
      citations.forEach(c => {
        const targetStr = `${c.file_path}:L${c.start_line}-L${c.end_line}`;
        const badgeHtml = `<button class="code-citation-badge" onclick="openFilePreview('${c.file_path}')"><i class="fa-solid fa-code"></i> ${targetStr}</button>`;
        parsedHtml = parsedHtml.replace(targetStr, badgeHtml);
      });
    }

    msgDiv.querySelector(".message-body").innerHTML = parsedHtml;
    hljs.highlightAll();
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  // Export Chat to Markdown File
  exportChatBtn.addEventListener("click", () => {
    const messages = chatMessages.querySelectorAll(".chat-message");
    let exportText = `# RepoMind AI Chat Session Export\n**Repository**: ${currentRepoId || 'N/A'}\n**Date**: ${new Date().toLocaleString()}\n\n---\n\n`;
    
    messages.forEach(msg => {
      const sender = msg.classList.contains("user-message") ? "**User**" : "**RepoMind AI**";
      const text = msg.querySelector(".message-body").innerText;
      exportText += `${sender}:\n${text}\n\n---\n\n`;
    });

    const blob = new Blob([exportText], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `repomind-chat-${currentRepoId || 'export'}.md`;
    a.click();
    URL.revokeObjectURL(url);
  });

  // --------------------------------------------------------------------------
  // Repository Intelligence & Folder Tree
  // --------------------------------------------------------------------------
  function renderRepoSummary(summary) {
    document.getElementById("statFiles").innerText = summary.total_files;
    document.getElementById("statLines").innerText = summary.total_lines.toLocaleString();
    document.getElementById("statBranch").innerText = summary.branch;

    const badgesContainer = document.getElementById("techStackBadges");
    badgesContainer.innerHTML = "";
    if (summary.tech_stack && summary.tech_stack.length > 0) {
      summary.tech_stack.forEach(tech => {
        const span = document.createElement("span");
        span.className = "badge";
        span.innerText = tech;
        badgesContainer.appendChild(span);
      });
    } else {
      badgesContainer.innerHTML = "<span class='hint-text'>Standard Code Base</span>";
    }

    const entryList = document.getElementById("entryPointsList");
    entryList.innerHTML = "";
    if (summary.entry_points && summary.entry_points.length > 0) {
      summary.entry_points.forEach(ep => {
        const item = document.createElement("div");
        item.className = "entry-item";
        item.innerHTML = `<span><i class="fa-solid fa-file"></i> ${ep.path}</span> <span class="badge">${ep.language}</span>`;
        item.onclick = () => openFilePreview(ep.path);
        entryList.appendChild(item);
      });
    } else {
      entryList.innerHTML = "<span class='hint-text'>No standard entry files found.</span>";
    }

    const treeContainer = document.getElementById("folderTreeContainer");
    treeContainer.innerHTML = renderTreeNodes(summary.folder_tree);
  }

  function renderTreeNodes(nodes) {
    if (!nodes || nodes.length === 0) return "";
    let html = "<div>";
    nodes.forEach(node => {
      if (node.type === "directory") {
        html += `
          <div class="tree-item">
            <span class="tree-folder-title"><i class="fa-solid fa-folder-open"></i> ${node.name}</span>
            <div style="padding-left: 1rem;">${renderTreeNodes(node.children)}</div>
          </div>
        `;
      } else {
        html += `
          <div class="tree-item tree-file-item" onclick="openFilePreview('${node.path}')">
            <i class="fa-solid fa-file-lines"></i> ${node.name}
          </div>
        `;
      }
    });
    html += "</div>";
    return html;
  }

  // --------------------------------------------------------------------------
  // STRETCH FEATURES: Auto-Generate README & Audit Codebase
  // --------------------------------------------------------------------------
  generateReadmeBtn.addEventListener("click", async () => {
    if (!currentRepoId) return alert("Please import a repository first!");
    readmeContent.innerText = "Generating README.md...";
    readmeModal.classList.remove("hidden");

    try {
      const res = await fetch("/api/generate-readme", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_id: currentRepoId })
      });
      const data = await res.json();
      readmeContent.innerText = data.readme;
      hljs.highlightElement(readmeContent);
    } catch (err) {
      readmeContent.innerText = "Error generating README: " + err.message;
    }
  });

  closeReadmeBtn.addEventListener("click", () => readmeModal.classList.add("hidden"));

  auditRepoBtn.addEventListener("click", async () => {
    if (!currentRepoId) return alert("Please import a repository first!");
    const auditCard = document.getElementById("auditCard");
    const auditResults = document.getElementById("auditResults");
    auditCard.classList.remove("hidden");
    auditResults.innerHTML = "<p class='hint-text'><i class='fa-solid fa-spinner fa-spin'></i> Auditing codebase for complex files & TODO markers...</p>";

    try {
      const res = await fetch("/api/audit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_id: currentRepoId })
      });
      const data = await res.json();

      let html = `<p><strong>Identified ${data.bug_prone_files.length} High-Complexity Files:</strong></p><ul style='margin-bottom:1rem; padding-left:1.2rem;'>`;
      data.bug_prone_files.forEach(f => {
        html += `<li><strong style='color:var(--primary-cyan);'>${f.file_path}</strong> - <span class='badge'>${f.risk_level} RISK</span>: ${f.reason}</li>`;
      });
      html += `</ul><p><strong>Found ${data.todo_count} TODO/FIXME Markers in Code:</strong></p><ul style='padding-left:1.2rem;'>`;
      data.todos.forEach(t => {
        html += `<li><code>${t.file_path}:L${t.line}</code>: ${escapeHtml(t.snippet)}</li>`;
      });
      html += "</ul>";

      auditResults.innerHTML = html;
    } catch (err) {
      auditResults.innerHTML = `<p class='hint-text' style='color:red;'>Audit failed: ${err.message}</p>`;
    }
  });

  // --------------------------------------------------------------------------
  // File Code Preview Modal
  // --------------------------------------------------------------------------
  window.openFilePreview = async function(filePath) {
    if (!currentRepoId) return;

    modalFileName.innerText = filePath;
    modalCodeSnippet.innerText = "Loading file content...";
    codeModal.classList.remove("hidden");

    try {
      const res = await fetch(`/api/repo/file/${currentRepoId}?file_path=${encodeURIComponent(filePath)}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Could not read file.");

      modalCodeSnippet.innerText = data.content;
      hljs.highlightElement(modalCodeSnippet);
    } catch (err) {
      modalCodeSnippet.innerText = "Error: " + err.message;
    }
  };

  closeModalBtn.addEventListener("click", () => {
    codeModal.classList.add("hidden");
  });

  // --------------------------------------------------------------------------
  // Semantic Vector Search
  // --------------------------------------------------------------------------
  const execSearchBtn = document.getElementById("execSearchBtn");
  const semanticQueryInput = document.getElementById("semanticQueryInput");
  const searchResultsList = document.getElementById("searchResultsList");

  execSearchBtn.addEventListener("click", performSemanticSearch);
  semanticQueryInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") performSemanticSearch();
  });

  async function performSemanticSearch() {
    const query = semanticQueryInput.value.trim();
    if (!query || !currentRepoId) return;

    searchResultsList.innerHTML = "<p class='hint-text'><i class='fa-solid fa-spinner fa-spin'></i> Searching vector store...</p>";

    try {
      const res = await fetch("/api/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_id: currentRepoId, query: query, top_k: 6 })
      });
      const data = await res.json();

      searchResultsList.innerHTML = "";
      if (!data.results || data.results.length === 0) {
        searchResultsList.innerHTML = "<p class='hint-text'>No matching code chunks found.</p>";
        return;
      }

      data.results.forEach(res => {
        const card = document.createElement("div");
        card.className = "card overview-card";
        card.style.marginBottom = "1rem";
        card.innerHTML = `
          <div style="display:flex; justify-content:space-between; margin-bottom:0.5rem;">
            <span class="code-citation-badge" onclick="openFilePreview('${res.file_path}')">
              <i class="fa-solid fa-code"></i> ${res.file_path} (Lines ${res.start_line}-${res.end_line})
            </span>
            <span class="badge">Relevancy: ${(res.score * 100).toFixed(1)}%</span>
          </div>
          <pre><code class="language-${res.language.toLowerCase()}">${escapeHtml(res.content)}</code></pre>
        `;
        searchResultsList.appendChild(card);
      });
      hljs.highlightAll();

    } catch (err) {
      searchResultsList.innerHTML = `<p class='hint-text' style='color:red;'>Search failed: ${err.message}</p>`;
    }
  }

  // --------------------------------------------------------------------------
  // Mermaid Architecture Diagram Generator
  // --------------------------------------------------------------------------
  async function renderArchitectureDiagram() {
    if (!currentRepoId) return;
    try {
      const res = await fetch("/api/diagram", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_id: currentRepoId })
      });
      const data = await res.json();

      const container = document.getElementById("mermaidViewer");
      container.innerHTML = `<div class="mermaid">${data.mermaid}</div>`;
      mermaid.contentLoaded();
    } catch (err) {
      console.error(err);
    }
  }

  // --------------------------------------------------------------------------
  // Settings Modal Handlers
  // --------------------------------------------------------------------------
  settingsBtn.addEventListener("click", () => settingsModal.classList.remove("hidden"));
  closeSettingsBtn.addEventListener("click", () => settingsModal.classList.add("hidden"));

  saveSettingsBtn.addEventListener("click", () => {
    localStorage.setItem("repomind_gh_token", settingsGhToken.value.trim());
    localStorage.setItem("repomind_gemini_key", settingsGeminiKey.value.trim());
    localStorage.setItem("repomind_openai_key", settingsOpenAIKey.value.trim());
    localStorage.setItem("repomind_groq_key", settingsGroqKey.value.trim());
    
    settingsModal.classList.add("hidden");
    alert("Settings & API Tokens saved successfully!");
  });

  // --------------------------------------------------------------------------
  // History Renderer
  // --------------------------------------------------------------------------
  function renderHistory() {
    const list = document.getElementById("historyList");
    if (!list) return;
    list.innerHTML = "";
    historyLogs.forEach(log => {
      const item = document.createElement("div");
      item.className = "entry-item";
      item.innerHTML = `
        <div>
          <strong>${log.repo}</strong> — ${log.action}
        </div>
        <span class="hint-text">${log.time}</span>
      `;
      list.appendChild(item);
    });
  }

  function escapeHtml(str) {
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
});
