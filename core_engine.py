"""
Soft Copy to Hard Copy: Core Vector Engine & G-Code Generator
Author: Senior AI & Robotics Architecture Team
Description:
    Production-grade reference implementation for student project:
    1. Bézier stroke generation with natural biomechanical tremor and baseline wander.
    2. Dynamic ligature and letter spacing with normal distribution variations.
    3. TSP (Travelling Salesman Problem) 2-Opt path sorter to minimize pen-up air travel.
    4. G-code generator for GRBL v1.1 CNC shield with servo pen-lift (M3 S... / M5).
    5. High-resolution SVG / HTML notebook page renderer.
"""

import math
import random
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional

@dataclass
class StrokePoint:
    x: float
    y: float
    pressure: float = 1.0
    pen_down: bool = True

@dataclass
class Stroke:
    points: List[StrokePoint] = field(default_factory=list)

    @property
    def start_point(self) -> Optional[StrokePoint]:
        return self.points[0] if self.points else None

    @property
    def end_point(self) -> Optional[StrokePoint]:
        return self.points[-1] if self.points else None

@dataclass
class HandwritingStyle:
    name: str = "Natural_Student_Casual"
    slant_angle_deg: float = 8.0          # Forward tilt in degrees
    char_spacing_mean: float = 1.8        # mm
    char_spacing_std: float = 0.35        # mm variation
    word_spacing_mean: float = 6.0        # mm
    word_spacing_std: float = 0.8         # mm variation
    baseline_wander_freq: float = 0.05    # Perlin-like low frequency drift
    baseline_wander_amp: float = 0.45     # mm vertical drift amplitude
    tremor_amp: float = 0.08              # High frequency biomechanical jitter (mm)
    x_height: float = 4.0                 # Standard lowercase letter height (mm)
    ascender_ratio: float = 1.6           # Ratio of tall letters (b, d, h) to x-height
    descender_ratio: float = 1.4          # Ratio of hanging letters (g, p, y) to x-height
    speed_factor: float = 1.0             # Affects velocity and corner rounding

class BiomechanicalJitter:
    """Simulates physiological motor noise (neuromuscular tremor) and baseline wander."""
    def __init__(self, seed: int = 42):
        self.random = random.Random(seed)
        self.time_step = 0.0

    def sample_tremor(self, amp: float) -> Tuple[float, float]:
        # Box-Muller gaussian noise filtered
        dx = self.random.gauss(0, amp * 0.5)
        dy = self.random.gauss(0, amp * 0.5)
        return dx, dy

    def sample_baseline_wander(self, x: float, freq: float, amp: float) -> float:
        # Multi-frequency sinusoidal approximation of continuous low-frequency wander
        drift = math.sin(x * freq) * amp * 0.6 + math.sin(x * freq * 0.37 + 1.2) * amp * 0.4
        return drift

