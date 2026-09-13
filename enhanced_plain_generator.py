"""
Enhanced Handwriting Engine:
1. Plain Sheet Mode (NO ruled lines, NO margin lines - perfect for plain A4 assignments
   or printing directly onto pre-ruled physical notebook paper!).
2. Multi-Font Handwriting Showcase (compares available handwriting styles side-by-side).
"""

import os
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def generate_plain_sheet_output(
    output_image="plain_sheet_handwritten_output.png",
    output_pdf="plain_sheet_handwritten_output.pdf",
    font_path="C:/Windows/Fonts/Inkfree.ttf",
    transparent_bg=False
):
    random.seed(101)
    width, height = 1600, 1200
    line_spacing = 46
    margin_top = 110
    margin_left = 170
    font_size = 28

    # Background: Plain warm white paper (or transparent if printing onto real notebook paper!)
    if transparent_bg:
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    else:
        # Clean plain A4 assignment sheet: pure crisp white with soft paper warmth (#fcfbf7)
        img = Image.new("RGBA", (width, height), (252, 251, 247, 255))

    font_main = ImageFont.truetype(font_path, font_size)
    font_header = ImageFont.truetype(font_path, int(font_size * 1.15))
    font_small = ImageFont.truetype(font_path, int(font_size * 0.85))

    # Realistic ballpoint royal blue ink
    base_ink_blue = (28, 68, 138, 245)

    def render_handwritten_text(text, start_x, baseline_y, font=font_main, ink_color=base_ink_blue, slant=0.0):
        cur_x = start_x
        for char in text:
            if char == " ":
                cur_x += random.uniform(font_size * 0.35, font_size * 0.48)
                continue

            jitter_y = random.uniform(-1.2, 1.4)
            jitter_x = random.uniform(-0.5, 0.5)
            char_rot = random.uniform(-2.5, 2.5) + slant

            alpha_var = random.randint(-18, 18)
            char_color = (
                max(10, min(255, ink_color[0] + alpha_var)),
                max(20, min(255, ink_color[1] + alpha_var)),
                max(60, min(255, ink_color[2] + alpha_var)),
                245
            )

            bbox = font.getbbox(char)
            cw = bbox[2] - bbox[0]
            ch = bbox[3] - bbox[1]

            pad = 12
            char_img = Image.new("RGBA", (cw + pad * 2, ch + pad * 2), (0, 0, 0, 0))
            char_draw = ImageDraw.Draw(char_img)
            char_draw.text((pad - bbox[0], pad - bbox[1]), char, font=font, fill=char_color)

            if abs(char_rot) > 0.1:
                char_img = char_img.rotate(char_rot, resample=Image.BICUBIC, expand=True)

            target_x = int(cur_x + jitter_x)
            target_y = int(baseline_y - ch + jitter_y - bbox[1])

            img.paste(char_img, (target_x, target_y), char_img)
            cur_x += cw + random.uniform(-0.5, 1.5)

    header_y = margin_top - line_spacing
    # Header
    render_handwritten_text("CMSP", 40, header_y + 36, font=font_main, ink_color=(35, 55, 95, 245))
    render_handwritten_text("Optimization problem Set - 1 .", 320, header_y + 36, font=font_header, ink_color=(25, 60, 130, 245))

    # Subheaders
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

    # Question & Content
    y2 = margin_top + line_spacing
    render_handwritten_text("Q 1 )", 75, y2 + 38, font=font_main)
    render_handwritten_text("investment available  =  Rs 20 lakhs .", margin_left + 45, y2 + 38, font=font_main)

    y3 = y2 + line_spacing
    render_handwritten_text("Returns : -", margin_left + 25, y3 + 38, font=font_main)

    y4 = y3 + line_spacing
    render_handwritten_text("Scheme  1  =  10 % .", margin_left + 45, y4 + 38, font=font_main)

    y5 = y4 + line_spacing
    render_handwritten_text("Scheme  2  =  12 % .", margin_left + 45, y5 + 38, font=font_main)

    y6 = y5 + line_spacing
    render_handwritten_text("Scheme  3  =  15 % .", margin_left + 45, y6 + 38, font=font_main)

    y7 = y6 + line_spacing * 2
    render_handwritten_text("Scheme  3  accepts  maximum  Rs 10 lakhs .", margin_left + 25, y7 + 38, font=font_main)

    y8 = y7 + line_spacing
    render_handwritten_text("Risk  per  lakh", margin_left + 25, y8 + 38, font=font_main)

    y9 = y8 + line_spacing
    render_handwritten_text("Scheme  1  =  0", margin_left + 35, y9 + 38, font=font_main)

    y10 = y9 + line_spacing
    render_handwritten_text("Scheme  2  =  10", margin_left + 35, y10 + 38, font=font_main)

    y11 = y10 + line_spacing
    render_handwritten_text("Scheme  3  =  20", margin_left + 35, y11 + 38, font=font_main)

    y12 = y11 + line_spacing * 2
    render_handwritten_text("maximum  Risk  =  500  units .", margin_left + 25, y12 + 38, font=font_main)

    # Convert to RGB for saving PNG & PDF
    rgb_img = Image.new("RGB", (width, height), (252, 251, 247))
    rgb_img.paste(img, (0, 0), img)

    rgb_img.save(output_image, "PNG", quality=95)
    rgb_img.save(output_pdf, "PDF", resolution=150.0)
    print(f"Generated Plain Sheet Image: {output_image}")
    print(f"Generated Plain Sheet PDF: {output_pdf}")

def generate_style_showcase(output_image="handwriting_styles_preview.png"):
    """
    Renders the same sentence in different handwriting styles to compare options.
    """
    styles = [
        ("Ink Free (Casual Student Ballpoint)", "C:/Windows/Fonts/Inkfree.ttf", 30),
        ("Segoe Print (Clean Rounded Classroom Notes)", "C:/Windows/Fonts/segoepr.ttf", 26),
        ("Segoe Script (Fluid Connected Cursive Notes)", "C:/Windows/Fonts/segoesc.ttf", 26),
        ("Lucida Handwriting (Slanted Italicized Penmanship)", "C:/Windows/Fonts/LHANDW.TTF", 24),
    ]

    width, height = 1400, 850
    canvas = Image.new("RGB", (width, height), (250, 249, 244))
    draw = ImageDraw.Draw(canvas)

    title_font = ImageFont.truetype("C:/Windows/Fonts/segoepr.ttf", 28)
    draw.text((40, 25), "Handwriting Style Comparison Showcase", font=title_font, fill=(20, 35, 70))
    draw.line([(40, 68), (width - 40, 68)], fill=(200, 205, 215), width=2)

    sample_sentence = "investment available = Rs 20 lakhs. Scheme 1 = 10 %, Scheme 2 = 12 %."

    y = 95
    for name, path, size in styles:
        if not os.path.exists(path):
            continue
        font = ImageFont.truetype(path, size)
        label_font = ImageFont.truetype("C:/Windows/Fonts/segoepr.ttf", 18)

        # Draw label
        draw.text((40, y), f"Style: {name}", font=label_font, fill=(100, 110, 130))
        # Draw sample text in blue ballpoint ink
        draw.text((40, y + 30), sample_sentence, font=font, fill=(24, 62, 132))
        draw.line([(40, y + 130), (width - 40, y + 130)], fill=(230, 232, 238), width=1)
        y += 175

    canvas.save(output_image, "PNG", quality=95)
    print(f"Generated Handwriting Style Showcase: {output_image}")

if __name__ == "__main__":
    generate_plain_sheet_output()
    generate_style_showcase()
