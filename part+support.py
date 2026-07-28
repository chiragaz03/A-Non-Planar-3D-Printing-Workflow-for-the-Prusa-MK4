import re

input_file = "Part+Support_shifted.txt"
output_file = "Part+Support_shifted_prusa_like.gcode"

# Lines that are clearly not G-code and should be commented out or removed
bad_text_keywords = [
    "Information listing created by",
    "Current work part",
    "Date",
    "name",
]

def is_gcode_or_comment(line):
    s = line.lstrip()
    if not s:
        return True
    return s[0] in ["G", "M", ";", "%"]

with open(input_file, "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

out = []
found_m83 = False
found_m82 = False
inserted_m83 = False
inserted_g92 = False

for line in lines:
    # Remove BOM / hidden unicode chars
    line = line.replace("\ufeff", "")

    stripped = line.strip()

    # Comment out bad text
    if any(k in stripped for k in bad_text_keywords):
        out.append("; " + stripped + "\n")
        continue

    # Remove M82
    if stripped.startswith("M82"):
        found_m82 = True
        continue

    # Track M83
    if stripped.startswith("M83"):
        found_m83 = True

    # Keep the line if it looks like G-code or a comment
    if is_gcode_or_comment(line):
        out.append(line)
    else:
        out.append("; " + stripped + "\n")

# Insert M83 and G92 E0 near the top if missing
new_out = []
for line in out:
    new_out.append(line)

    if (not inserted_m83) and line.strip().startswith("G90"):
        new_out.append("M83 ; force relative extrusion\n")
        inserted_m83 = True

    if (not inserted_g92) and line.strip().startswith("M83"):
        new_out.append("G92 E0 ; reset extrusion\n")
        inserted_g92 = True

# If G90 was not found, insert M83 and G92 at top
if not inserted_m83:
    new_out.insert(0, "M83 ; force relative extrusion\n")
if not inserted_g92:
    # put G92 right after M83 if possible
    if new_out and new_out[0].startswith("M83"):
        new_out.insert(1, "G92 E0 ; reset extrusion\n")
    else:
        new_out.insert(0, "G92 E0 ; reset extrusion\n")

with open(output_file, "w", encoding="utf-8") as f:
    f.writelines(new_out)

print("Done.")
print("Input file :", input_file)
print("Output file:", output_file)
print("Removed M82:", found_m82)
print("Found M83  :", found_m83)