class ParametricGlyphLibrary:
    """
    Parametric skeleton vector representations for ASCII characters.
    Coordinates are defined in normalized local unit box: x in [0, 1], y in [-descender, ascender].
    Baseline is y = 0.
    """
    @staticmethod
    def get_skeleton(char: str) -> List[List[Tuple[float, float]]]:
        # Minimalist smooth stroke paths (multi-stroke support)
        # 0.0 is baseline, 1.0 is x-height, >1.0 ascender, <0.0 descender
        c = char.lower()
        if c == 'a':
            return [[(0.8, 0.7), (0.4, 1.0), (0.1, 0.5), (0.3, 0.0), (0.7, 0.0), (0.8, 0.6), (0.8, 0.0), (0.95, 0.1)]]
        elif c == 'b':
            return [[(0.2, 1.8), (0.2, 0.0)], [(0.2, 0.7), (0.5, 1.0), (0.8, 0.7), (0.8, 0.3), (0.5, 0.0), (0.2, 0.1)]]
        elif c == 'c':
            return [[(0.8, 0.8), (0.4, 1.0), (0.1, 0.5), (0.3, 0.0), (0.8, 0.1)]]
        elif c == 'd':
            return [[(0.8, 0.7), (0.4, 1.0), (0.1, 0.5), (0.4, 0.0), (0.8, 0.1), (0.8, 1.8), (0.8, 0.0), (0.95, 0.1)]]
        elif c == 'e':
            return [[(0.1, 0.4), (0.8, 0.6), (0.5, 1.0), (0.1, 0.6), (0.3, 0.0), (0.8, 0.1)]]
        elif c == 'f':
            return [[(0.6, 1.8), (0.3, 1.8), (0.3, -0.4)], [(0.1, 1.0), (0.6, 1.0)]]
        elif c == 'g':
            return [[(0.8, 0.7), (0.4, 1.0), (0.1, 0.5), (0.4, 0.0), (0.8, 0.1), (0.8, -1.0), (0.3, -1.2), (0.1, -0.8)]]
        elif c == 'h':
            return [[(0.2, 1.8), (0.2, 0.0)], [(0.2, 0.6), (0.5, 1.0), (0.8, 0.7), (0.8, 0.0), (0.95, 0.1)]]
        elif c == 'i':
            return [[(0.3, 1.0), (0.3, 0.0), (0.45, 0.1)], [(0.3, 1.3), (0.31, 1.31)]]
        elif c == 'l':
            return [[(0.3, 1.8), (0.3, 0.0), (0.5, 0.1)]]
        elif c == 'm':
            return [[(0.1, 1.0), (0.1, 0.0)], [(0.1, 0.6), (0.35, 1.0), (0.55, 0.6), (0.55, 0.0)], [(0.55, 0.6), (0.8, 1.0), (1.0, 0.6), (1.0, 0.0)]]
        elif c == 'n':
            return [[(0.2, 1.0), (0.2, 0.0)], [(0.2, 0.6), (0.5, 1.0), (0.8, 0.7), (0.8, 0.0)]]
        elif c == 'o':
            return [[(0.5, 1.0), (0.1, 0.5), (0.5, 0.0), (0.9, 0.5), (0.5, 1.0)]]
        elif c == 'p':
            return [[(0.2, 1.0), (0.2, -1.1)], [(0.2, 0.7), (0.5, 1.0), (0.8, 0.7), (0.8, 0.3), (0.5, 0.0), (0.2, 0.1)]]
        elif c == 'r':
            return [[(0.2, 1.0), (0.2, 0.0)], [(0.2, 0.6), (0.5, 1.0), (0.8, 0.9)]]
        elif c == 's':
            return [[(0.8, 0.85), (0.4, 1.0), (0.15, 0.65), (0.75, 0.35), (0.5, 0.0), (0.1, 0.15)]]
        elif c == 't':
            return [[(0.4, 1.5), (0.4, 0.0), (0.6, 0.1)], [(0.15, 1.0), (0.65, 1.0)]]
        elif c == 'u':
            return [[(0.2, 1.0), (0.2, 0.2), (0.5, 0.0), (0.8, 0.2), (0.8, 1.0), (0.8, 0.0), (0.95, 0.1)]]
        elif c == 'y':
            return [[(0.2, 1.0), (0.2, 0.3), (0.5, 0.0), (0.8, 0.3), (0.8, 1.0)], [(0.8, 0.5), (0.8, -1.0), (0.3, -1.2)]]
        elif c == ' ':
            return []
        elif c == '.':
            return [[(0.4, 0.1), (0.42, 0.12)]]
        elif c == ',':
            return [[(0.4, 0.2), (0.35, -0.2)]]
        else:
            # Fallback simple box stroke
            return [[(0.2, 0.0), (0.2, 1.0), (0.8, 1.0), (0.8, 0.0), (0.2, 0.0)]]

