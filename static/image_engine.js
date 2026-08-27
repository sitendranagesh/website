/**
 * Sitendra Image Studio - Core Client-Side Engine
 * 100% In-Browser Image Manipulation, Binary Search Compression, DPI Injection, and Presets.
 */

window.ImageEngine = (function() {

  // =========================================================
  // 1. Presets Registry
  // =========================================================
  const Presets = {
    passports: {
      india: { name: "India Passport (3.5 × 4.5 cm)", widthCm: 3.5, heightCm: 4.5, dpi: 300, widthPx: 413, heightPx: 531, minKB: 20, maxKB: 100 },
      us: { name: "US Visa / Passport (2 × 2 in)", widthIn: 2, heightIn: 2, dpi: 300, widthPx: 600, heightPx: 600, minKB: 20, maxKB: 240 },
      uk: { name: "UK / EU Passport (35 × 45 mm)", widthCm: 3.5, heightCm: 4.5, dpi: 300, widthPx: 413, heightPx: 531, minKB: 20, maxKB: 100 },
      bangladesh: { name: "Bangladesh Passport (45 × 35 mm)", widthCm: 4.5, heightCm: 3.5, dpi: 300, widthPx: 531, heightPx: 413, minKB: 20, maxKB: 100 },
      australia: { name: "Australia Passport (35 × 45 mm)", widthCm: 3.5, heightCm: 4.5, dpi: 300, widthPx: 413, heightPx: 531, minKB: 20, maxKB: 100 }
    },
    exams: {
      upsc: { name: "UPSC Civil Services", widthPx: 350, heightPx: 350, minKB: 20, maxKB: 300, dpi: 300, requiresNameDate: true },
      ssc: { name: "SSC Photo", widthPx: 100, heightPx: 120, minKB: 20, maxKB: 50, dpi: 200, requiresNameDate: true },
      neet: { name: "NEET UG / NTA (Postcard / Passport)", widthPx: 400, heightPx: 600, minKB: 10, maxKB: 200, dpi: 300, requiresNameDate: true },
      gate: { name: "GATE / JAM", widthPx: 240, heightPx: 320, minKB: 20, maxKB: 200, dpi: 200, requiresNameDate: false },
      tnpsc: { name: "TNPSC Photo", widthPx: 165, heightPx: 215, minKB: 20, maxKB: 50, dpi: 200, requiresNameDate: true }
    },
    socials: {
      instaSquare: { name: "Instagram Square (1:1)", widthPx: 1080, heightPx: 1080 },
      instaStory: { name: "Instagram Story / Reel (9:16)", widthPx: 1080, heightPx: 1920 },
      ytThumb: { name: "YouTube Thumbnail (16:9)", widthPx: 1280, heightPx: 720 },
      ytBanner: { name: "YouTube Channel Banner", widthPx: 2560, heightPx: 1440 },
      twitterPost: { name: "Twitter/X Post", widthPx: 1200, heightPx: 675 },
      twitterHeader: { name: "Twitter/X Header Banner", widthPx: 1500, heightPx: 500 },
      fullHd: { name: "Full HD (1920 × 1080)", widthPx: 1920, heightPx: 1080 }
    }
  };

  // =========================================================
  // 2. DPI & Physical Units Conversion
  // =========================================================
  const DPI = {
    cmToPx(cm, dpi = 300) {
      return Math.round((cm / 2.54) * dpi);
    },
    mmToPx(mm, dpi = 300) {
      return Math.round((mm / 25.4) * dpi);
    },
    inchToPx(inch, dpi = 300) {
      return Math.round(inch * dpi);
    },
    pxToCm(px, dpi = 300) {
      return parseFloat(((px * 2.54) / dpi).toFixed(2));
    },

    /**
     * Injects a standard JFIF resolution segment (300 DPI) into a JPEG ArrayBuffer.
     */
    injectJfifDpi(jpegArrayBuffer, dpi = 300) {
      const view = new DataView(jpegArrayBuffer);
      // Validate SOI marker 0xFFD8
      if (view.getUint16(0) !== 0xFFD8) return jpegArrayBuffer;

      // Check if APP0 already exists
      if (view.getUint16(2) === 0xFFE0) {
        // Update density in existing JFIF segment
        // Length at offset 2, identifier 'JFIF\0' at offset 4
        const id = String.fromCharCode(
          view.getUint8(6), view.getUint8(7), view.getUint8(8), view.getUint8(9), view.getUint8(10)
        );
        if (id === "JFIF\0") {
          view.setUint8(13, 1); // 1 = dots per inch
          view.setUint16(14, dpi); // X density
          view.setUint16(16, dpi); // Y density
          return jpegArrayBuffer;
        }
      }

      // Construct a new JFIF APP0 segment
      const jfifHeader = new Uint8Array([
        0xFF, 0xE0, // APP0 marker
        0x00, 0x10, // Length (16 bytes)
        0x4A, 0x46, 0x49, 0x46, 0x00, // 'JFIF\0'
        0x01, 0x01, // Version 1.1
        0x01,       // Units: 1 = DPI
        (dpi >> 8) & 0xFF, dpi & 0xFF, // X density
        (dpi >> 8) & 0xFF, dpi & 0xFF, // Y density
        0x00, 0x00  // Thumbnail size (0x0)
      ]);

      const originalBytes = new Uint8Array(jpegArrayBuffer);
      const combined = new Uint8Array(originalBytes.length + jfifHeader.length);
      // Copy SOI
      combined.set(originalBytes.subarray(0, 2), 0);
      // Insert JFIF
      combined.set(jfifHeader, 2);
      // Copy rest of image
      combined.set(originalBytes.subarray(2), 2 + jfifHeader.length);

      return combined.buffer;
    }
  };

  // =========================================================
  // 3. Binary Search Target-Size Compressor
  // =========================================================
  async function compressToTargetKB(canvas, targetKB, options = {}) {
    const {
      mimeType = "image/jpeg",
      maxIterations = 8,
      tolerancePercent = 5,
      allowResize = true
    } = options;

    const targetBytes = targetKB * 1024;
    const minAcceptable = targetBytes * (1 - tolerancePercent / 100);
    const maxAcceptable = targetBytes * (1 + tolerancePercent / 100);

    let lowQ = 0.01;
    let highQ = 0.99;
    let bestBlob = null;
    let bestDiff = Infinity;

    // Helper: convert canvas to blob with specific quality
    function canvasToBlob(c, q, type) {
      return new Promise(resolve => c.toBlob(resolve, type, q));
    }

    let currentCanvas = canvas;
    let scale = 1.0;

    for (let iter = 0; iter < maxIterations; iter++) {
      const midQ = (lowQ + highQ) / 2;
      const blob = await canvasToBlob(currentCanvas, midQ, mimeType);
      const size = blob.size;
      const diff = Math.abs(size - targetBytes);

      if (diff < bestDiff) {
        bestDiff = diff;
        bestBlob = blob;
      }

      if (size >= minAcceptable && size <= maxAcceptable) {
        bestBlob = blob;
        break;
      }

      if (size > targetBytes) {
        highQ = midQ;
      } else {
        lowQ = midQ;
      }

      // If quality is bottomed out and still too large, downscale dimension
      if (highQ < 0.05 && size > targetBytes && allowResize && scale > 0.3) {
        scale *= 0.8;
        const newW = Math.max(50, Math.round(canvas.width * scale));
        const newH = Math.max(50, Math.round(canvas.height * scale));
        const tempCanvas = document.createElement("canvas");
        tempCanvas.width = newW;
        tempCanvas.height = newH;
        const ctx = tempCanvas.getContext("2d");
        ctx.drawImage(canvas, 0, 0, newW, newH);
        currentCanvas = tempCanvas;
        lowQ = 0.1;
        highQ = 0.95;
      }
    }

    return bestBlob;
  }

  // =========================================================
  // 4. Artificial File Size Increaser (Byte Padding)
  // =========================================================
  async function increaseBlobSize(blob, targetKB) {
    const targetBytes = targetKB * 1024;
    if (blob.size >= targetBytes) {
      return blob;
    }

    const neededPadding = targetBytes - blob.size;
    const arrayBuffer = await blob.arrayBuffer();
    const isJpeg = blob.type === "image/jpeg" || (new Uint8Array(arrayBuffer, 0, 2)[0] === 0xFF && new Uint8Array(arrayBuffer, 0, 2)[1] === 0xD8);

    if (isJpeg && neededPadding > 10) {
      // JPEG COM (Comment) marker: 0xFFFE + 2 bytes length + data
      const maxSegmentSize = 65533; // max length per JPEG segment
      let remaining = neededPadding;
      const chunks = [];
      chunks.push(new Uint8Array(arrayBuffer.slice(0, 2))); // SOI 0xFFD8

      while (remaining > 0) {
        const payloadLen = Math.min(remaining - 4, maxSegmentSize);
        if (payloadLen <= 0) break;
        const segLen = payloadLen + 2;
        const comHeader = new Uint8Array([
          0xFF, 0xFE,
          (segLen >> 8) & 0xFF, segLen & 0xFF
        ]);
        const paddingBytes = new Uint8Array(payloadLen);
        paddingBytes.fill(0x20); // clean space characters
        chunks.push(comHeader);
        chunks.push(paddingBytes);
        remaining -= (segLen + 2);
      }

      chunks.push(new Uint8Array(arrayBuffer.slice(2)));
      return new Blob(chunks, { type: "image/jpeg" });
    }

    // Generic safe trailing padding
    const padding = new Uint8Array(neededPadding);
    padding.fill(0x00);
    return new Blob([blob, padding], { type: blob.type || "image/png" });
  }

  // =========================================================
  // 5. Canvas Pixel Manipulation (Censor, Blur, Pixelate)
  // =========================================================
  function pixelateArea(ctx, x, y, width, height, blockSize = 14) {
    const imgData = ctx.getImageData(x, y, width, height);
    const data = imgData.data;

    for (let py = 0; py < height; py += blockSize) {
      for (let px = 0; px < width; px += blockSize) {
        let r = 0, g = 0, b = 0, a = 0, count = 0;

        for (let dy = 0; dy < blockSize; dy++) {
          for (let dx = 0; dx < blockSize; dx++) {
            const curX = px + dx;
            const curY = py + dy;
            if (curX < width && curY < height) {
              const idx = (curY * width + curX) * 4;
              r += data[idx];
              g += data[idx + 1];
              b += data[idx + 2];
              a += data[idx + 3];
              count++;
            }
          }
        }

        r = Math.round(r / count);
        g = Math.round(g / count);
        b = Math.round(b / count);
        a = Math.round(a / count);

        for (let dy = 0; dy < blockSize; dy++) {
          for (let dx = 0; dx < blockSize; dx++) {
            const curX = px + dx;
            const curY = py + dy;
            if (curX < width && curY < height) {
              const idx = (curY * width + curX) * 4;
              data[idx] = r;
              data[idx + 1] = g;
              data[idx + 2] = b;
              data[idx + 3] = a;
            }
          }
        }
      }
    }

    ctx.putImageData(imgData, x, y);
  }

  function blackBarArea(ctx, x, y, width, height) {
    ctx.fillStyle = "#000000";
    ctx.fillRect(x, y, width, height);
  }

  // =========================================================
  // 6. Dominant Color Palette Extractor
  // =========================================================
  function extractColorPalette(canvas, maxColors = 6) {
    const ctx = canvas.getContext("2d");
    const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const data = imgData.data;
    const colorCounts = {};

    // Step sample every 16 pixels for fast client performance
    for (let i = 0; i < data.length; i += 16 * 4) {
      const a = data[i + 3];
      if (a < 128) continue; // ignore transparent
      // Quantize to 32 steps
      const r = Math.round(data[i] / 32) * 32;
      const g = Math.round(data[i + 1] / 32) * 32;
      const b = Math.round(data[i + 2] / 32) * 32;
      const key = `${r},${g},${b}`;
      colorCounts[key] = (colorCounts[key] || 0) + 1;
    }

    const sorted = Object.entries(colorCounts).sort((a, b) => b[1] - a[1]);
    const top = sorted.slice(0, maxColors).map(([k]) => {
      const [r, g, b] = k.split(",").map(Number);
      const hex = "#" + [r, g, b].map(x => x.toString(16).padStart(2, "0")).join("").toUpperCase();
      return { r, g, b, hex };
    });

    return top;
  }

  return {
    Presets,
    DPI,
    compressToTargetKB,
    increaseBlobSize,
    pixelateArea,
    blackBarArea,
    extractColorPalette
  };

})();
