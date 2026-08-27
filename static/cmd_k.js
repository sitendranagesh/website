// Global Command Palette (Cmd + K / Ctrl + K) & PWA Init for Sitendra Platform
(function() {
  // Register Service Worker for PWA
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js').catch(() => {});
    });
  }

  // Predefined navigation items
  const defaultItems = [
    { title: 'Blog Feed & Articles', url: '/blog', category: 'Blog', icon: '📖' },
    { title: 'Image Manipulation Studio', url: '/image-tools', category: 'Image Tool', icon: '🖼️' },
    { title: 'Target KB Compressor (20KB, 50KB, 100KB)', url: '/image-tools', category: 'Image Tool', icon: '🎯' },
    { title: 'Passport Photo Maker (India 3.5x4.5, US 2x2)', url: '/image-tools', category: 'Image Tool', icon: '🛂' },
    { title: 'Add Name & Date on Photo (NEET / UPSC)', url: '/image-tools', category: 'Image Tool', icon: '📝' },
    { title: 'Merge Photo & Signature (Exam Form)', url: '/image-tools', category: 'Image Tool', icon: '🖋️' },
    { title: 'Signature Maker & Digital Pad', url: '/image-tools', category: 'Image Tool', icon: '✍️' },
    { title: 'Watermark Studio (Text & Logo)', url: '/image-tools', category: 'Image Tool', icon: '💧' },
    { title: 'Image to PDF Converter', url: '/image-tools', category: 'Image Tool', icon: '📄' },
    { title: 'PDF to JPG Converter', url: '/image-tools', category: 'Image Tool', icon: '📑' },
    { title: 'Image to Text (In-Browser OCR)', url: '/image-tools', category: 'Image Tool', icon: '🔍' },
    { title: 'Blur, Censor & Pixelate Faces / IDs', url: '/image-tools', category: 'Image Tool', icon: '🛡️' },
    { title: 'Increase File Size in KB / MB', url: '/image-tools', category: 'Image Tool', icon: '📈' },
    { title: 'Batch Image Compressor (ZIP)', url: '/image-tools', category: 'Image Tool', icon: '⚡' },
    { title: 'Instagram No-Crop & Grid Slicer', url: '/image-tools', category: 'Image Tool', icon: '✂️' },
    { title: 'Favicon & Multi-Size Icon Maker', url: '/image-tools', category: 'Image Tool', icon: '🖼️' },
    { title: 'Resize Image in Pixels (Exact Width & Height)', url: '/image-tools', category: 'Image Tool', icon: '📏' },
    { title: 'ATS Resume & CV Builder', url: '/resume', category: 'Career', icon: '📄' },
    { title: 'Beam Stress, Deflection & SFD/BMD Calculator', url: '/tools', category: 'Mechanical Calc', icon: '🏗️' },
    { title: 'Gear Train Ratio, RPM & Torque Multiplier', url: '/tools', category: 'Mechanical Calc', icon: '⚙️' },
    { title: 'Bolt Tightening Torque & Preload Force Estimator', url: '/tools', category: 'Mechanical Calc', icon: '🔩' },
    { title: 'ISO 286 Limits & Fits Tolerance Analyzer', url: '/tools', category: 'Mechanical Calc', icon: '📐' },
    { title: 'QR Code & Wi-Fi Studio', url: '/tools', category: 'Security', icon: '📱' },
    { title: 'Cryptographic File Hasher & Checksum (SHA-256, MD5)', url: '/tools', category: 'Security', icon: '🔐' },
    { title: 'Secure Password & Passphrase Generator', url: '/tools', category: 'Security', icon: '🔑' },
    { title: 'Side-by-Side Visual Text & Code Diff', url: '/tools', category: 'Developer', icon: '🔀' },
    { title: 'Developer & Engineering Tools', url: '/tools', category: 'Tools', icon: '⚙️' },
    { title: 'Projects Portfolio', url: '/projects', category: 'Projects', icon: '🚀' },
    { title: 'My Notes App', url: '/', category: 'Notes', icon: '📝' },
    { title: 'About Sitendra', url: '/about', category: 'About', icon: '👤' },
    { title: 'JSON Formatter & Validator', url: '/tools', category: 'Tool', icon: '{ }' },
    { title: 'Engineering Unit Converter', url: '/tools', category: 'Tool', icon: '📏' },
    { title: 'Regex Tester', url: '/tools', category: 'Tool', icon: '.*' },
  ];

  let dynamicItems = [...defaultItems];
  let isBackdropReady = false;

  // Fetch published blog posts for spotlight search
  fetch('/api/blogs')
    .then(r => r.json())
    .then(posts => {
      if (Array.isArray(posts)) {
        posts.forEach(p => {
          dynamicItems.push({
            title: p.title,
            url: `/blog/post/${p.slug}`,
            category: 'Article',
            icon: '📄'
          });
        });
      }
    })
    .catch(() => {});

  function createModal() {
    if (document.getElementById('cmdk-backdrop')) return;

    const backdrop = document.createElement('div');
    backdrop.id = 'cmdk-backdrop';
    backdrop.className = 'cmdk-backdrop';
    backdrop.innerHTML = `
      <div class="cmdk-modal">
        <div class="cmdk-input-row">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"/>
            <path d="m21 21-4.3-4.3"/>
          </svg>
          <input type="text" id="cmdk-input" class="cmdk-search-input" placeholder="Type a command, tool, or search articles..." autocomplete="off">
        </div>
        <ul class="cmdk-results-list" id="cmdk-list"></ul>
        <div class="cmdk-footer">
          <span>Navigation: <span class="cmdk-kbd">&uarr;</span> <span class="cmdk-kbd">&darr;</span> to navigate</span>
          <span>Select: <span class="cmdk-kbd">Enter</span> &bull; Close: <span class="cmdk-kbd">ESC</span></span>
        </div>
      </div>
    `;
    document.body.appendChild(backdrop);

    const input = document.getElementById('cmdk-input');
    const list = document.getElementById('cmdk-list');
    let selectedIndex = 0;

    function renderList(query = '') {
      const q = query.toLowerCase().trim();
      const filtered = dynamicItems.filter(item => 
        !q || item.title.toLowerCase().includes(q) || item.category.toLowerCase().includes(q)
      );

      list.innerHTML = '';
      if (filtered.length === 0) {
        list.innerHTML = '<li style="padding: 1.5rem; text-align: center; color: #64748B; font-size: 0.9rem;">No results found.</li>';
        return;
      }

      selectedIndex = Math.min(selectedIndex, filtered.length - 1);
      if (selectedIndex < 0) selectedIndex = 0;

      filtered.forEach((item, idx) => {
        const li = document.createElement('li');
        li.className = `cmdk-item ${idx === selectedIndex ? 'selected' : ''}`;
        li.innerHTML = `
          <div class="cmdk-item-left">
            <span class="cmdk-item-icon">${item.icon}</span>
            <span>${item.title}</span>
          </div>
          <span class="cmdk-item-badge">${item.category}</span>
        `;
        li.addEventListener('click', () => {
          window.location.href = item.url;
        });
        list.appendChild(li);
      });
    }

    input.addEventListener('input', () => {
      selectedIndex = 0;
      renderList(input.value);
    });

    input.addEventListener('keydown', (e) => {
      const items = list.querySelectorAll('.cmdk-item');
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        selectedIndex = (selectedIndex + 1) % items.length;
        renderList(input.value);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        selectedIndex = (selectedIndex - 1 + items.length) % items.length;
        renderList(input.value);
      } else if (e.key === 'Enter') {
        e.preventDefault();
        const selected = list.querySelector('.cmdk-item.selected');
        if (selected) selected.click();
      } else if (e.key === 'Escape') {
        closePalette();
      }
    });

    backdrop.addEventListener('click', (e) => {
      if (e.target === backdrop) closePalette();
    });

    isBackdropReady = true;
  }

  function openPalette() {
    createModal();
    const backdrop = document.getElementById('cmdk-backdrop');
    const input = document.getElementById('cmdk-input');
    backdrop.classList.add('open');
    input.value = '';
    const list = document.getElementById('cmdk-list');
    if (list) list.innerHTML = '';
    
    // Initial render
    const filtered = dynamicItems;
    filtered.forEach((item, idx) => {
      const li = document.createElement('li');
      li.className = `cmdk-item ${idx === 0 ? 'selected' : ''}`;
      li.innerHTML = `
        <div class="cmdk-item-left">
          <span class="cmdk-item-icon">${item.icon}</span>
          <span>${item.title}</span>
        </div>
        <span class="cmdk-item-badge">${item.category}</span>
      `;
      li.addEventListener('click', () => {
        window.location.href = item.url;
      });
      list.appendChild(li);
    });

    setTimeout(() => input.focus(), 50);
  }

  function closePalette() {
    const backdrop = document.getElementById('cmdk-backdrop');
    if (backdrop) backdrop.classList.remove('open');
  }

  // Keyboard shortcut listener
  window.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      const backdrop = document.getElementById('cmdk-backdrop');
      if (backdrop && backdrop.classList.contains('open')) {
        closePalette();
      } else {
        openPalette();
      }
    }
  });

  // Wire up any ⌘K header buttons
  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('#cmdk-btn, .open-cmdk').forEach(btn => {
      btn.addEventListener('click', openPalette);
    });
  });
})();
