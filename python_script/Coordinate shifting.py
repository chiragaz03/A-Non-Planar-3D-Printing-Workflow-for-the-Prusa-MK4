input_file = r"D:\Master programme study material\sem 3\IRP IMW\chirag g code\Final code mmm.txt"
output_file = r"D:\Master programme study material\sem 3\IRP IMW\chirag g code\Final code mmm.gcode"

with open(input_file, "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

with open(output_file, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Done. Saved as G-code: {output_file}")
