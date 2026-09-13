# AGENTS.md: Development Guide for Autonomous & Pair-Programming Agents

Welcome to the **Soft Copy to Hard Copy** repository. This document establishes guidelines, architectural principles, coding conventions, and operational workflows for AI agents, automated contributors, and developer pairs interacting with this codebase.

---

## 1. Project Overview & Philosophy

**Soft Copy to Hard Copy** is an end-to-end cyber-physical system that transforms digital text, PDFs, and notes into authentic handwritten documents. The repository serves two complementary output modes:

1. **Printable Mode (High-Resolution Visual Physics):**
   * Produces 300–600 DPI PDFs and raster images mimicking physical paper, ruled margins, ink absorption, and ballpoint pressure.
   * Supports both complete ruled notebook simulation and plain A4 unruled sheet layouts (ideal for direct notebook paper feeding into standard printers).
2. **Real-Pen Plotter Mode (Robotic CNC Actuation):**
   * Compiles vector trajectory splines $(x_t, y_t, p_t)$ into ISO G-code for GRBL v1.1 CNC shields and CoreXY pen plotters.
   * Solves the **"hollow outline"** dilemma of standard fonts using morphological centerline skeletonization (Zhang-Suen thinning) to yield genuine 1-line toolpaths for real ballpoint and gel pens.
   * Optimizes toolpaths via the **Traveling Salesperson Problem (TSP 2-Opt)** to minimize non-drawing air-moves by $>35\%$.

---

## 2. Directory Structure & Key Files

```
.
├── .gitignore                      # Excludes generated sample outputs (*.png, *.pdf, *.gcode)
├── AGENTS.md                       # This developer & agent instruction manual
├── README.md                       # High-impact user & academic documentation (SEO optimized)
├── PROJECT_BLUEPRINT.md            # Comprehensive research specification, literature review, & BOM
├── requirements.txt                # Python package dependencies
│
├── core_engine.py                  # Core parametric spline generator, TSP 2-Opt optimizer, GRBL compiler
├── font_to_single_stroke_plotter.py# Centerline skeletonizer (TTF -> 1-line toolpath for plotters)
├── generate_realistic_notebook.py  # Ruled notebook simulation generator (blue ink, red margins)
├── enhanced_plain_generator.py     # Plain sheet generator (unruled A4) + style comparison engine
└── generate_a4_cursive_pdf.py      # Standard A4 cursive document generator (Segoe Script, 300 DPI)
```

---

## 3. Core Architectural Principles for Agents

When extending, refactoring, or querying this codebase, agents MUST adhere to the following rules:

### Rule 1: Distinguish Outline Fonts from Single-Stroke Plotter Toolpaths
* Standard desktop fonts (`.ttf`, `.otf`) are closed boundary polygons.
* **Never** feed raw font outlines directly to a pen plotter. Always pass them through:
  * Centerline extraction (`font_to_single_stroke_plotter.py`), or
  * Native single-stroke libraries (`ParametricGlyphLibrary` in `core_engine.py`), or
  * Hershey / OPF vector stroke files.

### Rule 2: Biomechanical Noise Must Be Natural, Not Random Jitter
* Do not apply pure uniform white noise to character coordinates.
* Always use **low-pass filtered Gaussian noise** (Ornstein-Uhlenbeck process) for neuromuscular tremor and **multi-frequency sinusoidal functions** for baseline wander along horizontal spans.

### Rule 3: Maintain Mechanical Compatibility with GRBL v1.1
* Stepper motions: `G0` for rapid air traverses, `G1` with explicit feedrates (`F1200` to `F4000`) for drawing.
* Servo pen-lift: `M3 S[angle]` for pen drop (typically `S45`), `M3 S0` or `M5` for pen lift.
* Dwell pauses: Always inject `G4 P0.06` (60ms) immediately after pen-up or pen-down commands to allow the RC servo horn to complete its physical stroke before the XY steppers accelerate.

### Rule 4: Preserve Output Separation in Git
* Binary output files (`*.png`, `*.pdf`, `*.svg`, `*.gcode`) are excluded in `.gitignore` by design.
* Agents must not commit generated sample binaries unless explicitly instructed by the repository maintainer. Keep the repository lightweight, pure, and focused on code, algorithms, and documentation.

---

## 4. Environment & Command Execution

### Python Environment
* Python version: **Python 3.10+** (compatible with 3.8 through 3.12).
* Run test executions with:
  ```bash
  python core_engine.py
  python font_to_single_stroke_plotter.py
  python generate_a4_cursive_pdf.py
  ```

### Adding New Handwriting Fonts
* To introduce a new font, locate the `.ttf` or `.otf` file.
* In scripts like `enhanced_plain_generator.py` or `generate_a4_cursive_pdf.py`, pass the font path into `ImageFont.truetype(font_path, font_size)`.
* Standard Windows handwriting fonts (`Inkfree.ttf`, `segoepr.ttf`, `segoesc.ttf`, `LHANDW.TTF`) reside in `C:/Windows/Fonts/`.
* Downloadable open-source fonts (*Kalam*, *Caveat*, *Patrick Hand*) can be downloaded directly into the repository root.

---

## 5. Ethical Guidelines & Security Boundaries

* **No Signature / Stamp / Seal Generation:** This system is strictly engineered for student notes, study aids, and academic productivity. Under no circumstances should agents assist in forging signatures, official administrative seals, identity papers, or examination answer credentials.
* **Consent Verification:** In style-cloning workflows, verify that style samples are provided with the explicit permission of the original author.
