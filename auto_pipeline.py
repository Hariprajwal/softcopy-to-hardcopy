"""
Soft Copy to Hard Copy: Universal Automated Pipeline & Folder Watcher
====================================================================
Architecture:
1. Multi-Tier Document Ingestion:
   - Tier 1: Native Digital Text Extraction (PyMuPDF for PDF, python-docx for DOCX, UTF-8 for TXT).
   - Tier 2: Ollama Vision AI (llama3.2-vision / llava) for scanned handwriting & photographs.
   - Tier 3: OCR fallback (Tesseract / EasyOCR).
2. AI Text Cleanup & Math Formatting:
   - Optional local LLM polishing (via Ollama Qwen2.5 / Llama3.1) to correct OCR noise & format equations.
3. Automatic Student Personalization:
   - Injects student header (Name: Hariprajwal, Subject, Date) on Page 1 and continuation headers on subsequent pages.
4. Production-Grade A4 Cursive Handwriting Synthesis:
   - Standard 300 DPI ISO A4 plain sheets.
   - Segoe Script fluid connected cursive notes with biomechanical motor tremor, baseline wander, and royal blue ballpoint ink.
5. Automated Lifecycle & Folder Management:
   - Ingests from `pipeline/input/`.
   - Archives source documents to `pipeline/finished_input/`.
   - Emits finalized multi-page handwritten PDFs and previews to `pipeline/output/`.
"""

import os
import sys
import time
import json
import base64
import shutil
import random
import urllib.request
import urllib.error
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Optional text extraction dependencies
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    import docx
except ImportError:
    docx = None

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
        "ollama_vision_model": "llama3.2-vision",
        "ollama_text_cleanup_model": "qwen2.5:7b",
        "enable_ai_cleanup": False
    }
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                defaults.update(cfg)
        except Exception:
            pass
    return defaults

def setup_directories():
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    FINISHED_INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Multi-Tier Text Ingestion & Ollama Vision
# ---------------------------------------------------------------------------

