# A Non-Planar 3D Printing Workflow for the Prusa MK4

This repository contains the files, scripts, and documentation for a non-planar 3D printing workflow developed for the Prusa MK4 using Siemens NX, NX Post Builder, and Python-based post-processing.

## Project Overview

The goal of this project is to develop a practical workflow that converts Siemens NX non-planar additive toolpaths into printer-ready G-code for a desktop FDM printer. The workflow addresses key challenges such as:

- generating non-planar toolpaths
- converting NX motion output into G-code
- handling extrusion values
- filtering travel motions
- aligning part and support structures
- adapting industrial CAM output for the Prusa MK4

## Software and Hardware Used

### Software
- Siemens NX
- NX Additive Manufacturing
- NX Post Builder
- Python
- PrusaSlicer

### Hardware
- Prusa MK4 3D printer

## Repository Structure

```text
.
├── figures/
├── g-code_files/
├── part_files/
├── post_builder_files/
├── python_script/
└── research_paper/
