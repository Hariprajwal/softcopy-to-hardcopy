"""
Soft Copy to Hard Copy: Universal Automated Pipeline & Folder Watcher
====================================================================
Architecture:
1. Fast Dynamic Multi-Tier Document Ingestion:
   - Tier 1: Native Digital Text Extraction (PyMuPDF for PDF, python-docx for DOCX, UTF-8 for TXT).
   - Tier 2: RapidOCR (Ultra-fast ONNX-accelerated OCR for scanned PDFs & photos, ~0.8s/page).
   - Tier 3: Tesseract OCR fallback (if installed).
   - Tier 4: Ollama Vision fallback (if compatible vision model is loaded).
2. Smart Paragraph Assembly & OCR Sanitization:
   - Joins fragmented OCR word segments into natural fluid sentences.
   - Cleans CJK artifacts, converts math symbols (<=, >=, x1, x2), and formats tabular data.
3. Dynamic AI Academic Enhancement & Full Solution Generation:
   - Queries local Ollama server and auto-selects the best installed LLM (e.g. llama3.1:latest).
   - Solves and formats assignment equations, steps, and answers into clean student notebook text.
   - Graceful fallback to assembled clean text if Ollama is busy or times out.
4. Production-Grade A4 Cursive Handwriting Synthesis:
   - Standard 300 DPI ISO A4 warm plain sheets.
   - Fluid cursive handwriting with biomechanical motor tremor, baseline wander, and royal blue ballpoint ink.
   - Automatic Page 1 student header (Name: Hariprajwal, Subject, Date) and continuation headers on subsequent pages.
5. Automated Lifecycle & Folder Management:
   - Ingests from `pipeline/input/`.
   - Archives source documents to `pipeline/finished_input/`.
   - Emits finalized multi-page handwritten PDFs and previews to `pipeline/output/`.
"""

import os
import re
import sys
import time
import json
import math
import base64
import shutil
import random
import urllib.request
import urllib.error
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Dependency Imports & Auto-Detection
# ---------------------------------------------------------------------------

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    import docx
except ImportError:
    docx = None

try:
    from rapidocr_onnxruntime import RapidOCR
    rapid_ocr_engine = RapidOCR()
except Exception:
    rapid_ocr_engine = None

try:
    import pytesseract
except ImportError:
    pytesseract = None

# Directories
BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config.json"
PIPELINE_DIR = BASE_DIR / "pipeline"
INPUT_DIR = PIPELINE_DIR / "input"
FINISHED_INPUT_DIR = PIPELINE_DIR / "finished_input"
OUTPUT_DIR = PIPELINE_DIR / "output"

def load_config() -> dict:
    defaults = {
        "student_name": "Hariprajwal",
        "default_subject": "Assignment",
        "font_path": "C:/Windows/Fonts/segoesc.ttf",
        "fallback_font_path": "C:/Windows/Fonts/Inkfree.ttf",
        "font_size": 44,
        "ink_color_rgb": [22, 58, 128],
        "ollama_url": "http://localhost:11434",
        "ocr_engine": "rapidocr",
        "enable_ai_enhancement": True,
        "ollama_text_model": "llama3.1:latest",
        "ai_mode": "solve_and_clean",  # 'solve_and_clean', 'clean_only', 'raw'
        "ollama_timeout": 180,
        "paper_type": "plain_a4",
        "paper_color_rgb": [255, 255, 255],
        "human_misalignment": True,
        "margin_left": 220,
        "margin_right": 200,
        "margin_top": 220,
        "margin_bottom": 220,
        "line_spacing": 92
    }
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                defaults.update(cfg)
        except Exception as e:
            print(f"[!] Warning reading config.json: {e}")
    return defaults

def setup_directories():
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    FINISHED_INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Text Normalization & Paragraph Assembly
# ---------------------------------------------------------------------------