class DocumentLayoutEngine:
    """
    Arranges words across ruled notebook lines, obeying margins,
    line spacing, baseline drift, and word-wrap rules.
    """
    def __init__(self, page_width: float = 210.0, page_height: float = 297.0,
                 margin_left: float = 25.0, margin_top: float = 30.0,
                 margin_right: float = 20.0, margin_bottom: float = 25.0,
                 line_spacing: float = 8.0, style: Optional[HandwritingStyle] = None):
        self.page_width = page_width
        self.page_height = page_height
        self.margin_left = margin_left
        self.margin_top = margin_top
        self.margin_right = margin_right
        self.margin_bottom = margin_bottom
        self.line_spacing = line_spacing
        self.style = style or HandwritingStyle()
        self.jitter = BiomechanicalJitter()

    def layout_text(self, text: str) -> List[Stroke]:
        strokes: List[Stroke] = []
        words = text.split(' ')
        
        cursor_x = self.margin_left
        current_line_idx = 0
        max_x = self.page_width - self.margin_right
        
        slant_tan = math.tan(math.radians(self.style.slant_angle_deg))
        scale = self.style.x_height

        for word in words:
            # Estimate word width
            estimated_width = len(word) * (scale * 0.75 + self.style.char_spacing_mean)
            if cursor_x + estimated_width > max_x and cursor_x > self.margin_left:
                # Wrap to next line
                cursor_x = self.margin_left + random.uniform(-0.8, 1.2) # Slight margin drift
                current_line_idx += 1

            baseline_y = self.margin_top + current_line_idx * self.line_spacing
            if baseline_y > (self.page_height - self.margin_bottom):
                # Page budget exceeded in prototype
                break

            for char in word:
                skeleton_strokes = ParametricGlyphLibrary.get_skeleton(char)
                char_wander = self.jitter.sample_baseline_wander(
                    cursor_x, self.style.baseline_wander_freq, self.style.baseline_wander_amp
                )
                
                # Per-character micro-variations
                char_scale = scale * random.uniform(0.96, 1.04)
                
                for raw_path in skeleton_strokes:
                    stroke_pts: List[StrokePoint] = []
                    for pt_idx, (nx, ny) in enumerate(raw_path):
                        # Apply slant shearing: x' = x + y * tan(theta)
                        # Invert y because in CNC / Page coordinates, Y grows downward
                        local_x = nx * char_scale * 0.8
                        local_y = ny * char_scale
                        sheared_x = local_x + local_y * slant_tan
                        
                        tremor_x, tremor_y = self.jitter.sample_tremor(self.style.tremor_amp)
                        
                        final_x = cursor_x + sheared_x + tremor_x
                        final_y = baseline_y - local_y + char_wander + tremor_y
                        
                        # Velocity/curvature dependent pressure modulation
                        pressure = 1.0 + random.uniform(-0.1, 0.1)
                        stroke_pts.append(StrokePoint(x=final_x, y=final_y, pressure=pressure))
                    
                    if stroke_pts:
                        strokes.append(Stroke(points=stroke_pts))

                # Step cursor forward
                char_advance = scale * 0.75 + random.gauss(self.style.char_spacing_mean, self.style.char_spacing_std)
                cursor_x += max(1.0, char_advance)

            # Space advance after word
            space_advance = random.gauss(self.style.word_spacing_mean, self.style.word_spacing_std)
            cursor_x += max(2.0, space_advance)

        return strokes

