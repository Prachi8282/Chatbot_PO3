// ══════════════════════════════════════════════════════════════════════════════
// Chatbot Logic and UI Interactions
// ══════════════════════════════════════════════════════════════════════════════

document.addEventListener("DOMContentLoaded", () => {
    // DOM Cache
    const docListContainer = document.getElementById("document-list-container");
    const searchModeBadge = document.getElementById("search-mode-badge");
    const chatMessagesContainer = document.getElementById("chat-messages-container");
    const chatInputForm = document.getElementById("chat-input-form");
    const userQueryInput = document.getElementById("user-query-input");
    const btnClearChat = document.getElementById("btn-clear-chat");
    const previewSidebar = document.getElementById("preview-sidebar");
    const btnClosePreview = document.getElementById("btn-close-preview");
    const documentPreviewBody = document.getElementById("document-preview-body");

    let currentSearchMode = "Vector Semantic";
    let indexedDocs = [];

    // --- Markdown to HTML Lightweight Parser ---
    function parseMarkdown(mdText) {
        if (!mdText) return "";
        let html = mdText;
        
        // Headers
        html = html.replace(/^# (.*?)$/gm, '<h1>$1</h1>');
        html = html.replace(/^## (.*?)$/gm, '<h2>$1</h2>');
        html = html.replace(/^### (.*?)$/gm, '<h3>$1</h3>');
        
        // Bullet points
        html = html.replace(/^\- (.*?)$/gm, '<li>$1</li>');
        // Wrap consecutive <li> elements in <ul>
        html = html.replace(/(<li>.*?<\/li>)+/g, '<ul>$&</ul>');
        
        // Bold text
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Newlines/Paragraphs (non-header, non-list, non-empty lines)
        html = html.replace(/^(?!(?:<h|<ul|<li|<strong|\s*$).+?)$/gm, '<p>$1</p>');
        
        return html;
    }

    // --- Document Operations ---
    
    // Load documents from backend
    async function loadDocuments() {
        try {
            const res = await fetch("/api/documents");
            const data = await res.json();
            indexedDocs = data.documents;
            renderDocumentList(indexedDocs);
        } catch (err) {
            console.error("Failed to load documents", err);
            docListContainer.innerHTML = `<div class="loading-spinner" style="color: #ef4444;">Failed to load documents.</div>`;
        }
    }

    // Render document cards in left sidebar
    function renderDocumentList(docs) {
        if (docs.length === 0) {
            docListContainer.innerHTML = `<div class="loading-spinner">No documents indexed yet.</div>`;
            return;
        }

        docListContainer.innerHTML = "";
        docs.forEach(doc => {
            const card = document.createElement("div");
            card.className = "doc-card";
            card.id = `doc-card-${doc.id}`;
            
            // Clean filename for display
            const parts = doc.file_path.split(/[\\/]/);
            const filename = parts[parts.length - 1];

            card.innerHTML = `
                <div class="doc-card-title">${doc.title}</div>
                <div class="doc-card-meta">
                    <span class="path" title="${doc.file_path}">${filename}</span>
                    <span class="size">${Math.round(doc.char_count / 100) / 10} KB</span>
                </div>
            `;
            
            card.addEventListener("click", () => {
                // Highlight card
                document.querySelectorAll(".doc-card").forEach(c => c.classList.remove("active"));
                card.classList.add("active");
                previewDocument(doc.file_path);
            });
            
            docListContainer.appendChild(card);
        });
    }

    // Preview document in right sidebar
    async function previewDocument(filePath) {
        documentPreviewBody.innerHTML = `<div class="preview-placeholder"><div class="typing-indicator"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div><p>Loading document content...</p></div>`;
        previewSidebar.classList.remove("collapsed");

        try {
            const res = await fetch(`/api/documents/content?file_path=${encodeURIComponent(filePath)}`);
            if (!res.ok) throw new Error("Fetch failed");
            
            const data = await res.json();
            
            // Format source link and path
            const parts = filePath.split(/[\\/]/);
            const filename = parts[parts.length - 1];
            
            documentPreviewBody.innerHTML = `
                <div style="margin-bottom: 16px; font-size: 0.75rem; color: var(--color-text-muted);">
                    <strong>Source File:</strong> <span style="font-family: monospace;">${filename}</span><br>
                    <strong>Path:</strong> <span style="font-family: monospace; word-break: break-all;">${filePath}</span>
                </div>
                <div class="markdown-body">
                    ${parseMarkdown(data.content)}
                </div>
            `;
        } catch (err) {
            documentPreviewBody.innerHTML = `
                <div class="preview-placeholder" style="color: #ef4444;">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2"/>
                        <line x1="12" y1="8" x2="12" y2="12"/>
                        <line x1="12" y1="16" x2="12.01" y2="16"/>
                    </svg>
                    <p>Failed to load document content.</p>
                </div>
            `;
        }
    }

    // Close preview sidebar
    btnClosePreview.addEventListener("click", () => {
        previewSidebar.classList.add("collapsed");
        document.querySelectorAll(".doc-card").forEach(c => c.classList.remove("active"));
    });


    // --- Chat Operations ---

    // Add a message bubble to the chat container
    function addMessage(sender, text, resultData = null) {
        const messageDiv = document.createElement("div");
        messageDiv.className = `message ${sender}`;
        
        const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        let bubbleContent = `<div class="message-bubble">${text}`;
        
        if (resultData && resultData.results && resultData.results.length > 0) {
            bubbleContent += `<div class="search-results-list">`;
            resultData.results.forEach((res, index) => {
                // Clean filename
                const parts = res.file_path.split(/[\\/]/);
                const filename = parts[parts.length - 1];

                bubbleContent += `
                    <div class="result-card">
                        <div class="result-header">
                            <span class="result-title">
                                <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                                    <polyline points="14 2 14 8 20 8"/>
                                </svg>
                                ${res.document_title} &rsaquo; ${res.heading || "Section"}
                            </span>
                            <span class="result-score">${res.score}% Match</span>
                        </div>
                        <div class="result-content">${res.content}</div>
                        <button class="result-link-btn" data-filepath="${res.file_path}">
                            <svg fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                                <polyline points="15 3 21 3 21 9"/>
                                <line x1="10" y1="14" x2="21" y2="3"/>
                            </svg>
                            View Original Document
                        </button>
                    </div>
                `;
            });
            bubbleContent += `</div>`;
        } else if (resultData) {
            bubbleContent += `<p style="margin-top: 10px; color: var(--color-text-secondary); font-style: italic;">No matching paragraphs found. Try rephrasing your search terms.</p>`;
        }
        
        bubbleContent += `</div>`;
        bubbleContent += `<span class="message-time">${timestamp}</span>`;
        
        messageDiv.innerHTML = bubbleContent;
        chatMessagesContainer.appendChild(messageDiv);
        
        // Wire view buttons
        messageDiv.querySelectorAll(".result-link-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                const fp = btn.getAttribute("data-filepath");
                previewDocument(fp);
            });
        });
        
        // Auto scroll to bottom
        chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
    }

    // Show typing bubble indicator
    function showTypingIndicator() {
        const indicatorDiv = document.createElement("div");
        indicatorDiv.className = "message bot typing-indicator-container";
        indicatorDiv.innerHTML = `
            <div class="message-bubble">
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
        chatMessagesContainer.appendChild(indicatorDiv);
        chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
        return indicatorDiv;
    }

    // Set search mode badge text
    function updateSearchModeBadge(mode) {
        searchModeBadge.textContent = mode;
        if (mode.includes("Vector")) {
            searchModeBadge.style.background = "rgba(6, 182, 212, 0.15)";
            searchModeBadge.style.color = "var(--color-accent-teal)";
            searchModeBadge.style.borderColor = "rgba(6, 182, 212, 0.3)";
        } else {
            searchModeBadge.style.background = "rgba(245, 158, 11, 0.15)";
            searchModeBadge.style.color = "#f59e0b";
            searchModeBadge.style.borderColor = "rgba(245, 158, 11, 0.3)";
        }
    }

    // Reset Chat Stream to Welcome Screen
    function loadWelcomeScreen() {
        chatMessagesContainer.innerHTML = "";
        
        const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const welcomeDiv = document.createElement("div");
        welcomeDiv.className = "message bot";
        welcomeDiv.innerHTML = `
            <div class="message-bubble">
                <p><strong>Welcome to the Banking Security & Operations Chatbot!</strong></p>
                <p style="margin-top: 8px;">I perform secure, offline <strong>semantic search queries</strong> against our internal database files containing incidents and banking regulations.</p>
                <p style="margin-top: 8px;">Because I operate without an LLM generator, I will retrieve the exact content paragraphs and provide direct, verified document links below, avoiding any potential hallucinations.</p>
                
                <p style="margin-top: 16px; font-weight: 600; color: var(--color-accent-teal);">Quick search ideas:</p>
                <div class="starter-prompts">
                    <div class="starter-card" data-query="What do I do if database connections are locked in idle transactions?">
                        <span>Database idle connections playbook</span>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                    </div>
                    <div class="starter-card" data-query="What is the SWIFT clearing code for US Dollar transactions?">
                        <span>SWIFT Dollar transfer clearing code</span>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                    </div>
                    <div class="starter-card" data-query="What are the secondary identity documents acceptable for KYC verification?">
                        <span>KYC utility bills & lease verification</span>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                    </div>
                    <div class="starter-card" data-query="How do I block malicious IP ranges during a DDoS attack?">
                        <span>DDoS firewall and iptables commands</span>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                    </div>
                </div>
            </div>
            <span class="message-time">${timestamp}</span>
        `;
        
        chatMessagesContainer.appendChild(welcomeDiv);
        
        // Wire starter cards
        welcomeDiv.querySelectorAll(".starter-card").forEach(card => {
            card.addEventListener("click", () => {
                const query = card.getAttribute("data-query");
                userQueryInput.value = query;
                submitUserQuery(query);
            });
        });

        chatMessagesContainer.scrollTop = 0;
    }

    // Submit a query to the backend search API
    async function submitUserQuery(query) {
        if (!query.trim()) return;
        
        // Clear input field
        userQueryInput.value = "";

        // Add user message to UI
        addMessage("user", query);

        // Add typing indicator
        const typingIndicator = showTypingIndicator();

        try {
            const res = await fetch("/api/search", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query: query, top_k: 3 })
            });

            // Remove typing indicator
            typingIndicator.remove();

            if (!res.ok) {
                 throw new Error("Search server returned an error.");
            }

            const data = await res.json();
            
            // Update search mode badge (vector semantic search or keyword TF-IDF fallback)
            updateSearchModeBadge(data.search_mode);
            
            const count = data.results.length;
            let responseText = "";
            if (count > 0) {
                responseText = `I found **${count} relevant matching sections** in the knowledge database using **${data.search_mode}** matching:`;
            } else {
                responseText = `I could not find any matching documents for that query in the database. Please try rephrasing your search terms (e.g. use keywords like 'DDoS', 'SWIFT', or 'KYC').`;
            }

            addMessage("bot", parseMarkdown(responseText), data);

        } catch (err) {
            typingIndicator.remove();
            addMessage("bot", `<p style="color: #ef4444;"><strong>Error:</strong> Failed to connect to the search service. Please check if the backend server is running.</p>`);
            console.error("Search submission failed", err);
        }
    }

    // Input form submit listener
    chatInputForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const query = userQueryInput.value;
        submitUserQuery(query);
    });

    // Clear chat listener
    btnClearChat.addEventListener("click", () => {
        loadWelcomeScreen();
    });


    // --- Initialization ---
    async function init() {
        await loadDocuments();
        loadWelcomeScreen();
        
        // Fetch a dummy search query to check search mode badge
        try {
            const res = await fetch("/api/search", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query: "test", top_k: 1 })
            });
            const data = await res.json();
            updateSearchModeBadge(data.search_mode);
        } catch (e) {
            updateSearchModeBadge("Keyword TF-IDF (Fallback)");
        }
    }

    init();
});
