"""
Realistic Notebook Handwriting Generator (Printable Mode + Plotter Mode)
Produces an authentic notebook page matching real student handwriting notes.
"""

import os
import math
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def generate_notebook_page(
    output_image_path="realistic_notebook_output.png",
    output_pdf_path="realistic_notebook_output.pdf",
    width=1600,
    height=1200,
    line_spacing=46,
    margin_top=110,
    margin_left=170,
    font_size=28
):
    # Set seed for reproducible natural variation
    random.seed(101)

    # 1. Create Paper Canvas (Natural off-white notebook paper)
    # Background color: subtle warm notebook ivory #faf7ee
    img = Image.new("RGB", (width, height), (248, 246, 238))
    draw = ImageDraw.Draw(img)

    # 2. Draw Ruled Notebook Lines
    # Horizontal ruled lines (soft grey-blue #c5d3df)
    y = margin_top
    while y < height - 40:
        draw.line([(0, y), (width, y)], fill=(202, 214, 224), width=2)
        y += line_spacing

    # Vertical Margin Guide Line (soft crimson/red #f0a8a8)
    draw.line([(margin_left, 0), (margin_left, height)], fill=(240, 168, 168), width=2)
    # Secondary double margin line (common in Indian notebooks like Classmate)
    draw.line([(margin_left - 6, 0), (margin_left - 6, height)], fill=(245, 195, 195), width=1)

    # Top Header line
    header_y = margin_top - line_spacing
    draw.line([(0, header_y), (width, header_y)], fill=(240, 168, 168), width=2)

    # 3. Load Handwriting Font
    # Prefer Ink Free or Segoe Print from Windows Fonts
    font_path = "C:/Windows/Fonts/Inkfree.ttf"
    if not os.path.exists(font_path):
        font_path = "C:/Windows/Fonts/segoepr.ttf"

    font_main = ImageFont.truetype(font_path, font_size)
    font_header = ImageFont.truetype(font_path, int(font_size * 1.15))
    font_small = ImageFont.truetype(font_path, int(font_size * 0.85))

    # Ballpoint ink color palette (rich royal blue with micro-pressure variation)
    base_ink_blue = (28, 68, 138)  # #1c448a

    def render_handwritten_text(text, start_x, baseline_y, font=font_main, ink_color=base_ink_blue, slant=0.0):
        """
        Renders text character-by-character with:
        - Per-character baseline jitter (touches the line naturally)
        - Micro-rotations and slant
        - Spacing variation
        - Variable ballpoint ink pressure
        """
        cur_x = start_x
        for i, char in enumerate(text):
            if char == " ":
                cur_x += random.uniform(font_size * 0.35, font_size * 0.48)
                continue

            # Natural human variations
            jitter_y = random.uniform(-1.2, 1.4)
            jitter_x = random.uniform(-0.5, 0.5)
            char_rot = random.uniform(-2.5, 2.5) + slant

            # Pressure variation: slightly lighter or darker stroke
            alpha_var = random.randint(-18, 18)
            char_color = (
                max(10, min(255, ink_color[0] + alpha_var)),
                max(20, min(255, ink_color[1] + alpha_var)),
                max(60, min(255, ink_color[2] + alpha_var))
            )

            # Measure char bounding box
            bbox = font.getbbox(char)
            cw = bbox[2] - bbox[0]
            ch = bbox[3] - bbox[1]

            # Render character to isolated RGBA layer for rotation & warping
            pad = 12
            char_img = Image.new("RGBA", (cw + pad * 2, ch + pad * 2), (0, 0, 0, 0))
            char_draw = ImageDraw.Draw(char_img)
            char_draw.text((pad - bbox[0], pad - bbox[1]), char, font=font, fill=char_color)

            # Apply micro-rotation
            if abs(char_rot) > 0.1:
                char_img = char_img.rotate(char_rot, resample=Image.BICUBIC, expand=True)

            # Compute target placement so bottom rests on baseline_y
            target_x = int(cur_x + jitter_x)
            target_y = int(baseline_y - ch + jitter_y - bbox[1])

            # Paste character with alpha mask
            img.paste(char_img, (target_x, target_y), char_img)

            # Advance cursor
            cur_x += cw + random.uniform(-0.5, 1.5)

    # 4. Content layout replicating the user's uploaded sample!
    # Top Margin Header
    render_handwritten_text("CMSP", 40, header_y + 36, font=font_main, ink_color=(35, 55, 95))
    render_handwritten_text("Optimization problem Set - 1 .", 320, header_y + 36, font=font_header, ink_color=(25, 60, 130))

    # Line 1: Sub-headers
    y1 = margin_top
    render_handwritten_text("1", 540, y1 + 18, font=font_small)
    render_handwritten_text("st", 552, y1 + 12, font=font_small)
    render_handwritten_text("3 -> LPP formulation", 575, y1 + 18, font=font_small)
    render_handwritten_text("4", 940, y1 + 18, font=font_small)
    render_handwritten_text("th", 955, y1 + 12, font=font_small)
    render_handwritten_text("- 10", 975, y1 + 18, font=font_small)
    render_handwritten_text("th", 1020, y1 + 12, font=font_small)
    render_handwritten_text("-> graphical", 1045, y1 + 18, font=font_small)
    render_handwritten_text("method .", 1040, y1 + 42, font=font_small)

    # Line 2: Q1) Heading & Statement
    y2 = margin_top + line_spacing
    render_handwritten_text("Q 1 )", 75, y2 + 38, font=font_main)
    render_handwritten_text("investment available  =  Rs 20 lakhs .", margin_left + 45, y2 + 38, font=font_main)

    # Line 3: Returns :-
    y3 = y2 + line_spacing
    render_handwritten_text("Returns : -", margin_left + 25, y3 + 38, font=font_main)

    # Line 4: Scheme 1 = 10 %
    y4 = y3 + line_spacing
    render_handwritten_text("Scheme  1  =  10 % .", margin_left + 45, y4 + 38, font=font_main)

    # Line 5: Scheme 2 = 12 %
    y5 = y4 + line_spacing
    render_handwritten_text("Scheme  2  =  12 % .", margin_left + 45, y5 + 38, font=font_main)

    # Line 6: Scheme 3 = 15 %
    y6 = y5 + line_spacing
    render_handwritten_text("Scheme  3  =  15 % .", margin_left + 45, y6 + 38, font=font_main)

    # Line 7: Scheme 3 accepts maximum Rs 10 lakhs.
    y7 = y6 + line_spacing * 2
    render_handwritten_text("Scheme  3  accepts  maximum  Rs 10 lakhs .", margin_left + 25, y7 + 38, font=font_main)

    # Line 8: Risk per lakh
    y8 = y7 + line_spacing
    render_handwritten_text("Risk  per  lakh", margin_left + 25, y8 + 38, font=font_main)

    # Line 9: Scheme 1 = 0
    y9 = y8 + line_spacing
    render_handwritten_text("Scheme  1  =  0", margin_left + 35, y9 + 38, font=font_main)

    # Line 10: Scheme 2 = 10
    y10 = y9 + line_spacing
    render_handwritten_text("Scheme  2  =  10", margin_left + 35, y10 + 38, font=font_main)

    # Line 11: Scheme 3 = 20
    y11 = y10 + line_spacing
    render_handwritten_text("Scheme  3  =  20", margin_left + 35, y11 + 38, font=font_main)

    # Line 12: maximum Risk = 500 units.
    y12 = y11 + line_spacing * 2
    render_handwritten_text("maximum  Risk  =  500  units .", margin_left + 25, y12 + 38, font=font_main)

    # 5. Add Subtle Physical Paper & Ballpoint Indentation Texture
    # Subtle softening / blur to simulate ink absorption in paper cellulose
    paper_softened = img.filter(ImageFilter.SMOOTH_MORE)
    final_output = Image.blend(img, paper_softened, 0.35)

    # Save PNG and PDF
    final_output.save(output_image_path, "PNG", quality=95)
    final_output.save(output_pdf_path, "PDF", resolution=150.0)
    print(f"Generated realistic notebook image: {output_image_path}")
    print(f"Generated printable PDF: {output_pdf_path}")

if __name__ == "__main__":
    generate_notebook_page()