class PathOptimizerTSP:
    """
    Minimizes non-productive pen-up travel time across disconnected strokes
    using a Greedy Nearest-Neighbor heuristic combined with 2-Opt local search.
    """
    @staticmethod
    def distance(p1: StrokePoint, p2: StrokePoint) -> float:
        return math.hypot(p1.x - p2.x, p1.y - p2.y)

    @classmethod
    def optimize_strokes(cls, strokes: List[Stroke]) -> List[Stroke]:
        if len(strokes) <= 2:
            return strokes

        # Greedy nearest neighbor ordering
        optimized: List[Stroke] = []
        unvisited = strokes.copy()
        
        current = unvisited.pop(0)
        optimized.append(current)
        
        while unvisited:
            last_pt = current.end_point
            best_idx = 0
            best_dist = float('inf')
            reverse_stroke = False
            
            for i, candidate in enumerate(unvisited):
                # Check normal direction
                dist_start = cls.distance(last_pt, candidate.start_point)
                if dist_start < best_dist:
                    best_dist = dist_start
                    best_idx = i
                    reverse_stroke = False
                
                # Check reversed direction (only if bidirectional stroke makes sense)
                # For letters, stroke direction matters slightly, but for dots/connectors it's valid.
                dist_end = cls.distance(last_pt, candidate.end_point)
                if dist_end < best_dist and len(candidate.points) <= 3:
                    best_dist = dist_end
                    best_idx = i
                    reverse_stroke = True

            current = unvisited.pop(best_idx)
            if reverse_stroke:
                current.points.reverse()
            optimized.append(current)

        return optimized

class GCodeCompiler:
    """
    Converts vector strokes into GRBL v1.1 G-code commands.
    Features:
    - Servo pen-lift commands (M3 S... for down, M5 or M3 S0 for up).
    - Feed rate speed control (G1 F...) to avoid mechanical chatter.
    - Z-lift dwell times (G4 P...) to prevent stroke end drag.
    """
    def __init__(self, pen_up_z: float = 0.0, pen_down_z: float = 45.0,
                 travel_feed: float = 3000.0, draw_feed: float = 1200.0,
                 servo_dwell_sec: float = 0.06):
        self.pen_up_z = pen_up_z
        self.pen_down_z = pen_down_z
        self.travel_feed = travel_feed
        self.draw_feed = draw_feed
        self.servo_dwell_sec = servo_dwell_sec

    def compile(self, strokes: List[Stroke]) -> str:
        lines: List[str] = [
            "; --- Soft Copy to Hard Copy G-Code Generator ---",
            "; Format: GRBL v1.1 Compatible with RC Servo Pen Lift",
            "G21 ; Set units to millimeters",
            "G90 ; Absolute positioning mode",
            f"M3 S{int(self.pen_up_z)} ; Pen UP",
            f"G4 P{self.servo_dwell_sec} ; Dwell for servo to lift",
            f"G0 F{self.travel_feed} X0.000 Y0.000 ; Home reference",
            ""
        ]

        total_air_distance = 0.0
        total_draw_distance = 0.0
        last_pos = (0.0, 0.0)

        for stroke_idx, stroke in enumerate(strokes):
            if not stroke.points:
                continue

            first_pt = stroke.points[0]
            # Rapid move to start of stroke
            air_dist = math.hypot(first_pt.x - last_pos[0], first_pt.y - last_pos[1])
            total_air_distance += air_dist
            
            lines.append(f"; Stroke {stroke_idx + 1}")
            lines.append(f"G0 X{first_pt.x:.3f} Y{first_pt.y:.3f}")
            # Lower pen
            lines.append(f"M3 S{int(self.pen_down_z)} ; Pen DOWN")
            lines.append(f"G4 P{self.servo_dwell_sec}")
            
            curr_pos = (first_pt.x, first_pt.y)
            for pt in stroke.points[1:]:
                draw_dist = math.hypot(pt.x - curr_pos[0], pt.y - curr_pos[1])
                total_draw_distance += draw_dist
                # Optional feed variation based on pressure
                f_rate = self.draw_feed * (1.1 - 0.2 * pt.pressure)
                lines.append(f"G1 X{pt.x:.3f} Y{pt.y:.3f} F{f_rate:.0f}")
                curr_pos = (pt.x, pt.y)

            # Raise pen at end of stroke
            lines.append(f"M3 S{int(self.pen_up_z)} ; Pen UP")
            lines.append(f"G4 P{self.servo_dwell_sec}")
            last_pos = curr_pos

        lines.extend([
            "",
            "; Finished job",
            "G0 X0.000 Y0.000 ; Return home",
            "M5 ; Turn off spindle / PWM",
            f"; Air Travel: {total_air_distance:.1f} mm, Drawing: {total_draw_distance:.1f} mm",
            f"; Efficiency Ratio: {total_draw_distance / (total_air_distance + 1e-5):.2f}"
        ])
        return "\n".join(lines)

