"""
Auto Pipeline & Folder Watcher for Soft Copy to Hard Copy
Automatically converts any document placed in `pipeline/input/` into an
authentic A4 handwritten cursive PDF, then moves the source file to
`pipeline/finished_input/` and stores the result in `pipeline/output/`.

Supports: .pdf, .docx, .txt, .png, .jpg, .jpeg
"""

import os
import sys
import time
import shutil
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Optional text extraction dependencies with graceful fallbacks
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
PIPELINE_DIR = BASE_DIR / "pipeline"
INPUT_DIR = PIPELINE_DIR / "input"
FINISHED_INPUT_DIR = PIPELINE_DIR / "finished_input"
OUTPUT_DIR = PIPELINE_DIR / "output"

def setup_directories():
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    FINISHED_INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def extract_text_from_file(file_path: Path) -> str:
    ext = file_path.suffix.lower()
    text = ""
    
    if ext == ".txt":
        try:
            text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = file_path.read_text(encoding="latin-1", errors="ignore")

    elif ext == ".pdf":
        if fitz:
            doc = fitz.open(str(file_path))
            pages_text = [page.get_text() for page in doc]
            text = "\n\n".join(pages_text).strip()
            # If PDF contains no selectable text (scanned PDF), attempt OCR if available
            if not text and pytesseract:
                print(f"[*] Scanned PDF detected for {file_path.name}. Running OCR...")
                ocr_pages = []
                for page in doc:
                    pix = page.get_pixmap(dpi=150)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    ocr_pages.append(pytesseract.image_to_string(img))
                text = "\n\n".join(ocr_pages).strip()
        else:
            raise RuntimeError("PyMuPDF (fitz) is not installed. Run: pip install PyMuPDF")

    elif ext == ".docx":
        if docx:
            doc = docx.Document(str(file_path))
            text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        else:
            raise RuntimeError("python-docx is not installed. Run: pip install python-docx")

    elif ext in [".png", ".jpg", ".jpeg"]:
        if pytesseract:
            img = Image.open(str(file_path))
            text = pytesseract.image_to_string(img)
        else:
            raise RuntimeError("pytesseract is not installed for image OCR.")

    else:
        raise ValueError(f"Unsupported file format: {ext}")

    return text.strip()

class A4CursiveRenderer:
    """
    Renders multiline text into standard 300 DPI A4 handwritten cursive pages
    using Segoe Script with natural baseline drift, spacing jitter, and ballpoint ink depth.
    """
    def __init__(self, font_path="C:/Windows/Fonts/segoesc.ttf", font_size=44):
        self.font_path = font_path if os.path.exists(font_path) else "C:/Windows/Fonts/Inkfree.ttf"
        self.font_size = font_size
        self.font_main = ImageFont.truetype(self.font_path, self.font_size)
        self.font_header = ImageFont.truetype(self.font_path, int(self.font_size * 1.25))
        self.font_small = ImageFont.truetype(self.font_path, int(self.font_size * 0.85))

        # 300 DPI Standard A4 dimensions
        self.width = 2480
        self.height = 3508
        self.dpi = 300

        # Margin and layout geometry
        self.margin_left = 300
        self.margin_right = 260
        self.margin_top = 280
        self.margin_bottom = 280
        self.line_spacing = 96
        self.max_width = self.width - self.margin_right

        # Ballpoint royal blue ink
        self.base_ink = (22, 58, 128)

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

    def render_document(self, raw_text: str) -> list:
        """
        Converts raw text into a list of PIL Images (each representing an A4 page).
        Supports automatic pagination, paragraph structure, and word wrapping.
        """
        random.seed(101)
        pages = []
        
        def new_page():
            # Crisp unruled ivory paper
            return Image.new("RGBA", (self.width, self.height), (252, 251, 248, 255))

        current_page = new_page()
        cur_y = self.margin_top

        # Split text into paragraphs
        paragraphs = raw_text.split("\n")

        for para in paragraphs:
            para = para.strip()
            if not para:
                # Blank line / paragraph spacing
                cur_y += int(self.line_spacing * 0.7)
                if cur_y > self.height - self.margin_bottom:
                    pages.append(current_page)
                    current_page = new_page()
                    cur_y = self.margin_top
                continue

            # Detect if paragraph is a title or header
            is_header = len(para) < 60 and (para.isupper() or para.startswith("#") or "Assignment" in para or "Problem" in para)
            font = self.font_header if is_header else self.font_main
            clean_para = para.lstrip("#").strip()

            # Word wrap into lines
            words = clean_para.split(" ")
            current_line = []
            
            for word in words:
                test_line = " ".join(current_line + [word])
                if self.margin_left + self._estimate_text_width(test_line, font) > self.max_width:
                    if current_line:
                        # Flush line to canvas
                        if cur_y > self.height - self.margin_bottom:
                            pages.append(current_page)
                            current_page = new_page()
                            cur_y = self.margin_top
                        
                        line_str = " ".join(current_line)
                        self._render_line_on_canvas(current_page, line_str, self.margin_left, cur_y, font)
                        cur_y += self.line_spacing
                        current_line = [word]
                    else:
                        current_line = [word]
                else:
                    current_line.append(word)

            if current_line:
                if cur_y > self.height - self.margin_bottom:
                    pages.append(current_page)
                    current_page = new_page()
                    cur_y = self.margin_top

                line_str = " ".join(current_line)
                self._render_line_on_canvas(current_page, line_str, self.margin_left, cur_y, font)
                cur_y += self.line_spacing

        pages.append(current_page)

        # Convert RGBA pages to RGB
        rgb_pages = []
        for p in pages:
            rgb = Image.new("RGB", (self.width, self.height), (252, 251, 248))
            rgb.paste(p, (0, 0), p)
            rgb_pages.append(rgb)

        return rgb_pages

