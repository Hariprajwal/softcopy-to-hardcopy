"""
Complete CMSP Optimization Assignment Generator
Student Name: Hariprajwal
Font: Segoe Script (Fluid Connected Cursive Notes)
Format: Standard ISO A4 (300 DPI, Plain Sheet)
"""

import math
import random
from PIL import Image, ImageDraw, ImageFont

def generate_cmsp_assignment(
    output_pdf="CMSP_Assignment_Hariprajwal_handwritten.pdf",
    output_png="CMSP_Assignment_Hariprajwal_page1.png",
    font_path="C:/Windows/Fonts/segoesc.ttf"
):
    random.seed(42)

    width = 2480
    height = 3508
    dpi = 300

    line_spacing = 92
    margin_top = 220
    margin_left = 220
    margin_right = 200
    font_size = 44

    font_title = ImageFont.truetype(font_path, int(font_size * 1.35))
    font_header = ImageFont.truetype(font_path, int(font_size * 1.15))
    font_main = ImageFont.truetype(font_path, font_size)
    font_small = ImageFont.truetype(font_path, int(font_size * 0.85))

    base_ink_blue = (22, 58, 128)

    def render_handwritten_line(canvas, text, start_x, baseline_y, font=font_main, ink_color=base_ink_blue, is_header=False):
        cur_x = start_x
        words = text.split(" ")

        # Continuous sinusoidal & slope baseline wander
        if not is_header:
            line_slope = random.uniform(-0.0025, 0.0025)
            wave_len1 = random.uniform(900, 1500)
            wave_amp1 = random.uniform(2.0, 4.0)
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

            word_jitter_y = random.uniform(-2.2, 2.2) if not is_header else 0.0
            word_rot = random.uniform(-0.6, 0.6) if not is_header else 0.0

            for char in word:
                dx = cur_x - start_x
                continuous_wander = (
                    dx * line_slope +
                    wave_amp1 * math.sin(2 * math.pi * cur_x / wave_len1 + wave_phase1) +
                    wave_amp2 * math.sin(2 * math.pi * cur_x / wave_len2 + wave_phase2)
                )

                char_jitter_y = word_jitter_y + (random.uniform(-1.0, 1.0) if not is_header else 0.0)
                char_jitter_x = random.uniform(-0.4, 0.4) if not is_header else 0.0
                char_rot = word_rot + (random.uniform(-1.2, 1.2) if not is_header else 0.0)

                alpha_var = random.randint(-16, 16) if not is_header else 0
                char_color = (
                    max(10, min(255, ink_color[0] + alpha_var)),
                    max(20, min(255, ink_color[1] + alpha_var)),
                    max(60, min(255, ink_color[2] + alpha_var)),
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
                cur_x += cw - 1.5 + (random.uniform(-0.4, 0.4) if not is_header else 0.0)

            cur_x += font_size * (random.uniform(0.36, 0.50) if not is_header else 0.42)

    # ---------------- PAGE 1 ----------------
    page1 = Image.new("RGBA", (width, height), (255, 255, 255, 255))

    # Top Header with Student Name & Subject (Right-Aligned dynamically)
    y = margin_top
    render_handwritten_line(page1, "Name  :   Hariprajwal", margin_left, y, font=font_title, ink_color=(20, 50, 120), is_header=True)
    subj_str = "Subject  :   CMSP"
    subj_w = font_title.getbbox(subj_str)[2] - font_title.getbbox(subj_str)[0]
    subj_x = max(margin_left + 700, width - margin_right - subj_w)
    render_handwritten_line(page1, subj_str, subj_x, y, font=font_title, ink_color=(20, 50, 120), is_header=True)

    y += int(line_spacing * 1.3)
    render_handwritten_line(page1, "Optimization   Problem   Set   -   1   .", margin_left + 150, y, font=font_title, ink_color=(18, 48, 115))

    y += int(line_spacing * 1.1)
    render_handwritten_line(page1, "1st 3  ->  LPP formulation", margin_left + 80, y, font=font_small)
    render_handwritten_line(page1, "4th - 10th  ->  Graphical method .", 1450, y, font=font_small)

    y += int(line_spacing * 1.4)
    render_handwritten_line(page1, "Q 1 )", margin_left - 180, y, font=font_header)
    render_handwritten_line(page1, "investment   available   =   Rs  20  lakhs  .", margin_left, y, font=font_main)

    y += int(line_spacing * 1.1)
    render_handwritten_line(page1, "Returns   :   -", margin_left, y, font=font_main)

    y += line_spacing
    render_handwritten_line(page1, "Scheme   1   =   10  %  .", margin_left + 80, y, font=font_main)

    y += line_spacing
    render_handwritten_line(page1, "Scheme   2   =   12  %  .", margin_left + 80, y, font=font_main)

    y += line_spacing
    render_handwritten_line(page1, "Scheme   3   =   15  %  .", margin_left + 80, y, font=font_main)

    y += int(line_spacing * 1.3)
    render_handwritten_line(page1, "Scheme   3   accepts   maximum   Rs  10  lakhs  .", margin_left, y, font=font_main)

    y += int(line_spacing * 1.2)
    render_handwritten_line(page1, "Risk   per   lakh", margin_left, y, font=font_main)

    y += line_spacing
    render_handwritten_line(page1, "Scheme   1   =   0", margin_left + 80, y, font=font_main)

    y += line_spacing
    render_handwritten_line(page1, "Scheme   2   =   10", margin_left + 80, y, font=font_main)

    y += line_spacing
    render_handwritten_line(page1, "Scheme   3   =   20", margin_left + 80, y, font=font_main)

    y += int(line_spacing * 1.3)
    render_handwritten_line(page1, "maximum   Risk   =   500   units  .", margin_left, y, font=font_main)

    y += int(line_spacing * 1.3)
    render_handwritten_line(page1, "investor   wants   investment   in   scheme  1   to   be", margin_left, y, font=font_main)
    y += line_spacing
    render_handwritten_line(page1, "greater   than   scheme  2  .", margin_left, y, font=font_main)

    y += int(line_spacing * 1.5)
    render_handwritten_line(page1, "Step  -  1", margin_left, y, font=font_header, ink_color=(18, 48, 115))

    y += line_spacing
    render_handwritten_line(page1, "let", margin_left, y, font=font_main)

    y += line_spacing
    render_handwritten_line(page1, "x 1   =   investment   in   Scheme 1   ( lakhs )", margin_left + 60, y, font=font_main)

    y += line_spacing
    render_handwritten_line(page1, "x 2   =   investment   in   Scheme 2   ( lakhs )", margin_left + 60, y, font=font_main)


    # ---------------- PAGE 2 ----------------
    page2 = Image.new("RGBA", (width, height), (255, 255, 255, 255))
    y = margin_top

    # Header Page 2 (Dynamically aligned)
    render_handwritten_line(page2, "Name  :   Hariprajwal", margin_left, y, font=font_title, ink_color=(20, 50, 120), is_header=True)
    p2_str = "(  Page  2  )"
    p2_w = font_header.getbbox(p2_str)[2] - font_header.getbbox(p2_str)[0]
    p2_x = max(margin_left + 700, width - margin_right - p2_w)
    render_handwritten_line(page2, p2_str, p2_x, y, font=font_header, ink_color=(20, 50, 120), is_header=True)

    y += int(line_spacing * 1.5)
    render_handwritten_line(page2, "x 3   =   investment   in   Scheme 3   ( lakhs )", margin_left + 60, y, font=font_main)

    y += int(line_spacing * 1.5)
    render_handwritten_line(page2, "Step  -  2   observe   the   function", margin_left, y, font=font_header, ink_color=(18, 48, 115))

    y += line_spacing
    render_handwritten_line(page2, "expected   Return   :  -", margin_left, y, font=font_main)

    y += int(line_spacing * 1.2)
    render_handwritten_line(page2, "Max  Z   =   0 . 10  x 1   +   0 . 12  x 2   +   0 . 15  x 3", margin_left + 60, y, font=font_header)

    y += int(line_spacing * 1.5)
    render_handwritten_line(page2, "Step  -  3   constraints", margin_left, y, font=font_header, ink_color=(18, 48, 115))

    y += line_spacing
    render_handwritten_line(page2, "total   investment   :", margin_left, y, font=font_main)

    y += line_spacing
    render_handwritten_line(page2, "x 1   +   x 2   +   x 3   <=   20", margin_left + 80, y, font=font_main)

    y += int(line_spacing * 1.2)
    render_handwritten_line(page2, "Scheme   3   limitation   :", margin_left, y, font=font_main)

    y += line_spacing
    render_handwritten_line(page2, "x 3   <=   10", margin_left + 80, y, font=font_main)

    y += int(line_spacing * 1.2)
    render_handwritten_line(page2, "Scheme   1   greater   than   Scheme  2   :", margin_left, y, font=font_main)

    y += line_spacing
    render_handwritten_line(page2, "x 1   >   x 2", margin_left + 80, y, font=font_main)

    y += int(line_spacing * 1.2)
    render_handwritten_line(page2, "Risk   :  -", margin_left, y, font=font_main)

    y += line_spacing
    render_handwritten_line(page2, "0  x 1   +   10  x 2   +   20  x 3   <=   500", margin_left + 80, y, font=font_main)

    y += line_spacing
    render_handwritten_line(page2, "or    10  x 2   +   20  x 3   <=   500", margin_left + 80, y, font=font_main)

    y += int(line_spacing * 1.2)
    render_handwritten_line(page2, "Non   negativity   :", margin_left, y, font=font_main)

    y += line_spacing
    render_handwritten_line(page2, "x 1  ,   x 2  ,   x 3   >=   0", margin_left + 80, y, font=font_main)

    y += int(line_spacing * 1.6)
    render_handwritten_line(page2, "Final  LPP  Formulation  :", margin_left, y, font=font_header, ink_color=(18, 48, 115))

    y += int(line_spacing * 1.1)
    render_handwritten_line(page2, "Maximize   Z   =   0 . 10  x 1   +   0 . 12  x 2   +   0 . 15  x 3", margin_left + 60, y, font=font_header)

    y += line_spacing
    render_handwritten_line(page2, "Subject  to  :", margin_left + 60, y, font=font_main)

    y += line_spacing
    render_handwritten_line(page2, "x 1   +   x 2   +   x 3   <=   20", margin_left + 140, y, font=font_main)

    y += line_spacing
    render_handwritten_line(page2, "x 3   <=   10", margin_left + 140, y, font=font_main)

    y += line_spacing
    render_handwritten_line(page2, "x 1   >   x 2", margin_left + 140, y, font=font_main)

    y += line_spacing
    render_handwritten_line(page2, "10  x 2   +   20  x 3   <=   500", margin_left + 140, y, font=font_main)

    y += line_spacing
    render_handwritten_line(page2, "x 1  ,   x 2  ,   x 3   >=   0", margin_left + 140, y, font=font_main)


    # Convert to RGB (pure white)
    rgb_page1 = Image.new("RGB", (width, height), (255, 255, 255))
    rgb_page1.paste(page1, (0, 0), page1)

    rgb_page2 = Image.new("RGB", (width, height), (255, 255, 255))
    rgb_page2.paste(page2, (0, 0), page2)

    # Save multi-page PDF
    rgb_page1.save(output_pdf, "PDF", resolution=float(dpi), save_all=True, append_images=[rgb_page2])
    # Save preview image of Page 1
    rgb_page1.save(output_png, "PNG", dpi=(dpi, dpi), quality=95)
    # Save preview image of Page 2
    rgb_page2.save("CMSP_Assignment_Hariprajwal_page2.png", "PNG", dpi=(dpi, dpi), quality=95)

    print(f"Generated 2-Page A4 Cursive PDF: {output_pdf}")
    print(f"Generated Previews: {output_png} & CMSP_Assignment_Hariprajwal_page2.png")

if __name__ == "__main__":
    generate_cmsp_assignment()