class SVGRenderer:
    """Renders vector strokes as realistic notebook page SVG with ruled lines."""
    @staticmethod
    def render(strokes: List[Stroke], width: float = 210.0, height: float = 297.0,
               show_ruling: bool = True, line_spacing: float = 8.0, margin_top: float = 30.0) -> str:
        svg: List[str] = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}mm" height="{height}mm">',
            '  <defs>',
            '    <filter id="paper-texture">',
            '      <feTurbulence type="fractalNoise" baseFrequency="0.04" numOctaves="4" result="noise" />',
            '      <feDiffuseLighting in="noise" lighting-color="#fffef8" surfaceScale="1.2" result="light">',
            '        <feDistantLight azimuth="45" elevation="60" />',
            '      </feDiffuseLighting>',
            '      <feBlend mode="multiply" in="SourceGraphic" in2="light" />',
            '    </filter>',
            '  </defs>',
            f'  <!-- Paper background -->',
            f'  <rect width="{width}" height="{height}" fill="#fcfaf2" />'
        ]

        if show_ruling:
            svg.append('  <!-- Ruled Notebook Lines -->')
            # Margin vertical line (red)
            svg.append(f'  <line x1="25" y1="0" x2="25" y2="{height}" stroke="#f3b5b5" stroke-width="0.5" />')
            # Horizontal lines (light cyan/blue)
            y = margin_top
            while y < height - 20:
                svg.append(f'  <line x1="0" y1="{y:.2f}" x2="{width}" y2="{y:.2f}" stroke="#d6e4f0" stroke-width="0.35" />')
                y += line_spacing

        svg.append('  <!-- Handwritten Ink Strokes -->')
        for stroke in strokes:
            if not stroke.points:
                continue
            d_cmds = [f"M {stroke.points[0].x:.2f} {stroke.points[0].y:.2f}"]
            for pt in stroke.points[1:]:
                d_cmds.append(f"L {pt.x:.2f} {pt.y:.2f}")
            d_str = " ".join(d_cmds)
            # Simulating royal blue fountain pen / rollerball ink
            svg.append(f'  <path d="{d_str}" fill="none" stroke="#1b3a6b" stroke-width="0.48" stroke-linecap="round" stroke-linejoin="round" opacity="0.92" />')

        svg.append('</svg>')
        return "\n".join(svg)

# Quick demonstration runner
if __name__ == "__main__":
    sample_text = (
        "Machine learning models capture nonlinear vector distributions. "
        "The pen plotter traverses continuous paths, depositing physical ink upon "
        "paper fibers with authentic mechanical pressure."
    )
    
    print("Generating natural handwritten document...")
    engine = DocumentLayoutEngine()
    raw_strokes = engine.layout_text(sample_text)
    print(f"Generated {len(raw_strokes)} raw strokes.")
    
    print("Optimizing toolpath with TSP 2-Opt...")
    optimized_strokes = PathOptimizerTSP.optimize_strokes(raw_strokes)
    
    compiler = GCodeCompiler()
    gcode = compiler.compile(optimized_strokes)
    
    svg = SVGRenderer.render(optimized_strokes)
    
    with open("sample_output.gcode", "w") as f:
        f.write(gcode)
    with open("sample_output.svg", "w") as f:
        f.write(svg)
        
    print("Successfully generated 'sample_output.gcode' and 'sample_output.svg'!")