def process_file(file_path: Path, renderer: A4CursiveRenderer):
    print(f"\n[+] Processing: {file_path.name}")
    try:
        text = extract_text_from_file(file_path)
        if not text:
            print(f"[!] Warning: No text could be extracted from {file_path.name}. Skipping.")
            return

        print(f"[*] Extracted {len(text.split())} words. Generating handwritten A4 cursive pages...")
        pages = renderer.render_document(text)

        stem = file_path.stem
        output_pdf = OUTPUT_DIR / f"{stem}_handwritten.pdf"
        output_preview_png = OUTPUT_DIR / f"{stem}_handwritten_page1.png"

        # Save multi-page PDF
        if len(pages) == 1:
            pages[0].save(output_pdf, "PDF", resolution=float(renderer.dpi))
        else:
            pages[0].save(output_pdf, "PDF", resolution=float(renderer.dpi), save_all=True, append_images=pages[1:])

        # Save first page PNG preview
        pages[0].save(output_preview_png, "PNG", dpi=(renderer.dpi, renderer.dpi), quality=95)

        print(f"[OK] Successfully generated PDF: {output_pdf.name} ({len(pages)} page(s))")
        print(f"[OK] Preview image saved: {output_preview_png.name}")

        # Move source file to finished_input directory
        dest_input = FINISHED_INPUT_DIR / file_path.name
        if dest_input.exists():
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            dest_input = FINISHED_INPUT_DIR / f"{file_path.stem}_{timestamp}{file_path.suffix}"
        
        shutil.move(str(file_path), str(dest_input))
        print(f"[OK] Moved original file to: {dest_input.relative_to(BASE_DIR)}")

    except Exception as e:
        print(f"[FAIL] Error processing {file_path.name}: {e}")

def run_batch_pipeline():
    setup_directories()
    renderer = A4CursiveRenderer()
    
    input_files = [f for f in INPUT_DIR.iterdir() if f.is_file() and not f.name.startswith(".")]
    if not input_files:
        print(f"[*] No files found in '{INPUT_DIR.relative_to(BASE_DIR)}'. Place PDFs/DOCXs/TXTs there.")
        return

    print(f"[*] Found {len(input_files)} file(s) in inbox. Processing batch...")
    for f in input_files:
        process_file(f, renderer)
    print("\n[OK] Batch processing complete! Check 'pipeline/output/'.")

def watch_folder_pipeline(interval=2.0):
    setup_directories()
    renderer = A4CursiveRenderer()
    print(f"===========================================================")
    print(f"  SOFT COPY TO HARD COPY - AUTOMATED FOLDER WATCHER")
    print(f"  Watching: {INPUT_DIR.resolve()}")
    print(f"  Finished: {FINISHED_INPUT_DIR.resolve()}")
    print(f"  Outputs:  {OUTPUT_DIR.resolve()}")
    print(f"===========================================================")
    print(f"[*] Waiting for new documents... (Press Ctrl+C to stop)")

    try:
        while True:
            input_files = [f for f in INPUT_DIR.iterdir() if f.is_file() and not f.name.startswith(".")]
            for f in input_files:
                # Allow a tiny delay in case the file is still being copied
                initial_size = f.stat().st_size
                time.sleep(0.5)
                if f.exists() and f.stat().st_size == initial_size:
                    process_file(f, renderer)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n[*] Watcher stopped.")

if __name__ == "__main__":
    if "--watch" in sys.argv:
        watch_folder_pipeline()
    else:
        run_batch_pipeline()
