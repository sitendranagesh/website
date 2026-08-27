/**
 * Sitendra Security & Everyday Web Utilities Engine
 * 100% In-Browser Cryptographic Hashing, File Checksums, Password & Passphrase Generators, and Visual Diff.
 */

window.SecurityEngine = (function() {

  // =========================================================
  // 1. CRYPTOGRAPHIC HASHING & CHECKSUM ENGINE
  // =========================================================

  // Pure JS MD5 implementation for client-side MD5
  function md5(string) {
    function rotateLeft(lValue, iShiftBits) {
      return (lValue << iShiftBits) | (lValue >>> (32 - iShiftBits));
    }
    function addUnsigned(lX, lY) {
      const lX8 = (lX & 0x80000000);
      const lY8 = (lY & 0x80000000);
      const lX4 = (lX & 0x40000000);
      const lY4 = (lY & 0x40000000);
      const lResult = (lX & 0x3FFFFFFF) + (lY & 0x3FFFFFFF);
      if (lX4 & lY4) return (lResult ^ 0x80000000 ^ lX8 ^ lY8);
      if (lX4 | lY4) {
        if (lResult & 0x40000000) return (lResult ^ 0xC0000000 ^ lX8 ^ lY8);
        else return (lResult ^ 0x40000000 ^ lX8 ^ lY8);
      } else return (lResult ^ lX8 ^ lY8);
    }
    function F(x,y,z){return (x & y) | ((~x) & z);}
    function G(x,y,z){return (x & z) | (y & (~z));}
    function H(x,y,z){return (x ^ y ^ z);}
    function I(x,y,z){return (y ^ (x | (~z)));}
    function FF(a,b,c,d,x,s,ac){
      a = addUnsigned(a, addUnsigned(addUnsigned(F(b, c, d), x), ac));
      return addUnsigned(rotateLeft(a, s), b);
    }
    function GG(a,b,c,d,x,s,ac){
      a = addUnsigned(a, addUnsigned(addUnsigned(G(b, c, d), x), ac));
      return addUnsigned(rotateLeft(a, s), b);
    }
    function HH(a,b,c,d,x,s,ac){
      a = addUnsigned(a, addUnsigned(addUnsigned(H(b, c, d), x), ac));
      return addUnsigned(rotateLeft(a, s), b);
    }
    function II(a,b,c,d,x,s,ac){
      a = addUnsigned(a, addUnsigned(addUnsigned(I(b, c, d), x), ac));
      return addUnsigned(rotateLeft(a, s), b);
    }
    function convertToWordArray(string) {
      let lWordCount;
      const lMessageLength = string.length;
      const lNumberOfWords_temp1 = lMessageLength + 8;
      const lNumberOfWords_temp2 = (lNumberOfWords_temp1 - (lNumberOfWords_temp1 % 64)) / 64;
      const lNumberOfWords = (lNumberOfWords_temp2 + 1) * 16;
      const lWordArray = Array(lNumberOfWords - 1);
      let lBytePosition = 0;
      let lByteCount = 0;
      while (lByteCount < lMessageLength) {
        lWordCount = (lByteCount - (lByteCount % 4)) / 4;
        lBytePosition = (lByteCount % 4) * 8;
        lWordArray[lWordCount] = (lWordArray[lWordCount] | (string.charCodeAt(lByteCount) << lBytePosition));
        lByteCount++;
      }
      lWordCount = (lByteCount - (lByteCount % 4)) / 4;
      lBytePosition = (lByteCount % 4) * 8;
      lWordArray[lWordCount] = lWordArray[lWordCount] | (0x80 << lBytePosition);
      lWordArray[lNumberOfWords - 2] = lMessageLength << 3;
      lWordArray[lNumberOfWords - 1] = lMessageLength >>> 29;
      return lWordArray;
    }
    function wordToHex(lValue) {
      let wordToHexValue = "", wordToHexValue_temp = "", lByte, lCount;
      for (lCount = 0; lCount <= 3; lCount++) {
        lByte = (lValue >>> (lCount * 8)) & 255;
        wordToHexValue_temp = "0" + lByte.toString(16);
        wordToHexValue = wordToHexValue + wordToHexValue_temp.substr(wordToHexValue_temp.length - 2, 2);
      }
      return wordToHexValue;
    }

    const x = convertToWordArray(unescape(encodeURIComponent(string)));
    let a = 0x67452301, b = 0xEFCDAB89, c = 0x98BADCFE, d = 0x10325476;
    const S11=7, S12=12, S13=17, S14=22;
    const S21=5, S22=9 , S23=14, S24=20;
    const S31=4, S32=11, S33=16, S34=23;
    const S41=6, S42=10, S43=15, S44=21;

    for (let k = 0; k < x.length; k += 16) {
      const AA = a, BB = b, CC = c, DD = d;
      a=FF(a,b,c,d,x[k+0],S11,0xD76AA478); d=FF(d,a,b,c,x[k+1],S12,0xE8C7B756); c=FF(c,d,a,b,x[k+2],S13,0x242070DB); b=FF(b,c,d,a,x[k+3],S14,0xC1BDCEEE);
      a=FF(a,b,c,d,x[k+4],S11,0xF57C0FAF); d=FF(d,a,b,c,x[k+5],S12,0x4787C62A); c=FF(c,d,a,b,x[k+6],S13,0xA8304613); b=FF(b,c,d,a,x[k+7],S14,0xFD469501);
      a=FF(a,b,c,d,x[k+8],S11,0x698098D8); d=FF(d,a,b,c,x[k+9],S12,0x8B44F7AF); c=FF(c,d,a,b,x[k+10],S13,0xFFFF5BB1); b=FF(b,c,d,a,x[k+11],S14,0x895CD7BE);
      a=FF(a,b,c,d,x[k+12],S11,0x6B901122); d=FF(d,a,b,c,x[k+13],S12,0xFD987193); c=FF(c,d,a,b,x[k+14],S13,0xA679438E); b=FF(b,c,d,a,x[k+15],S14,0x49B40821);

      a=GG(a,b,c,d,x[k+1],S21,0xF61E2562); d=GG(d,a,b,c,x[k+6],S22,0xC040B340); c=GG(c,d,a,b,x[k+11],S23,0x265E5A51); b=GG(b,c,d,a,x[k+0],S24,0xE9B6C7AA);
      a=GG(a,b,c,d,x[k+5],S21,0xD62F105D); d=GG(d,a,b,c,x[k+10],S22,0x2441453); c=GG(c,d,a,b,x[k+15],S23,0xD8A1E681); b=GG(b,c,d,a,x[k+4],S24,0xE7D3FBC8);
      a=GG(a,b,c,d,x[k+9],S21,0x21E1CDE6); d=GG(d,a,b,c,x[k+14],S22,0xC33707D6); c=GG(c,d,a,b,x[k+3],S23,0xF4D50D87); b=GG(b,c,d,a,x[k+8],S24,0x455A14ED);
      a=GG(a,b,c,d,x[k+13],S21,0xA9E3E905); d=GG(d,a,b,c,x[k+2],S22,0xFCEFA3F8); c=GG(c,d,a,b,x[k+7],S23,0x676F02D9); b=GG(b,c,d,a,x[k+12],S24,0x8D2A4C8A);

      a=HH(a,b,c,d,x[k+5],S31,0xFFFA3942); d=HH(d,a,b,c,x[k+8],S32,0x8771F681); c=HH(c,d,a,b,x[k+11],S33,0x6D9D6122); b=HH(b,c,d,a,x[k+14],S34,0xFDE5380C);
      a=HH(a,b,c,d,x[k+1],S31,0xA4BEEA44); d=HH(d,a,b,c,x[k+4],S32,0x4BDECFA9); c=HH(c,d,a,b,x[k+7],S33,0xF6BB4B60); b=HH(b,c,d,a,x[k+10],S34,0xBEBFBC70);
      a=HH(a,b,c,d,x[k+13],S31,0x289B7EC6); d=HH(d,a,b,c,x[k+0],S32,0xEAA127FA); c=HH(c,d,a,b,x[k+3],S33,0xD4EF3085); b=HH(b,c,d,a,x[k+6],S34,0x4881D05);
      a=HH(a,b,c,d,x[k+9],S31,0xD9D4D039); d=HH(d,a,b,c,x[k+12],S32,0xE6DB99E5); c=HH(c,d,a,b,x[k+15],S33,0x1FA27CF8); b=HH(b,c,d,a,x[k+2],S34,0xC4AC5665);

      a=II(a,b,c,d,x[k+0],S41,0xF4292244); d=II(d,a,b,c,x[k+7],S42,0x432AFF97); c=II(c,d,a,b,x[k+14],S43,0xAB9423A7); b=II(b,c,d,a,x[k+5],S44,0xFC93A039);
      a=II(a,b,c,d,x[k+12],S41,0x655B59C3); d=II(d,a,b,c,x[k+3],S42,0x8F0CCC92); c=II(c,d,a,b,x[k+10],S43,0xFFEFF47D); b=II(b,c,d,a,x[k+1],S44,0x85845DD1);
      a=II(a,b,c,d,x[k+8],S41,0x6FA87E4F); d=II(d,a,b,c,x[k+15],S42,0xFE2CE6E0); c=II(c,d,a,b,x[k+6],S43,0xA3014314); b=II(b,c,d,a,x[k+13],S44,0x4E0811A1);
      a=II(a,b,c,d,x[k+4],S41,0xF7537E82); d=II(d,a,b,c,x[k+11],S42,0xBD3AF235); c=II(c,d,a,b,x[k+2],S43,0x2AD7D2BB); b=II(b,c,d,a,x[k+9],S44,0xEB86D391);

      a = addUnsigned(a, AA); b = addUnsigned(b, BB); c = addUnsigned(c, CC); d = addUnsigned(d, DD);
    }
    return (wordToHex(a) + wordToHex(b) + wordToHex(c) + wordToHex(d)).toLowerCase();
  }

  async function hashBuffer(algo, buffer) {
    if (algo === "MD5") {
      const bytes = new Uint8Array(buffer);
      let binary = "";
      for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
      return md5(binary);
    }

    const algoMap = {
      "SHA-1": "SHA-1",
      "SHA-256": "SHA-256",
      "SHA-384": "SHA-384",
      "SHA-512": "SHA-512"
    };

    const hashBuffer = await crypto.subtle.digest(algoMap[algo] || "SHA-256", buffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  }

  async function hashText(algo, text) {
    const encoder = new TextEncoder();
    const data = encoder.encode(text);
    return hashBuffer(algo, data.buffer);
  }

  // =========================================================
  // 2. CRYPTOGRAPHIC PASSWORD & PASSPHRASE GENERATOR
  // =========================================================
  const DICENAME_WORDS = [
    "ability", "able", "aboard", "about", "above", "accept", "accident", "accord", "account", "accurate",
    "achieve", "acquire", "across", "action", "active", "actor", "actual", "adapt", "address", "advance",
    "aerobic", "afford", "afraid", "agency", "agent", "agree", "ahead", "airport", "alarm", "album",
    "alert", "alien", "align", "alive", "alpha", "alpine", "always", "amber", "ambient", "among",
    "anchor", "ancient", "angel", "angle", "animal", "annual", "answer", "antenna", "antique", "anvil",
    "apart", "apex", "apology", "appeal", "apple", "approve", "apron", "aqua", "arcade", "arch",
    "arctic", "area", "arena", "argon", "armor", "army", "around", "arrange", "array", "arrow",
    "artisan", "artist", "ascend", "asphalt", "asset", "atlas", "atom", "atomic", "attach", "attack",
    "attend", "attic", "audio", "audit", "august", "aunt", "aura", "author", "auto", "autumn",
    "avatar", "avenue", "average", "avoid", "awake", "award", "aware", "awesome", "axis", "azure",
    "bacon", "badge", "bagel", "balance", "balcony", "ballast", "bamboo", "banana", "banner", "barber",
    "barrel", "barrier", "base", "basic", "basket", "battery", "battle", "beacon", "beam", "bear",
    "beauty", "before", "begin", "behave", "behind", "believe", "bench", "benefit", "best", "beyond",
    "bicycle", "binary", "biology", "birch", "biscuit", "blade", "blanket", "blast", "blaze", "blend",
    "bless", "block", "blossom", "blue", "board", "boat", "bold", "bolt", "bonus", "boost",
    "border", "boss", "botany", "bottle", "bounce", "boundary", "brave", "bread", "breeze", "brick",
    "bridge", "brief", "bright", "bronze", "brother", "brush", "bubble", "budget", "buffalo", "build",
    "bullet", "bundle", "bunker", "burden", "butter", "cabin", "cable", "cactus", "cadet", "cafe",
    "calendar", "calm", "camera", "camp", "canopy", "canyon", "capable", "capital", "captain", "carbon",
    "card", "cargo", "carpet", "carrier", "castle", "catalyst", "catch", "cater", "cause", "cavity",
    "cedar", "ceiling", "center", "century", "ceramic", "cereal", "chain", "chair", "chalk", "champion",
    "change", "channel", "chaos", "chapter", "charge", "chariot", "charm", "chart", "chase", "chassis",
    "cheese", "chef", "cherry", "chest", "chief", "chimney", "choice", "chrome", "chronic", "circuit",
    "citizen", "citrus", "city", "civic", "civil", "claim", "clarity", "classic", "clean", "clerk",
    "clever", "client", "cliff", "climate", "climb", "clinic", "clock", "clone", "cloth", "cloud",
    "clover", "cluster", "coach", "coast", "cobalt", "code", "coffee", "cohort", "coin", "cold",
    "collar", "colony", "color", "column", "combat", "combine", "comet", "comfort", "command", "common",
    "compact", "compass", "complex", "comply", "compose", "compute", "concept", "concord", "concrete", "condor",
    "conduit", "connect", "consent", "console", "constant", "consume", "contact", "contain", "context", "control",
    "convert", "convey", "cookie", "copper", "coral", "core", "corner", "corona", "correct", "cosmic",
    "cottage", "cotton", "couch", "council", "counsel", "counter", "county", "courage", "cousin", "cove",
    "cradle", "craft", "crane", "crater", "credit", "creek", "crescent", "crest", "cricket", "crimson",
    "crisis", "crisp", "criterion", "critic", "cross", "crown", "crucial", "cruise", "crystal", "cube",
    "cubic", "cuisine", "culture", "current", "curtain", "curve", "cushion", "custom", "cyber", "cycle",
    "cyclone", "cylinder", "dagger", "daily", "dairy", "damage", "dance", "danger", "daring", "dark",
    "dash", "data", "database", "daughter", "dawn", "daylight", "dazzle", "deal", "debate", "debris",
    "decade", "decimal", "decision", "deck", "declare", "decline", "decor", "decree", "deep", "default",
    "defeat", "defect", "defend", "define", "degree", "delay", "delete", "delight", "delta", "demand",
    "demise", "denial", "dense", "density", "dental", "depart", "depend", "deploy", "deposit", "depth",
    "deputy", "derive", "desert", "design", "desk", "desktop", "desire", "destroy", "detail", "detect",
    "develop", "device", "devote", "diagram", "dial", "diamond", "diary", "dictate", "diesel", "diet",
    "differ", "digit", "dignity", "dilemma", "dinner", "diploma", "direct", "disable", "disaster", "disc",
    "disclose", "discover", "discuss", "disease", "dish", "dismiss", "display", "distance", "distinct", "district",
    "divert", "divide", "divine", "doctor", "document", "dolphin", "domain", "domino", "donate", "donor",
    "door", "dormant", "dosage", "double", "dove", "draft", "dragon", "drain", "drama", "drastic",
    "draw", "dream", "dress", "drift", "drill", "drive", "drone", "drop", "drum", "dryer",
    "dual", "duck", "duct", "duet", "duke", "dummy", "dune", "durable", "duration", "dust",
    "duty", "dwarf", "dynamic", "dynamo", "eagle", "early", "earn", "earth", "easel", "east",
    "easy", "echo", "eclipse", "economy", "ecosystem", "edge", "editor", "educate", "effect", "effort",
    "eight", "elbow", "elder", "elect", "element", "elevator", "elite", "embark", "embassy", "emerald",
    "emerge", "emission", "emotion", "emperor", "empire", "employ", "empower", "empty", "enable", "enact",
    "encode", "encore", "endless", "endorse", "endure", "energy", "enforce", "engage", "engine", "enhance",
    "enjoy", "enlist", "enough", "enrich", "enroll", "ensure", "enter", "entire", "entry", "envelope",
    "envoy", "episode", "epoch", "equal", "equip", "equity", "erase", "erosion", "error", "erupt",
    "escape", "essay", "essence", "estate", "esteem", "eternal", "ether", "ethics", "evacuate", "evaluate",
    "evening", "event", "everest", "evident", "evolve", "exact", "exalt", "examine", "example", "excel",
    "excess", "exchange", "excite", "exclude", "execute", "exempt", "exercise", "exhaust", "exhibit", "exile",
    "exist", "exit", "exotic", "expand", "expect", "expert", "expire", "explain", "explicit", "explore",
    "export", "expose", "express", "extend", "extent", "extra", "extreme", "fabric", "facade", "facet",
    "facility", "factor", "factory", "faculty", "fade", "falcon", "fame", "family", "famous", "fancy",
    "fantasy", "farmer", "fashion", "fast", "fatal", "father", "fatigue", "fault", "favor", "feasible",
    "feature", "federal", "feedback", "fellow", "female", "fence", "fender", "ferry", "festival", "fiber",
    "fiction", "field", "fierce", "figure", "filter", "final", "finance", "finder", "fine", "finger",
    "finish", "fire", "firewall", "firm", "fiscal", "fisher", "fissure", "fitness", "flag", "flame",
    "flange", "flare", "flash", "flat", "flavor", "fleet", "flex", "flight", "flock", "flood",
    "floor", "flora", "flow", "fluid", "flush", "flute", "flux", "flyer", "foam", "focus",
    "foggy", "folder", "folklore", "follow", "font", "foot", "force", "forecast", "forest", "forge",
    "format", "formula", "fortune", "forum", "forward", "fossil", "foster", "found", "fox", "fraction",
    "fracture", "fragment", "frame", "freedom", "freeze", "frequency", "fresh", "friction", "friend", "frigate",
    "frontier", "frost", "frown", "frozen", "fruit", "fuel", "fulfill", "full", "fumble", "function",
    "fundamental", "fungus", "furnace", "furniture", "fury", "fuse", "fusion", "future", "gadget", "gain",
    "galaxy", "gallery", "galley", "game", "gamma", "garage", "garden", "garlic", "gasoline", "gateway",
    "gather", "gauge", "gear", "gemini", "general", "generate", "generic", "genesis", "genius", "genre",
    "gentle", "genuine", "geology", "geometry", "gesture", "geyser", "ghost", "giant", "gift", "giggle",
    "ginger", "giraffe", "glacier", "glance", "glare", "glass", "glide", "glimpse", "global", "globe",
    "glorious", "glory", "glove", "glow", "glue", "glycol", "goal", "goat", "gold", "golden",
    "gondola", "good", "goose", "gospel", "govern", "grace", "grade", "gradient", "gradual", "grain",
    "grand", "granite", "grant", "grape", "graph", "grasp", "gravity", "great", "green", "grid",
    "grief", "grill", "grind", "grip", "groove", "ground", "group", "grove", "grow", "growth",
    "guard", "guardian", "guess", "guide", "guild", "guitar", "gulf", "gust", "gyro", "habit"
  ];

  function generatePassword(length = 16, opts = {}) {
    const {
      uppercase = true,
      lowercase = true,
      numbers = true,
      symbols = true,
      avoidAmbiguous = true
    } = opts;

    let upperSet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    let lowerSet = "abcdefghijklmnopqrstuvwxyz";
    let numberSet = "0123456789";
    let symbolSet = "!@#$%^&*()_+-=[]{}|;:,.<>?";

    if (avoidAmbiguous) {
      upperSet = upperSet.replace(/[O]/g, "");
      lowerSet = lowerSet.replace(/[l]/g, "");
      numberSet = numberSet.replace(/[01]/g, "");
      symbolSet = symbolSet.replace(/[|]/g, "");
    }

    let charPool = "";
    if (uppercase) charPool += upperSet;
    if (lowercase) charPool += lowerSet;
    if (numbers) charPool += numberSet;
    if (symbols) charPool += symbolSet;

    if (!charPool) charPool = lowerSet + numberSet;

    const randomValues = new Uint32Array(length);
    crypto.getRandomValues(randomValues);

    let result = "";
    for (let i = 0; i < length; i++) {
      result += charPool[randomValues[i] % charPool.length];
    }
    return result;
  }

  function generatePassphrase(numWords = 4, separator = "-", capitalize = true) {
    const randomIndices = new Uint32Array(numWords);
    crypto.getRandomValues(randomIndices);

    const words = [];
    for (let i = 0; i < numWords; i++) {
      let word = DICENAME_WORDS[randomIndices[i] % DICENAME_WORDS.length];
      if (capitalize) word = word.charAt(0).toUpperCase() + word.slice(1);
      words.push(word);
    }
    return words.join(separator);
  }

  function calculateEntropy(pwd) {
    let poolSize = 0;
    if (/[a-z]/.test(pwd)) poolSize += 26;
    if (/[A-Z]/.test(pwd)) poolSize += 26;
    if (/[0-9]/.test(pwd)) poolSize += 10;
    if (/[^a-zA-Z0-9]/.test(pwd)) poolSize += 32;

    if (poolSize === 0 || pwd.length === 0) {
      return { bits: 0, strength: "Very Weak", crackTime: "Instant" };
    }

    const bits = Math.round(pwd.length * (Math.log(poolSize) / Math.log(2)));

    let strength = "Very Weak";
    let crackTime = "Instant";

    if (bits < 28) {
      strength = "Very Weak"; crackTime = "< 1 second";
    } else if (bits < 36) {
      strength = "Weak"; crackTime = "A few seconds";
    } else if (bits < 60) {
      strength = "Reasonable"; crackTime = "A few months";
    } else if (bits < 85) {
      strength = "Strong"; crackTime = "Thousands of years";
    } else {
      strength = "Very Strong"; crackTime = "Centuries / Unbreakable";
    }

    return { bits, strength, crackTime };
  }

  // =========================================================
  // 3. VISUAL TEXT DIFF ENGINE (Line-by-Line comparison)
  // =========================================================
  function computeLineDiff(textA, textB) {
    const linesA = textA.split(/\r?\n/);
    const linesB = textB.split(/\r?\n/);
    const diff = [];

    const max = Math.max(linesA.length, linesB.length);
    for (let i = 0; i < max; i++) {
      const a = linesA[i];
      const b = linesB[i];

      if (a === undefined) {
        diff.push({ type: "added", lineB: i + 1, content: b });
      } else if (b === undefined) {
        diff.push({ type: "removed", lineA: i + 1, content: a });
      } else if (a === b) {
        diff.push({ type: "unchanged", lineA: i + 1, lineB: i + 1, content: a });
      } else {
        diff.push({ type: "removed", lineA: i + 1, content: a });
        diff.push({ type: "added", lineB: i + 1, content: b });
      }
    }
    return diff;
  }

  return {
    md5,
    hashBuffer,
    hashText,
    generatePassword,
    generatePassphrase,
    calculateEntropy,
    computeLineDiff
  };

})();
