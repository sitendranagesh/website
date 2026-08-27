/**
 * Sitendra Quick Chat & Interactive Assistant
 * Lightweight, client-first interactive chat widget with zero heavy backend requirements.
 */

(function() {
  // Knowledge Base Rules & Intent Matcher
  const KNOWLEDGE = [
    {
      keywords: ["project", "portfolio", "built", "work", "mechanical", "cad"],
      response: "🚀 Sitendra has built both **Mechanical Systems** (CAD mechanism modeling, gear tolerance optimizations) and **Software Products** (Multi-subdomain Blog, Notes App, Image Studio, Developer Hub). <br><br>👉 <a href='/projects'>Explore the Projects Portfolio &rarr;</a>"
    },
    {
      keywords: ["image", "tool", "pdf", "compress", "resize", "passport", "ocr", "censor", "photo", "convert"],
      response: "🖼️ Our **Image Studio** offers 14 privacy-first, client-side utilities including: <br>• 🎯 Exact Target KB Compressor (20KB, 50KB)<br>• 🛂 Official Passport & Exam Photo Maker (with Name/DOB)<br>• 📄 Image to PDF & PDF to JPG<br>• 🔍 In-Browser OCR Text Extraction<br>• ✍️ Digital Signature Pad<br><br>👉 <a href='/image-tools'>Open Image Studio &rarr;</a>"
    },
    {
      keywords: ["mech", "beam", "gear", "bolt", "torque", "deflection", "sfd", "bmd", "tolerance", "fits", "calculator", "calc"],
      response: "🧮 Explore our **Mechanical Engineering Calculators Suite**: <br>• 🏗️ Beam Deflection &amp; Bending Stress (Live SFD/BMD plots)<br>• ⚙️ Gear Train Ratio &amp; Torque Multiplier<br>• 🔩 Fastener Bolt Tightening Torque &amp; Preload<br>• 📐 ISO 286 Limits, Fits &amp; Tolerances<br><br>👉 <a href='/tools'>Open Mechanical Calculators &rarr;</a>"
    },
    {
      keywords: ["security", "qr", "qrcode", "hash", "checksum", "sha256", "md5", "password", "passphrase", "diff"],
      response: "🔐 Check out our **Security &amp; Everyday Web Utilities**: <br>• 📱 QR Code &amp; Wi-Fi Connect Studio<br>• 🔐 Cryptographic Hash &amp; File Checksum (SHA-256, MD5)<br>• 🔑 Secure Password &amp; Passphrase Generator<br>• 🔀 Side-by-Side Visual Text &amp; Code Diff<br><br>👉 <a href='/tools'>Open Security Tools &rarr;</a>"
    },
    {
      keywords: ["dev tool", "json", "unit", "converter", "regex"],
      response: "⚙️ Check out our **Developer & Engineering Tools Hub** for JSON Formatting, Engineering Unit Conversions (Pressure, Torque, Force, Power), and Regex Testing. <br><br>👉 <a href='/tools'>Open Dev Tools &rarr;</a>"
    },
    {
      keywords: ["blog", "article", "read", "post", "rss", "feed"],
      response: "📖 Sitendra writes technical articles on backend architecture, system design, and engineering workflows. You can also subscribe to our RSS feed at <code>/feed.xml</code>! <br><br>👉 <a href='/blog'>Visit the Blog &rarr;</a>"
    },
    {
      keywords: ["who", "about", "sitendra", "bio", "experience", "skills"],
      response: "👤 Sitendra Kumar Nagesh is a Mechanical Engineer by training and Software Engineer by trade, specializing in Python/FastAPI, modern web architectures, and mechanical systems. <br><br>👉 <a href='/about'>Read Full Bio & About Page &rarr;</a>"
    },
    {
      keywords: ["resume", "cv", "curriculum", "career", "template", "job"],
      response: "📄 Check out our **ATS Resume & CV Builder**! Choose between Modern Engineer, Minimalist, and Executive templates, customize colors, and download a vector-crisp PDF. <br><br>👉 <a href='/resume'>Open Resume Builder &rarr;</a>"
    },
    {
      keywords: ["contact", "email", "hire", "message", "touch", "reach"],
      response: "📬 You can leave a quick message right here in this chat, or email Sitendra directly at <a href='mailto:sitendranagesh@gmail.com'>sitendranagesh@gmail.com</a>."
    }
  ];

  function createChatDOM() {
    if (document.getElementById("chat-widget-fab")) return;

    // 1. Floating Toggle Button
    const fab = document.createElement("button");
    fab.id = "chat-widget-fab";
    fab.className = "chat-widget-fab";
    fab.setAttribute("aria-label", "Open Quick Chat");
    fab.setAttribute("title", "Quick Chat & Assistant");
    fab.innerHTML = `
      <span class="chat-unread-dot"></span>
      <svg class="fab-icon-chat" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      </svg>
      <svg class="fab-icon-close" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="18" y1="6" x2="6" y2="18"/>
        <line x1="6" y1="6" x2="18" y2="18"/>
      </svg>
    `;

    // 2. Chat Window
    const win = document.createElement("div");
    win.id = "chat-widget-window";
    win.className = "chat-widget-window";
    win.innerHTML = `
      <div class="chat-header">
        <div class="chat-header-user">
          <div class="chat-avatar">S</div>
          <div>
            <div class="chat-title">Sitendra Assistant</div>
            <div class="chat-status">Online &bull; Instant Q&amp;A</div>
          </div>
        </div>
        <button type="button" class="chat-close-btn" id="chat-close-btn" aria-label="Close Chat">&times;</button>
      </div>

      <div class="chat-messages" id="chat-messages">
        <div class="chat-msg bot">
          👋 Hi there! I'm Sitendra's interactive assistant. Ask me anything about his projects, tools, or drop a quick note.
          <div class="chat-quick-chips">
            <button type="button" class="chat-chip" data-query="projects">🚀 Projects</button>
            <button type="button" class="chat-chip" data-query="image tools">🖼️ Image Studio</button>
            <button type="button" class="chat-chip" data-query="resume">📄 Resume Builder</button>
            <button type="button" class="chat-chip" data-query="blog">📖 Blog</button>
            <button type="button" class="chat-chip" data-query="about">👤 Who is Sitendra?</button>
            <button type="button" class="chat-chip" data-query="contact">📬 Contact</button>
          </div>
        </div>
      </div>

      <form class="chat-input-box" id="chat-form">
        <input type="text" id="chat-input" placeholder="Type a question or message..." autocomplete="off">
        <button type="submit" class="chat-send-btn" aria-label="Send Message">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="22" y1="2" x2="11" y2="13"/>
            <polygon points="22 2 15 22 11 13 2 9 22 2"/>
          </svg>
        </button>
      </form>
    `;

    document.body.appendChild(fab);
    document.body.appendChild(win);

    // Event Listeners
    fab.addEventListener("click", toggleChat);
    document.getElementById("chat-close-btn").addEventListener("click", toggleChat);

    const form = document.getElementById("chat-form");
    const input = document.getElementById("chat-input");

    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const val = input.value.trim();
      if (!val) return;
      handleUserQuery(val);
      input.value = "";
    });

    document.addEventListener("click", (e) => {
      if (e.target && e.target.classList.contains("chat-chip")) {
        const query = e.target.dataset.query;
        handleUserQuery(query);
      }
    });
  }

  function toggleChat() {
    const fab = document.getElementById("chat-widget-fab");
    const win = document.getElementById("chat-widget-window");
    const isOpen = win.classList.toggle("open");
    fab.classList.toggle("open", isOpen);

    if (isOpen) {
      const dot = fab.querySelector(".chat-unread-dot");
      if (dot) dot.style.display = "none";
      setTimeout(() => document.getElementById("chat-input").focus(), 200);
    }
  }

  async function handleUserQuery(text) {
    appendMessage(text, "user");

    const lower = text.toLowerCase();
    let matchedResponse = null;

    // Check Knowledge Base
    for (const item of KNOWLEDGE) {
      if (item.keywords.some(kw => lower.includes(kw))) {
        matchedResponse = item.response;
        break;
      }
    }

    if (matchedResponse) {
      setTimeout(() => appendMessage(matchedResponse, "bot"), 350);
    } else {
      // If it looks like a direct visitor message/greeting, save to backend
      setTimeout(async () => {
        try {
          const res = await fetch("/api/chat/message", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text, name: "Website Visitor" })
          });
          if (res.ok) {
            appendMessage("✅ Thank you! I've forwarded your message to Sitendra. He'll review it shortly. Feel free to explore the <a href='/projects'>Projects</a> or <a href='/tools'>Tools</a> in the meantime!", "bot");
          } else {
            appendMessage("I'm happy to help! You can ask about Sitendra's <b>projects</b>, <b>blog posts</b>, <b>image tools</b>, or email him at <a href='mailto:sitendranagesh@gmail.com'>sitendranagesh@gmail.com</a>.", "bot");
          }
        } catch (e) {
          appendMessage("Got it! Feel free to ask about Sitendra's <b>projects</b>, <b>image studio</b>, or <b>blog articles</b>.", "bot");
        }
      }, 400);
    }
  }

  function appendMessage(htmlContent, sender) {
    const container = document.getElementById("chat-messages");
    if (!container) return;

    const msg = document.createElement("div");
    msg.className = `chat-msg ${sender}`;
    msg.innerHTML = htmlContent;
    container.appendChild(msg);
    container.scrollTop = container.scrollHeight;
  }

  // Init when DOM ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", createChatDOM);
  } else {
    createChatDOM();
  }
})();