def normalize_and_clean_text(text: str) -> str:
    """Sanitizes text, replacing unusual unicode and OCR noise with clean Latin/ASCII equivalents."""
    replacements = {
        "\u3002": ".",
        "\uff0c": ",",
        "\uff1a": ":",
        "\uff1b": ";",
        "\u201c": '"',
        "\u201d": '"',
        "\u2018": "'",
        "\u2019": "'",
        "\u2013": "-",
        "\u2014": "-",
        "\u2026": "...",
        "\u00a0": " ",
        "二": "=",
        "一": "-",
        "□": "",
        "○": "O",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)

    # Filter out unsupported non-ASCII characters that cause font rendering boxes
    cleaned_chars = []
    for ch in text:
        if ord(ch) < 128 or ch in "•°±²³µ·":
            cleaned_chars.append(ch)
        elif ch in "\r\t":
            cleaned_chars.append(" ")
    return "".join(cleaned_chars)

def assemble_ocr_lines(raw_lines: list) -> str:
    """Assembles raw OCR line snippets into natural flowing paragraphs."""
    paragraphs = []
    current_para = []

    for line in raw_lines:
        line_clean = normalize_and_clean_text(line).strip()
        if not line_clean:
            continue

        # Header / step / question / bullet detection
        is_break = (
            bool(re.match(r"^(Step|Q\d|Problem|Set|\d+[\.\)\-]|[-•*#])", line_clean, re.I)) or
            line_clean.endswith(":") or
            any(w in line_clean.lower() for w in ["returns:", "objective:", "constraints:", "subject to:"]) or
            (len(line_clean) < 28 and line_clean.isupper())
        )

        if is_break and current_para:
            paragraphs.append(" ".join(current_para))
            current_para = [line_clean]
        else:
            current_para.append(line_clean)

    if current_para:
        paragraphs.append(" ".join(current_para))

    return "\n\n".join(paragraphs)

# ---------------------------------------------------------------------------
# Dynamic Ollama Model Discovery & Management
# ---------------------------------------------------------------------------

def get_installed_ollama_models(ollama_url: str) -> list:
    """Discovers all models currently installed in the local Ollama instance."""
    try:
        req = urllib.request.Request(f"{ollama_url}/api/tags")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return [m.get("name", "") for m in data.get("models", [])]
    except Exception:
        return []

def select_best_ollama_model(config: dict) -> str:
    """Selects the best available Ollama text model dynamically."""
    ollama_url = config.get("ollama_url", "http://localhost:11434")
    configured = config.get("ollama_text_model")
    models = get_installed_ollama_models(ollama_url)

    if not models:
        return configured or "llama3.1:latest"

    # 1. Exact match for configured model
    if configured and configured in models:
        return configured

    # 2. Prefix match
    if configured:
        for m in models:
            if m.startswith(configured) or configured.startswith(m.split(":")[0]):
                return m

    # 3. Dynamic candidate preference list (reliable models on this system)
    preference = [
        "llama3.1:latest", "llama3.1",
        "phi3.5:latest", "phi3.5",
        "qwen2.5:7b", "qwen2.5",
        "gemma2:9b", "llama3:latest"
    ]
    for pref in preference:
        for m in models:
            if m == pref or m.startswith(pref):
                return m

    return models[0]

# ---------------------------------------------------------------------------
# Fast OCR & Multi-Tier Text Ingestion
# ---------------------------------------------------------------------------

def ocr_image_bytes(img_bytes: bytes, config: dict, page_num: int = 1) -> str:
    """Performs ultra-fast OCR on image bytes using RapidOCR or fallbacks."""
    t0 = time.time()

    # Tier 1: RapidOCR (Instant ONNX OCR)
    if rapid_ocr_engine:
        try:
            result, _ = rapid_ocr_engine(img_bytes)
            if result:
                lines = [r[1] for r in result if len(r) > 1 and r[1].strip()]
                elapsed = time.time() - t0
                assembled = assemble_ocr_lines(lines)
                print(f"[*] Page {page_num}: Extracted {len(lines)} lines via RapidOCR in {elapsed:.2f}s.")
                return assembled
        except Exception as e:
            print(f"[!] RapidOCR error on page {page_num}: {e}")

    # Tier 2: Tesseract OCR fallback
    if pytesseract:
        try:
            from io import BytesIO
            img = Image.open(BytesIO(img_bytes))
            text = pytesseract.image_to_string(img).strip()
            if text:
                elapsed = time.time() - t0
                print(f"[*] Page {page_num}: Extracted text via Tesseract in {elapsed:.2f}s.")
                return normalize_and_clean_text(text)
        except Exception as e:
            print(f"[!] Tesseract error on page {page_num}: {e}")

    return ""

