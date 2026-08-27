/**
 * Sitendra Mechanical Engineering & Physics Calculation Engine
 * 100% In-Browser Engineering Calculators, Beam Deflection (SFD/BMD), Gear Trains, Bolt Torques, and ISO 286 Fits.
 */

window.MechEngine = (function() {

  // =========================================================
  // 1. BEAM STRESS & DEFLECTION ENGINE
  // =========================================================
  const Materials = {
    steel: { name: "Structural Steel (E = 200 GPa)", E: 200e9, yield: 250e6 },
    aluminum: { name: "Aluminum 6061-T6 (E = 69 GPa)", E: 69e9, yield: 276e6 },
    titanium: { name: "Titanium Ti-6Al-4V (E = 114 GPa)", E: 114e9, yield: 880e6 },
    cast_iron: { name: "Gray Cast Iron (E = 100 GPa)", E: 100e9, yield: 200e6 },
    brass: { name: "Brass (E = 105 GPa)", E: 105e9, yield: 200e6 }
  };

  /**
   * Calculates Moment of Inertia (I) and Section Modulus (Z) for common cross-sections.
   * All dimensions in meters.
   */
  function calculateSectionProperties(shape, dims) {
    let I = 0; // m^4
    let Z = 0; // m^3
    let area = 0; // m^2

    if (shape === "rect") {
      const b = dims.width;
      const h = dims.height;
      I = (b * Math.pow(h, 3)) / 12;
      Z = (b * Math.pow(h, 2)) / 6;
      area = b * h;
    } else if (shape === "circle") {
      const d = dims.diameter;
      I = (Math.PI * Math.pow(d, 4)) / 64;
      Z = (Math.PI * Math.pow(d, 3)) / 32;
      area = (Math.PI * Math.pow(d, 2)) / 4;
    } else if (shape === "pipe") {
      const d_o = dims.outerDiameter;
      const d_i = dims.innerDiameter;
      I = (Math.PI * (Math.pow(d_o, 4) - Math.pow(d_i, 4))) / 64;
      Z = (Math.PI * (Math.pow(d_o, 4) - Math.pow(d_i, 4))) / (32 * d_o);
      area = (Math.PI * (Math.pow(d_o, 2) - Math.pow(d_i, 2))) / 4;
    } else if (shape === "ibeam") {
      const B = dims.flangeWidth;
      const H = dims.totalHeight;
      const tf = dims.flangeThickness;
      const tw = dims.webThickness;
      const innerH = H - 2 * tf;
      I = (B * Math.pow(H, 3) - (B - tw) * Math.pow(innerH, 3)) / 12;
      Z = I / (H / 2);
      area = 2 * (B * tf) + (innerH * tw);
    }

    return { I, Z, area };
  }

  /**
   * Solves beam reactions, max moment, max stress, max deflection, and generates SFD/BMD points.
   */
  function solveBeam(params) {
    const {
      type = "simply_supported", // 'simply_supported' or 'cantilever'
      loadType = "point", // 'point' or 'udl'
      L, // Length (m)
      P = 0, // Point load (N)
      a = L / 2, // Load position from left (m)
      w = 0, // UDL load (N/m)
      E, // Elastic modulus (Pa)
      I, // Moment of inertia (m^4)
      Z // Section modulus (m^3)
    } = params;

    let R_A = 0; // N
    let R_B = 0; // N
    let M_max = 0; // N*m
    let maxDeflection = 0; // m
    const numPoints = 100;
    const xPoints = [];
    const sfd = []; // Shear force (N)
    const bmd = []; // Bending moment (N*m)

    if (type === "simply_supported") {
      if (loadType === "point") {
        const b = L - a;
        R_A = (P * b) / L;
        R_B = (P * a) / L;
        M_max = (P * a * b) / L;

        // Max deflection for point load
        if (a === L / 2) {
          maxDeflection = (P * Math.pow(L, 3)) / (48 * E * I);
        } else {
          maxDeflection = (P * b * Math.pow(L * L - b * b, 1.5)) / (9 * Math.sqrt(3) * L * E * I);
        }

        for (let i = 0; i <= numPoints; i++) {
          const x = (i / numPoints) * L;
          xPoints.push(x);
          const V = x < a ? R_A : (x > a ? -R_B : 0);
          const M = x <= a ? R_A * x : R_A * x - P * (x - a);
          sfd.push(V);
          bmd.push(M);
        }
      } else if (loadType === "udl") {
        R_A = (w * L) / 2;
        R_B = (w * L) / 2;
        M_max = (w * Math.pow(L, 2)) / 8;
        maxDeflection = (5 * w * Math.pow(L, 4)) / (384 * E * I);

        for (let i = 0; i <= numPoints; i++) {
          const x = (i / numPoints) * L;
          xPoints.push(x);
          const V = R_A - w * x;
          const M = R_A * x - (w * Math.pow(x, 2)) / 2;
          sfd.push(V);
          bmd.push(M);
        }
      }
    } else if (type === "cantilever") {
      if (loadType === "point") {
        R_A = P;
        M_max = P * a;
        maxDeflection = (P * Math.pow(a, 2) * (3 * L - a)) / (6 * E * I);

        for (let i = 0; i <= numPoints; i++) {
          const x = (i / numPoints) * L;
          xPoints.push(x);
          const V = x <= a ? -P : 0;
          const M = x <= a ? -P * (a - x) : 0;
          sfd.push(V);
          bmd.push(M);
        }
      } else if (loadType === "udl") {
        R_A = w * L;
        M_max = (w * Math.pow(L, 2)) / 2;
        maxDeflection = (w * Math.pow(L, 4)) / (8 * E * I);

        for (let i = 0; i <= numPoints; i++) {
          const x = (i / numPoints) * L;
          xPoints.push(x);
          const V = -w * (L - x);
          const M = -(w * Math.pow(L - x, 2)) / 2;
          sfd.push(V);
          bmd.push(M);
        }
      }
    }

    const maxBendingStress = Z > 0 ? M_max / Z : 0; // Pa

    return {
      R_A,
      R_B,
      M_max,
      maxBendingStress,
      maxDeflection,
      xPoints,
      sfd,
      bmd
    };
  }

  // =========================================================
  // 2. GEAR TRAIN & TORQUE ENGINE
  // =========================================================
  function solveGearTrain(params) {
    const {
      N1, // Teeth on input gear (Pinion)
      N2, // Teeth on driven gear
      N3 = 0, // Teeth on output gear (if 3-gear train)
      module = 2.0, // Gear Module (mm)
      inputRPM = 1500, // RPM
      inputPowerKW = 5.0, // kW
      efficiency = 0.96 // Mechanical Efficiency
    } = params;

    let ratio = 0;
    let outputRPM = 0;
    let d1 = module * N1; // mm
    let d2 = module * N2; // mm
    let d3 = N3 > 0 ? module * N3 : 0; // mm
    let centerDist = 0; // mm

    if (N3 > 0) {
      // 3-Gear train (N2 is idler)
      ratio = N3 / N1;
      outputRPM = inputRPM / ratio;
      centerDist = (d1 + 2 * d2 + d3) / 2;
    } else {
      // 2-Gear simple pair
      ratio = N2 / N1;
      outputRPM = inputRPM / ratio;
      centerDist = (d1 + d2) / 2;
    }

    // Power & Torque (T = 9550 * P / n)
    const inputTorqueNm = inputRPM > 0 ? (9550 * inputPowerKW) / inputRPM : 0;
    const outputTorqueNm = inputTorqueNm * ratio * efficiency;
    const pitchLineVelocity = (Math.PI * (d1 / 1000) * inputRPM) / 60; // m/s

    return {
      ratio: parseFloat(ratio.toFixed(3)),
      outputRPM: parseFloat(outputRPM.toFixed(1)),
      inputTorqueNm: parseFloat(inputTorqueNm.toFixed(2)),
      outputTorqueNm: parseFloat(outputTorqueNm.toFixed(2)),
      d1: parseFloat(d1.toFixed(2)),
      d2: parseFloat(d2.toFixed(2)),
      d3: parseFloat(d3.toFixed(2)),
      centerDist: parseFloat(centerDist.toFixed(2)),
      pitchLineVelocity: parseFloat(pitchLineVelocity.toFixed(2))
    };
  }

  // =========================================================
  // 3. BOLT TIGHTENING TORQUE & PRELOAD ENGINE (VDI 2230 / ISO 898)
  // =========================================================
  const MetricBolts = {
    "M3": { d: 3, pitch: 0.5, As: 5.03 },
    "M4": { d: 4, pitch: 0.7, As: 8.78 },
    "M5": { d: 5, pitch: 0.8, As: 14.2 },
    "M6": { d: 6, pitch: 1.0, As: 20.1 },
    "M8": { d: 8, pitch: 1.25, As: 36.6 },
    "M10": { d: 10, pitch: 1.5, As: 58.0 },
    "M12": { d: 12, pitch: 1.75, As: 84.3 },
    "M14": { d: 14, pitch: 2.0, As: 115.0 },
    "M16": { d: 16, pitch: 2.0, As: 157.0 },
    "M20": { d: 20, pitch: 2.5, As: 245.0 },
    "M24": { d: 24, pitch: 3.0, As: 353.0 }
  };

  const BoltGrades = {
    "4.8": { Sy: 320, Sp: 310 }, // MPa
    "8.8": { Sy: 640, Sp: 580 }, // MPa (Standard high tensile)
    "10.9": { Sy: 940, Sp: 830 }, // MPa
    "12.9": { Sy: 1100, Sp: 970 } // MPa (Max strength socket cap)
  };

  function solveBoltTorque(params) {
    const {
      size = "M10",
      grade = "8.8",
      frictionCoeff = 0.14, // 0.14 = lightly oiled standard, 0.10 = anti-seize, 0.20 = dry
      preloadPercent = 85 // 85% of proof load
    } = params;

    const bolt = MetricBolts[size] || MetricBolts["M10"];
    const boltGrade = BoltGrades[grade] || BoltGrades["8.8"];

    // Proof load tension (N) = As * Sp * (percent / 100)
    const clampForceN = bolt.As * boltGrade.Sp * (preloadPercent / 100);
    const clampForceKN = clampForceN / 1000;

    // Torque formula: T = K * F_i * d
    // K (torque factor) approx = 0.16 + 0.5 * mu
    const K = 0.16 + 0.6 * frictionCoeff;
    const torqueNm = (K * clampForceN * (bolt.d / 1000));
    const torqueLbFt = torqueNm * 0.737562;

    return {
      size,
      grade,
      clampForceKN: parseFloat(clampForceKN.toFixed(2)),
      torqueNm: parseFloat(torqueNm.toFixed(2)),
      torqueLbFt: parseFloat(torqueLbFt.toFixed(2)),
      stressAreaMm2: bolt.As
    };
  }

  // =========================================================
  // 4. ISO 286 LIMITS & FITS TOLERANCE ENGINE
  // =========================================================
  const HoleTolerances = {
    // [lowerDev, upperDev] in micrometers (microns) for standard sizes ~25mm
    "H7": [0, 21],
    "H8": [0, 33],
    "H9": [0, 52],
    "JS7": [-10, 10],
    "P7": [-35, -14]
  };

  const ShaftTolerances = {
    "d9": [-117, -65],
    "e8": [-73, -40],
    "f7": [-41, -20],
    "g6": [-20, -7],
    "h6": [-13, 0],
    "js6": [-6.5, 6.5],
    "k6": [2, 15],
    "m6": [8, 21],
    "p6": [22, 35],
    "s6": [35, 48]
  };

  function solveLimitsAndFits(nominalMm, holeCode = "H7", shaftCode = "g6") {
    const hTol = HoleTolerances[holeCode] || [0, 21];
    const sTol = ShaftTolerances[shaftCode] || [-20, -7];

    // Scale tolerance deviations proportionally with nominal size (approx ISO factor)
    const factor = Math.pow(nominalMm / 25, 0.35);
    const holeLowerUm = parseFloat((hTol[0] * factor).toFixed(1));
    const holeUpperUm = parseFloat((hTol[1] * factor).toFixed(1));

    const shaftLowerUm = parseFloat((sTol[0] * factor).toFixed(1));
    const shaftUpperUm = parseFloat((sTol[1] * factor).toFixed(1));

    const holeMinMm = nominalMm + holeLowerUm / 1000;
    const holeMaxMm = nominalMm + holeUpperUm / 1000;

    const shaftMinMm = nominalMm + shaftLowerUm / 1000;
    const shaftMaxMm = nominalMm + shaftUpperUm / 1000;

    const maxClearanceUm = holeUpperUm - shaftLowerUm;
    const minClearanceUm = holeLowerUm - shaftUpperUm;

    let fitType = "Clearance Fit";
    if (minClearanceUm < 0 && maxClearanceUm > 0) {
      fitType = "Transition Fit";
    } else if (maxClearanceUm <= 0) {
      fitType = "Interference (Press) Fit";
    }

    return {
      nominalMm,
      holeCode,
      shaftCode,
      fitType,
      holeLowerUm,
      holeUpperUm,
      shaftLowerUm,
      shaftUpperUm,
      holeMinMm: parseFloat(holeMinMm.toFixed(4)),
      holeMaxMm: parseFloat(holeMaxMm.toFixed(4)),
      shaftMinMm: parseFloat(shaftMinMm.toFixed(4)),
      shaftMaxMm: parseFloat(shaftMaxMm.toFixed(4)),
      maxClearanceUm: parseFloat(maxClearanceUm.toFixed(1)),
      minClearanceUm: parseFloat(minClearanceUm.toFixed(1))
    };
  }

  return {
    Materials,
    calculateSectionProperties,
    solveBeam,
    solveGearTrain,
    solveBoltTorque,
    solveLimitsAndFits
  };

})();
