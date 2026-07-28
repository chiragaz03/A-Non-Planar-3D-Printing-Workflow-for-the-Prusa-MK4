import math
import re
from pathlib import Path

# -----------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------

IN_FILE  = Path("nx_newpart.txt")          # NX output file
OUT_FILE = Path("nx_newpart_final.gcode")  # Printer G-code output

EXTRUSION_FACTOR = 0.05   # mm of extrusion per mm of path (tune later)

NOZZLE_TEMP = 200         # °C
BED_TEMP    = 60          # °C

Z_OFFSET = 0.0            # mm (set >0 if you need to lift everything from bed)

# Prusa MK4 nominal bed center (252 x 210 mm)
X_CENTER = 126.0          # mm
Y_CENTER = 105.0          # mm

# -----------------------------------------------------------
# IMPLEMENTATION
# -----------------------------------------------------------

word_re = re.compile(r'([A-Z])([-+]?[0-9]*\.?[0-9]+)')


def scan_xy_bounds(lines):
    """Scan all lines once to find Xmin, Xmax, Ymin, Ymax in NX coordinates."""
    x_vals = []
    y_vals = []

    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("(") or line.startswith(";"):
            continue
        if line.startswith("N"):
            parts = line.split(maxsplit=1)
            if len(parts) < 2:
                continue
            line = parts[1].strip()
            if not line:
                continue

        words = dict(word_re.findall(line))
        if "X" in words:
            x_vals.append(float(words["X"]))
        if "Y" in words:
            y_vals.append(float(words["Y"]))

    if not x_vals or not y_vals:
        # Nothing found; no shift
        return 0.0, 0.0

    x_min, x_max = min(x_vals), max(x_vals)
    y_min, y_max = min(y_vals), max(y_vals)

    cx = 0.5 * (x_min + x_max)   # part center in NX coords
    cy = 0.5 * (y_min + y_max)

    dx = X_CENTER - cx           # shift to printer center
    dy = Y_CENTER - cy

    return dx, dy


def main():
    if not IN_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {IN_FILE.resolve()}")

    all_lines = IN_FILE.read_text().splitlines()

    # First pass: compute X/Y shift
    dx, dy = scan_xy_bounds(all_lines)
    print(f"Computed XY shift: dx={dx:.3f}, dy={dy:.3f}")

    E = 0.0
    x_prev = y_prev = z_prev = None

    with OUT_FILE.open("w") as fout:
        # --- HEADER ---
        fout.write("; Non-planar test from NX + custom post\n")
        fout.write("G21 ; mm\n")
        fout.write("G90 ; absolute XYZ\n")
        fout.write("M82 ; absolute extrusion\n")
        fout.write(f"M104 S{NOZZLE_TEMP}\n")
        fout.write(f"M140 S{BED_TEMP}\n")
        fout.write("G28 ; home all axes\n")
        fout.write("G92 E0 ; reset extrusion\n")
        fout.write(f"M109 S{NOZZLE_TEMP}\n")
        fout.write(f"M190 S{BED_TEMP}\n")

        for raw_line in all_lines:
            line = raw_line.strip()
            if not line or line.startswith("(") or line.startswith(";"):
                continue

            # Remove line numbers
            if line.startswith("N"):
                parts = line.split(maxsplit=1)
                if len(parts) < 2:
                    continue
                line = parts[1].strip()
                if not line:
                    continue

            # Skip milling-specific commands
            if line.startswith("T") or "G43" in line or "M06" in line:
                continue
            if "M03" in line or "M08" in line:
                continue
            if line.startswith("G91 G28"):
                continue

            # Skip % and duplicate G21/G90
            if line.startswith("%"):
                continue
            if line.startswith("G21") or line.startswith("G90"):
                continue

            words = dict(word_re.findall(line))

            # -------- G0 (travel) --------
            if line.startswith("G0") or line.startswith("G00"):
                x_nx = float(words.get("X", x_prev - dx if x_prev is not None else 0.0))
                y_nx = float(words.get("Y", y_prev - dy if y_prev is not None else 0.0))

                x = x_nx + dx
                y = y_nx + dy

                if "Z" in words:
                    z_raw = float(words["Z"])
                    z = z_raw + Z_OFFSET
                else:
                    z = z_prev if z_prev is not None else 0.0

                x_prev, y_prev, z_prev = x, y, z

                out = f"G0 X{x:.3f} Y{y:.3f} Z{z:.3f}"
                if "F" in words:
                    out += f" F{float(words['F']):.1f}"
                fout.write(out + "\n")
                continue

            # -------- G1 (feed with extrusion) --------
            is_explicit_g1 = line.startswith("G1") or line.startswith("G01")
            has_xyz = any(axis in words for axis in ("X", "Y", "Z"))
            has_other_g = any(
                w == "G" and v not in ("1", "01")
                for w, v in word_re.findall(line)
            )

            if is_explicit_g1 or (has_xyz and not has_other_g):
                x_nx = float(words.get("X", x_prev - dx if x_prev is not None else 0.0))
                y_nx = float(words.get("Y", y_prev - dy if y_prev is not None else 0.0))

                x = x_nx + dx
                y = y_nx + dy

                if "Z" in words:
                    z_raw = float(words["Z"])
                    z = z_raw + Z_OFFSET
                else:
                    z = z_prev if z_prev is not None else 0.0

                if x_prev is None:
                    distance = 0.0
                else:
                    dx_step = x - x_prev
                    dy_step = y - y_prev
                    dz_step = z - z_prev
                    distance = math.sqrt(dx_step * dx_step +
                                         dy_step * dy_step +
                                         dz_step * dz_step)

                x_prev, y_prev, z_prev = x, y, z
                E += EXTRUSION_FACTOR * distance

                out = f"G1 X{x:.3f} Y{y:.3f} Z{z:.3f} E{E:.5f}"
                if "F" in words:
                    out += f" F{float(words['F']):.1f}"
                fout.write(out + "\n")
                continue

            # Ignore NX footer M-codes; we'll write own
            if line.startswith("M104") or line.startswith("M10"):
                continue
            if line.startswith("M11"):
                continue
            if line.startswith("M84"):
                continue

            # Default: copy anything else
            fout.write(line + "\n")

        # --- FOOTER ---
        fout.write("; End of program\n")
        fout.write("M104 S0\n")
        fout.write("M140 S0\n")
        fout.write("G92 E0\n")
        fout.write("M84\n")

    print(f"Done. Wrote {OUT_FILE.resolve()}")


if __name__ == "__main__":
    main()