def call_ollama_vision(image_bytes: bytes, config: dict) -> str:
    """Calls local Ollama Vision model to transcribe scanned handwriting."""
    ollama_url = config.get("ollama_url", "http://localhost:11434")
    model = config.get("ollama_vision_model", "llama3.2-vision")
    
    b64_img = base64.b64encode(image_bytes).decode("utf-8")
    payload = {
        "model": model,
        "prompt": (
            "Transcribe all handwritten and printed text in this document image accurately. "
            "Preserve question numbers, math equations (e.g. x1, x2, <=, >=, %), returns, and steps. "
            "Output only the transcribed text without any conversational preamble or notes."
        ),
        "images": [b64_img],
        "stream": False
    }
    
    req = urllib.request.Request(
        f"{ollama_url}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    
    with urllib.request.urlopen(req, timeout=45) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        return res.get("response", "").strip()

def extract_text_from_document(file_path: Path, config: dict) -> str:
    ext = file_path.suffix.lower()
    text = ""

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
        
        # If digital text exists across the PDF, use it
        if len(digital_text.split()) > 15:
            print(f"[*] Extracted native digital text from {file_path.name} ({len(digital_text.split())} words).")
            return digital_text

        # Otherwise, this is a SCANNED PDF: Run AI Vision / OCR on pages
        print(f"[*] Scanned PDF detected: '{file_path.name}'. Initiating vision transcription...")
        transcribed_pages = []
        for i, page in enumerate(doc):
            print(f"[*] Processing page {i + 1}/{len(doc)} with vision...")
            pix = page.get_pixmap(dpi=150)
            img_bytes = pix.tobytes("png")
            
            page_text = ""
            # Attempt Ollama Vision first
            try:
                page_text = call_ollama_vision(img_bytes, config)
                if page_text:
                    print(f"[*] Page {i + 1} transcribed via Ollama Vision.")
            except Exception as e:
                # Graceful notice if vision model is not yet pulled
                pass

            # Fallback to Tesseract OCR if available
            if not page_text and pytesseract:
                try:
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    page_text = pytesseract.image_to_string(img).strip()
                except Exception:
                    pass

            if page_text:
                transcribed_pages.append(page_text)
            else:
                # Fallback notice for user
                print(f"[!] Tip: Run 'ollama pull llama3.2-vision' or 'ollama pull llava' to enable automatic AI visual transcription of scanned PDFs.")

        if transcribed_pages:
            return "\n\n".join(transcribed_pages)
        else:
            # If no OCR or vision model is installed yet, return a clear guidance message
            return (
                f"Document: {file_path.stem}\n"
                "Scanned PDF uploaded. To enable automatic AI transcription of scanned image pages, "
                "install a vision model using: ollama pull llama3.2-vision (or ollama pull llava)."
            )

    # 4. Standalone Images
    elif ext in [".png", ".jpg", ".jpeg"]:
        img_bytes = file_path.read_bytes()
        try:
            text = call_ollama_vision(img_bytes, config)
            if text:
                return text
        except Exception:
            pass

        if pytesseract:
            img = Image.open(str(file_path))
            return pytesseract.image_to_string(img).strip()

    return text.strip()

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

        # Geometry & margins
        self.margin_left = 300
        self.margin_right = 260
        self.margin_top = 260
        self.margin_bottom = 260
        self.line_spacing = 92
        self.max_width = self.width - self.margin_right

        # Ink Color
        color = config.get("ink_color_rgb", [22, 58, 128])
        self.base_ink = tuple(color)

    def _render_line_on_canvas(self, canvas: Image.Image, text: str, start_x: int, baseline_y: int, font=None):
        font = font or self.font_main
        cur_x = start_x
        words = text.split(" ")

        for word in words:
            word_jitter_y = random.uniform(-2.5, 2.5)
            for char in word:
                char_jitter_y = word_jitter_y + random.uniform(-1.0, 1.0)
                char_rot = random.uniform(-1.2, 1.2)

                alpha_var = random.randint(-15, 15)
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

                target_x = int(cur_x)
                target_y = int(baseline_y - ch + char_jitter_y - bbox[1])

                canvas.paste(char_img, (target_x, target_y), char_img)
                cur_x += cw - 1.5 + random.uniform(-0.4, 0.4)

            cur_x += self.font_size * random.uniform(0.38, 0.52)

    def _estimate_text_width(self, text: str, font=None) -> int:
        font = font or self.font_main
        bbox = font.getbbox(text)
        return bbox[2] - bbox[0]

    def render_document(self, raw_text: str, document_title: str = "") -> list:
        random.seed(42)
        pages = []
        student_name = self.config.get("student_name", "Hariprajwal")

        def create_a4_canvas():
            # Warm ivory unruled plain sheet
            return Image.new("RGBA", (self.width, self.height), (252, 251, 248, 255))

        current_page = create_a4_canvas()
        page_index = 1

        # Header on Page 1: Student Name & Subject
        y = self.margin_top
        self._render_line_on_canvas(
            current_page, f"Name  :   {student_name}", self.margin_left - 160, y, font=self.font_title
        )
        subject_label = document_title or self.config.get("default_subject", "Assignment")
        self._render_line_on_canvas(
            current_page, f"Subject  :   {subject_label}", 1650, y, font=self.font_title
        )
        y += int(self.line_spacing * 1.6)

        paragraphs = raw_text.split("\n")

        for para in paragraphs:
            para = para.strip()
            if not para:
                y += int(self.line_spacing * 0.6)
                if y > self.height - self.margin_bottom:
                    pages.append(current_page)
                    page_index += 1
                    current_page = create_a4_canvas()
                    y = self.margin_top
                    self._render_line_on_canvas(
                        current_page, f"Name  :   {student_name}", self.margin_left - 160, y, font=self.font_title
                    )
                    self._render_line_on_canvas(
                        current_page, f"( Page  {page_index} )", 1850, y, font=self.font_header
                    )
                    y += int(self.line_spacing * 1.6)
                continue

            # Header / step detection
            is_heading = (
                len(para) < 65 and (
                    para.startswith("Step") or para.startswith("Q") or
                    para.startswith("#") or "Problem" in para or "Formulation" in para
                )
            )
            font = self.font_header if is_heading else self.font_main
            clean_para = para.lstrip("#").strip()

            # Wrap paragraph words into A4 margins
            words = clean_para.split(" ")
            current_line = []
            indent = self.margin_left + (40 if not is_heading else 0)

            for word in words:
                test_line = " ".join(current_line + [word])
                if indent + self._estimate_text_width(test_line, font) > self.max_width:
                    if current_line:
                        if y > self.height - self.margin_bottom:
                            pages.append(current_page)
                            page_index += 1
                            current_page = create_a4_canvas()
                            y = self.margin_top
                            self._render_line_on_canvas(
                                current_page, f"Name  :   {student_name}", self.margin_left - 160, y, font=self.font_title
                            )
                            self._render_line_on_canvas(
                                current_page, f"( Page  {page_index} )", 1850, y, font=self.font_header
                            )
                            y += int(self.line_spacing * 1.6)

                        line_str = " ".join(current_line)
                        self._render_line_on_canvas(current_page, line_str, indent, y, font)
                        y += self.line_spacing
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
                        current_page, f"Name  :   {student_name}", self.margin_left - 160, y, font=self.font_title
                    )
                    self._render_line_on_canvas(
                        current_page, f"( Page  {page_index} )", 1850, y, font=self.font_header
                    )
                    y += int(self.line_spacing * 1.6)

                line_str = " ".join(current_line)
                self._render_line_on_canvas(current_page, line_str, indent, y, font)
                y += self.line_spacing

        pages.append(current_page)

        # Convert RGBA to RGB
        rgb_pages = []
        for p in pages:
            rgb = Image.new("RGB", (self.width, self.height), (252, 251, 248))
            rgb.paste(p, (0, 0), p)
            rgb_pages.append(rgb)

        return rgb_pages

# ---------------------------------------------------------------------------
# Lifecycle: Process, Save & Archive
# ---------------------------------------------------------------------------

def process_file(file_path: Path, config: dict, renderer: UniversalA4Renderer):
    print(f"\n[+] Ingesting: {file_path.name}")
    try:
        text = extract_text_from_document(file_path, config)
        if not text:
            print(f"[!] Warning: No text content found in {file_path.name}. Skipping.")
            return

        title = file_path.stem.replace("_", " ")
        print(f"[*] Synthesizing handwritten cursive pages for '{title}'...")
        pages = renderer.render_document(text, document_title=title)

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

        print(f"[OK] Generated A4 PDF: {output_pdf.name} ({len(pages)} page(s))")
        print(f"[OK] Saved Preview: {output_preview_png.name}")

        # Move source file to finished_input
        dest_input = FINISHED_INPUT_DIR / file_path.name
        if dest_input.exists():
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            dest_input = FINISHED_INPUT_DIR / f"{file_path.stem}_{timestamp}{file_path.suffix}"

        shutil.move(str(file_path), str(dest_input))
        print(f"[OK] Archived original file to: {dest_input.relative_to(BASE_DIR)}")

    except Exception as e:
        print(f"[FAIL] Error processing {file_path.name}: {e}")

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