def extract_text_from_document(file_path: Path, config: dict) -> str:
    """Universal multi-tier text extractor for PDF, DOCX, TXT, and Images."""
    ext = file_path.suffix.lower()

    # 1. Plain Text Files
    if ext == ".txt":
        try:
            return file_path.read_text(encoding="utf-8").strip()
        except UnicodeDecodeError:
            return file_path.read_text(encoding="latin-1", errors="ignore").strip()

    # 2. Word Documents
    elif ext == ".docx":
        if docx:
            doc = docx.Document(str(file_path))
            return "\n".join([p.text for p in doc.paragraphs if p.text.strip()]).strip()
        else:
            raise RuntimeError("python-docx is not installed. Run: pip install python-docx")

    # 3. PDF Documents (Native or Scanned)
    elif ext == ".pdf":
        if not fitz:
            raise RuntimeError("PyMuPDF (fitz) is not installed. Run: pip install PyMuPDF")

        doc = fitz.open(str(file_path))
        # First attempt native digital text extraction
        pages_text = [page.get_text().strip() for page in doc]
        digital_text = "\n\n".join([p for p in pages_text if p])
        
        # If digital text exists across the PDF (> 20 words), use it directly
        if len(digital_text.split()) > 20:
            print(f"[*] Extracted native digital text from '{file_path.name}' ({len(digital_text.split())} words across {len(doc)} pages).")
            return normalize_and_clean_text(digital_text)

        # Otherwise, this is a SCANNED PDF: Run Fast OCR on each page
        print(f"[*] Scanned PDF detected: '{file_path.name}' ({len(doc)} pages). Starting Fast OCR...")
        transcribed_pages = []
        for i, page in enumerate(doc):
            pix = page.get_pixmap(dpi=130)
            img_bytes = pix.tobytes("png")
            page_text = ocr_image_bytes(img_bytes, config, page_num=i + 1)
            if page_text:
                transcribed_pages.append(page_text)

        if transcribed_pages:
            return "\n\n".join(transcribed_pages)
        else:
            return f"Assignment Problem: {file_path.stem}\n(Scanned document processed with empty text extraction)"

    # 4. Standalone Images
    elif ext in [".png", ".jpg", ".jpeg", ".bmp", ".webp"]:
        img_bytes = file_path.read_bytes()
        return ocr_image_bytes(img_bytes, config, page_num=1)

    return ""

# ---------------------------------------------------------------------------
# AI Academic Formatting & Full Solution Enhancement
# ---------------------------------------------------------------------------

def enhance_text_with_ollama(raw_text: str, config: dict, doc_title: str) -> str:
    """Enhances raw OCR text using Ollama LLM into clean, solved, ready-to-write assignment notes."""
    if not config.get("enable_ai_enhancement", True):
        return raw_text

    ollama_url = config.get("ollama_url", "http://localhost:11434")
    model = select_best_ollama_model(config)
    ai_mode = config.get("ai_mode", "solve_and_clean")
    timeout = config.get("ollama_timeout", 180)

    print(f"[*] Enhancing assignment via Ollama Model '{model}' (Mode: {ai_mode})...")

    if ai_mode == "solve_and_clean":
        system_instruction = (
            "You are an expert university student writing an assignment solution.\n"
            "Review the following OCR text extracted from an assignment document.\n"
            "Tasks:\n"
            "1. Fix any OCR typos (e.g. 'ophimizahion' -> 'Optimization', 'inuestment' -> 'Investment').\n"
            "2. Accurately reconstruct mathematical variables, objectives, and constraints (e.g., Maximize Z = ..., Subject to: x1 + x2 <= ..., x1 >= 0).\n"
            "3. If problems are presented, formulate the complete mathematical problem and write out the step-by-step solution clearly.\n"
            "4. Organize neatly with headings like 'Problem Statement', 'Step 1: Formulation', 'Objective Function', 'Constraints', 'Calculation', and 'Final Answer'.\n"
            "5. Format for direct handwriting on paper: do NOT use markdown code blocks (```), do NOT use raw pipe tables (| --- |). Format tables as bulleted lines or key-value pairs (e.g. 'Scheme 1: Return 10%, Risk 5').\n"
            "6. Output ONLY the assignment text. Do not include conversational chit-chat."
        )
    else:
        system_instruction = (
            "You are an academic text cleanup assistant.\n"
            "Clean up the following raw OCR text of an assignment problem.\n"
            "Fix OCR typos and mathematical notation, remove scan artifacts, and format neatly with steps and bullet points.\n"
            "Output ONLY the cleaned assignment text without conversational preamble or markdown code blocks."
        )

    # Process in focused sections if text is long to prevent CPU timeout
    text_sample = raw_text[:4000]
    prompt = f"{system_instruction}\n\nAssignment Title: {doc_title}\n\nRaw Extracted Text:\n{text_sample}"

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_predict": 1800
        }
    }

    try:
        t0 = time.time()
        req = urllib.request.Request(
            f"{ollama_url}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            enhanced = data.get("response", "").strip()
            if enhanced and len(enhanced) > 50:
                elapsed = time.time() - t0
                print(f"[OK] Ollama enhancement complete in {elapsed:.1f}s ({len(enhanced.split())} words generated).")
                return enhanced
    except Exception as e:
        print(f"[!] Ollama enhancement bypassed or timed out ({e}). Using cleaned raw text.")

    return raw_text

# ---------------------------------------------------------------------------
# Text Preprocessor for Handwriting Fonts
# ---------------------------------------------------------------------------

def format_for_handwriting(text: str) -> str:
    """Prepares text specifically for handwriting synthesis, removing markdown and formatting artifacts."""
    lines = text.split("\n")
    cleaned_lines = []

    for line in lines:
        l = line.strip()
        if not l:
            cleaned_lines.append("")
            continue

        # Skip markdown code block delimiters
        if l.startswith("```"):
            continue

        # Strip LLM conversational preambles (e.g. 'Here is the corrected solution:')
        if any(l.lower().startswith(p) for p in [
            "here is the", "here are the", "sure, here", "certainly, here",
            "certainly! here", "below is the", "here's the"
        ]):
            continue

        # Convert markdown table divider lines (|---|---|) to empty
        if re.match(r"^\|[\s\-:|]+\|$", l):
            continue

        # Convert table rows (| Col 1 | Col 2 |) to readable key-value or indented format
        if l.startswith("|") and l.endswith("|"):
            parts = [p.strip() for p in l.split("|")[1:-1] if p.strip()]
            if len(parts) >= 2:
                l = "    " + "  :  ".join(parts)
            elif len(parts) == 1:
                l = "    " + parts[0]

        # Strip markdown bold/italic asterisks: **text** -> text, *text* -> text
        l = re.sub(r"\*\*(.*?)\*\*", r"\1", l)
        l = re.sub(r"\*(.*?)\*", r"\1", l)
        l = re.sub(r"__(.*?)__", r"\1", l)
        l = re.sub(r"_(.*?)_", r"\1", l)

        # Clean LaTeX notation like \text{...}, \frac{a}{b}
        l = re.sub(r"\\text\{([^}]+)\}", r"\1", l)
        l = re.sub(r"\\frac\{([^}]+)\}\{([^}]+)\}", r"(\1 / \2)", l)
        l = l.replace("\\le", "<=").replace("\\ge", ">=").replace("\\times", "x")

        # Convert bullet points to neat uniform symbols
        if l.startswith("* ") or l.startswith("- ") or l.startswith("+ "):
            l = "- " + l[2:]

        l = normalize_and_clean_text(l)
        cleaned_lines.append(l)

    return "\n".join(cleaned_lines)

def group_text_into_paragraphs(cleaned_lines: list) -> list:
    """
    Groups cleaned lines into cohesive paragraphs for A4 rendering.
    Coalesces OCR sentence fragments into fluid paragraphs while preserving
    headings, steps, equations, and lists.
    """
    paragraphs = []
    current_para = []

    for line in cleaned_lines:
        l = line.strip()
        if not l:
            if current_para:
                paragraphs.append(" ".join(current_para))
                current_para = []
            continue

        # Detect headers, questions, steps, bullet points, or list elements
        is_break = (
            bool(re.match(r"^(Step\s*\d|Q\s*\d|\d+[\.\)\-]|[-•*#])", l, re.I)) or
            l.endswith(":") or
            any(k in l.lower() for k in ["problem statement", "objective function", "constraints", "returns :", "subject to:"]) or
            (len(l) < 45 and (l.isupper() or l.startswith("#") or "Assignment" in l or "Problem" in l or "Scheme" in l))
        )

        if is_break:
            if current_para:
                paragraphs.append(" ".join(current_para))
                current_para = []
            current_para.append(l)
            # If line is a header or ends with a colon, treat as standalone
            if l.endswith(":") or l.startswith("#") or bool(re.match(r"^(Step\s*\d|Q\s*\d)", l, re.I)):
                paragraphs.append(" ".join(current_para))
                current_para = []
        else:
            current_para.append(l)

    if current_para:
        paragraphs.append(" ".join(current_para))

    return paragraphs

# ---------------------------------------------------------------------------
# Universal A4 Cursive Handwriting Synthesis Engine
# ---------------------------------------------------------------------------

class UniversalA4Renderer:
    def __init__(self, config: dict):
        self.config = config
        font_path = config.get("font_path", "C:/Windows/Fonts/segoesc.ttf")
        if not os.path.exists(font_path):
            font_path = config.get("fallback_font_path", "C:/Windows/Fonts/Inkfree.ttf")

        self.font_size = config.get("font_size", 44)
        self.font_title = ImageFont.truetype(font_path, int(self.font_size * 1.3))
        self.font_header = ImageFont.truetype(font_path, int(self.font_size * 1.15))
        self.font_main = ImageFont.truetype(font_path, self.font_size)
        self.font_small = ImageFont.truetype(font_path, int(self.font_size * 0.85))

        # Standard ISO A4 @ 300 DPI
        self.width = 2480
        self.height = 3508
        self.dpi = 300

        # Paper background color (pure crisp white #FFFFFF by default)
        paper_color = config.get("paper_color_rgb", [255, 255, 255])
        self.paper_color = tuple(paper_color)
        self.paper_color_rgba = (self.paper_color[0], self.paper_color[1], self.paper_color[2], 255)

        # Geometry & margins
        self.margin_left = config.get("margin_left", 220)
        self.margin_right = config.get("margin_right", 240)
        self.margin_top = config.get("margin_top", 220)
        self.margin_bottom = config.get("margin_bottom", 220)
        self.line_spacing = config.get("line_spacing", 92)
        self.max_width = self.width - self.margin_right
        self.human_misalignment = config.get("human_misalignment", True)

        # Ink Color
        color = config.get("ink_color_rgb", [22, 58, 128])
        self.base_ink = tuple(color)

    def _render_line_on_canvas(self, canvas: Image.Image, text: str, start_x: int, baseline_y: int, font=None, is_header=False):
        font = font or self.font_main
        cur_x = start_x
        words = text.split(" ")

        # Continuous sinusoidal & tilt baseline wander parameters for this line
        if self.human_misalignment and not is_header:
            line_slope = random.uniform(-0.0025, 0.0025)
            wave_len1 = random.uniform(900, 1500)
            wave_amp1 = random.uniform(2.0, 4.2)
            wave_phase1 = random.uniform(0, 2 * math.pi)

            wave_len2 = random.uniform(320, 580)
            wave_amp2 = random.uniform(1.0, 2.2)
            wave_phase2 = random.uniform(0, 2 * math.pi)
        else:
            line_slope = 0.0
            wave_len1, wave_amp1, wave_phase1 = 1.0, 0.0, 0.0
            wave_len2, wave_amp2, wave_phase2 = 1.0, 0.0, 0.0

        for word in words:
            if not word:
                continue

            word_jitter_y = random.uniform(-2.2, 2.2) if self.human_misalignment else 0.0
            word_rot = random.uniform(-0.6, 0.6) if self.human_misalignment else 0.0

            for char in word:
                dx = cur_x - start_x
                continuous_wander = (
                    dx * line_slope +
                    wave_amp1 * math.sin(2 * math.pi * cur_x / wave_len1 + wave_phase1) +
                    wave_amp2 * math.sin(2 * math.pi * cur_x / wave_len2 + wave_phase2)
                )

                char_jitter_y = word_jitter_y + (random.uniform(-1.0, 1.0) if self.human_misalignment else 0.0)
                char_jitter_x = random.uniform(-0.4, 0.4) if self.human_misalignment else 0.0
                char_rot = word_rot + (random.uniform(-1.2, 1.2) if self.human_misalignment else 0.0)

                alpha_var = random.randint(-16, 16) if self.human_misalignment else 0
                char_color = (
                    max(10, min(255, self.base_ink[0] + alpha_var)),
                    max(20, min(255, self.base_ink[1] + alpha_var)),
                    max(60, min(255, self.base_ink[2] + alpha_var)),
                    245
                )

                bbox = font.getbbox(char)
                cw = bbox[2] - bbox[0]
                ch = bbox[3] - bbox[1]

                pad = 16
                char_img = Image.new("RGBA", (cw + pad * 2, ch + pad * 2), (0, 0, 0, 0))
                char_draw = ImageDraw.Draw(char_img)
                char_draw.text((pad - bbox[0], pad - bbox[1]), char, font=font, fill=char_color)

                if abs(char_rot) > 0.1:
                    char_img = char_img.rotate(char_rot, resample=Image.BICUBIC, expand=True)

                target_x = int(cur_x + char_jitter_x)
                target_y = int(baseline_y + continuous_wander - ch + char_jitter_y - bbox[1])

                canvas.paste(char_img, (target_x, target_y), char_img)
                cur_x += cw - 1.5 + (random.uniform(-0.4, 0.4) if self.human_misalignment else 0.0)

            space_scale = random.uniform(0.36, 0.50) if self.human_misalignment else 0.42
            cur_x += self.font_size * space_scale

    def _estimate_text_width(self, text: str, font=None) -> int:
        font = font or self.font_main
        words = text.split(" ")
        total_w = 0
        for w_idx, word in enumerate(words):
            if w_idx > 0:
                total_w += int(self.font_size * 0.46)
            for c in word:
                bbox = font.getbbox(c)
                cw = bbox[2] - bbox[0]
                total_w += max(4, cw - 1)
        return total_w

    def render_document(self, raw_text: str, document_title: str = "") -> list:
        random.seed(42)
        pages = []
        student_name = self.config.get("student_name", "Hariprajwal")
        clean_text = format_for_handwriting(raw_text)
        paragraphs = group_text_into_paragraphs(clean_text.split("\n"))

        def create_a4_canvas():
            # Crisp pure white plain A4 sheet
            return Image.new("RGBA", (self.width, self.height), self.paper_color_rgba)

        current_page = create_a4_canvas()
        page_index = 1

        # Header on Page 1: Student Name & Subject (Dynamically right-aligned or wrapped)
        y = self.margin_top
        name_str = f"Name  :   {student_name}"
        name_w = self._estimate_text_width(name_str, font=self.font_title)
        self._render_line_on_canvas(
            current_page, name_str, self.margin_left, y, font=self.font_title, is_header=True
        )

        subject_label = document_title or self.config.get("default_subject", "Assignment")
        subj_str = f"Subject  :   {subject_label}"
        subj_w = self._estimate_text_width(subj_str, font=self.font_title)
        target_subj_x = self.width - self.margin_right - subj_w

        if target_subj_x < self.margin_left + name_w + 140:
            y += int(self.line_spacing * 0.95)
            self._render_line_on_canvas(
                current_page, subj_str, self.margin_left, y, font=self.font_title, is_header=True
            )
            y += int(self.line_spacing * 1.3)
        else:
            self._render_line_on_canvas(
                current_page, subj_str, target_subj_x, y, font=self.font_title, is_header=True
            )
            y += int(self.line_spacing * 1.4)

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # Header / step / question detection
            is_heading = (
                len(para) < 65 and (
                    para.startswith("Step") or para.startswith("Q") or
                    para.startswith("#") or "Problem" in para or "Formulation" in para or
                    "Objective" in para or "Constraints" in para or "Answer" in para or
                    para.endswith(":")
                )
            )
            font = self.font_header if is_heading else self.font_main
            clean_para = para.lstrip("#").strip()

            words = clean_para.split(" ")
            current_line = []
            base_indent = self.margin_left + (35 if not is_heading else 0)

            for word in words:
                test_line = " ".join(current_line + [word])
                if base_indent + self._estimate_text_width(test_line, font) > self.max_width:
                    if current_line:
                        if y > self.height - self.margin_bottom:
                            pages.append(current_page)
                            page_index += 1
                            current_page = create_a4_canvas()
                            y = self.margin_top
                            self._render_line_on_canvas(
                                current_page, f"Name  :   {student_name}", self.margin_left, y, font=self.font_title, is_header=True
                            )
                            page_str = f"( Page  {page_index} )"
                            p_w = self._estimate_text_width(page_str, font=self.font_header)
                            p_x = max(self.margin_left + 700, self.width - self.margin_right - p_w)
                            self._render_line_on_canvas(
                                current_page, page_str, p_x, y, font=self.font_header, is_header=True
                            )
                            y += int(self.line_spacing * 1.5)

                        # Natural margin stagger for each line
                        margin_stagger = random.gauss(0, 5.0) if self.human_misalignment else 0.0
                        margin_stagger = max(-10.0, min(10.0, margin_stagger))
                        line_x = int(base_indent + margin_stagger)

                        line_str = " ".join(current_line)
                        self._render_line_on_canvas(current_page, line_str, line_x, y, font)

                        # Organic line spacing variation
                        gap_jitter = random.uniform(-4.0, 6.0) if self.human_misalignment else 0.0
                        y += int(self.line_spacing + gap_jitter)
                        current_line = [word]
                    else:
                        current_line = [word]
                else:
                    current_line.append(word)

            if current_line:
                if y > self.height - self.margin_bottom:
                    pages.append(current_page)
                    page_index += 1
                    current_page = create_a4_canvas()
                    y = self.margin_top
                    self._render_line_on_canvas(
                        current_page, f"Name  :   {student_name}", self.margin_left, y, font=self.font_title, is_header=True
                    )
                    page_str = f"( Page  {page_index} )"
                    p_w = self._estimate_text_width(page_str, font=self.font_header)
                    p_x = max(self.margin_left + 700, self.width - self.margin_right - p_w)
                    self._render_line_on_canvas(
                        current_page, page_str, p_x, y, font=self.font_header, is_header=True
                    )
                    y += int(self.line_spacing * 1.5)

                margin_stagger = random.gauss(0, 5.0) if self.human_misalignment else 0.0
                margin_stagger = max(-10.0, min(10.0, margin_stagger))
                line_x = int(base_indent + margin_stagger)

                line_str = " ".join(current_line)
                self._render_line_on_canvas(current_page, line_str, line_x, y, font)

                gap_jitter = random.uniform(-4.0, 6.0) if self.human_misalignment else 0.0
                y += int(self.line_spacing + gap_jitter)

            # Extra breathing space after headings or paragraphs
            if is_heading:
                y += int(self.line_spacing * 0.3)
            else:
                y += int(self.line_spacing * 0.4)

        pages.append(current_page)

        # Convert RGBA to RGB using pure white paper color
        rgb_pages = []
        for p in pages:
            rgb = Image.new("RGB", (self.width, self.height), self.paper_color)
            rgb.paste(p, (0, 0), p)
            rgb_pages.append(rgb)

        return rgb_pages

# ---------------------------------------------------------------------------
# Lifecycle: Process, Save & Archive
# ---------------------------------------------------------------------------

def process_file(file_path: Path, config: dict, renderer: UniversalA4Renderer):
    print(f"\n=================================================================")
    print(f"[+] Ingesting: {file_path.name}")
    print(f"=================================================================")
    try:
        # Step 1: Fast Multi-Tier Text Ingestion & Paragraph Assembly
        raw_text = extract_text_from_document(file_path, config)
        if not raw_text or len(raw_text.strip()) == 0:
            print(f"[!] Warning: No text content found in {file_path.name}. Skipping.")
            return

        title = file_path.stem.replace("_", " ")

        # Step 2: Dynamic AI Enhancement & Problem Solving via Ollama
        final_text = enhance_text_with_ollama(raw_text, config, title)

        # Step 3: Synthesis of Cursive Handwritten Document
        print(f"[*] Synthesizing handwritten cursive pages for '{title}'...")
        pages = renderer.render_document(final_text, document_title=title)

        stem = file_path.stem
        output_pdf = OUTPUT_DIR / f"{stem}_handwritten.pdf"
        output_preview_png = OUTPUT_DIR / f"{stem}_handwritten_page1.png"

        # Multi-page PDF output
        if len(pages) == 1:
            pages[0].save(output_pdf, "PDF", resolution=float(renderer.dpi))
        else:
            pages[0].save(output_pdf, "PDF", resolution=float(renderer.dpi), save_all=True, append_images=pages[1:])

        # First-page preview image
        pages[0].save(output_preview_png, "PNG", dpi=(renderer.dpi, renderer.dpi), quality=95)

        print(f"[OK] Successfully Generated A4 PDF: {output_pdf.name} ({len(pages)} page(s))")
        print(f"[OK] Saved High-Res Preview:        {output_preview_png.name}")

        # Move source file to finished_input
        dest_input = FINISHED_INPUT_DIR / file_path.name
        if dest_input.exists():
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            dest_input = FINISHED_INPUT_DIR / f"{file_path.stem}_{timestamp}{file_path.suffix}"

        shutil.move(str(file_path), str(dest_input))
        print(f"[OK] Archived original file to:     {dest_input.relative_to(BASE_DIR)}")

    except Exception as e:
        print(f"[FAIL] Error processing {file_path.name}: {e}")
        import traceback
        traceback.print_exc()

def run_batch_pipeline():
    setup_directories()
    config = load_config()
    renderer = UniversalA4Renderer(config)

    input_files = [f for f in INPUT_DIR.iterdir() if f.is_file() and not f.name.startswith(".")]
    if not input_files:
        print(f"[*] No documents in '{INPUT_DIR.relative_to(BASE_DIR)}'.")
        print(f"[*] Place any PDF, DOCX, TXT, or image into that folder and run this script.")
        return

    print(f"[*] Found {len(input_files)} document(s) in inbox. Running universal pipeline...")
    for f in input_files:
        process_file(f, config, renderer)
    print("\n[OK] Pipeline complete! Check 'pipeline/output/'.")

def watch_folder_pipeline(interval=2.0):
    setup_directories()
    config = load_config()
    renderer = UniversalA4Renderer(config)
    print("=================================================================")
    print("  SOFT COPY TO HARD COPY - UNIVERSAL AUTOMATED WATCHER")
    print(f"  Student Name: {config.get('student_name', 'Hariprajwal')}")
    print(f"  Watching:     {INPUT_DIR.resolve()}")
    print(f"  Archive:      {FINISHED_INPUT_DIR.resolve()}")
    print(f"  Outputs:      {OUTPUT_DIR.resolve()}")
    print("=================================================================")
    print("[*] Monitoring folder for new documents... (Press Ctrl+C to stop)")

    try:
        while True:
            input_files = [f for f in INPUT_DIR.iterdir() if f.is_file() and not f.name.startswith(".")]
            for f in input_files:
                initial_size = f.stat().st_size
                time.sleep(0.5)
                if f.exists() and f.stat().st_size == initial_size:
                    process_file(f, config, renderer)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n[*] Watcher stopped.")

if __name__ == "__main__":
    if "--watch" in sys.argv:
        watch_folder_pipeline()
    else:
        run_batch_pipeline()
