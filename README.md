# visual-web-test-repair-subset

A simplified subset reproduction inspired by the paper **Visual Web Test Repair**.

## Project Overview
This project implements a simplified subset reproduction of the core idea in the paper *Visual Web Test Repair*.

The goal is to demonstrate that:
- a baseline Selenium locator can work on an old version of a web page,
- the same locator can fail on a new version after DOM changes,
- visual information can be used to identify the target element again,
- and the repaired interaction can succeed.

## Reproduction Goal
This project reproduces a simplified **same-page non-selection** breakage scenario.

In our example:
- `v1.html` represents the old version of the page,
- `v2.html` represents the new version after UI and DOM changes.

The baseline locator works on version 1 but fails on version 2.  
Then visual template matching is used to locate the target button again and complete the interaction successfully.

## Files
- `v1.html` — old version of the page
- `v2.html` — new version of the page with DOM changes
- `subset_reproduction.py` — main reproduction script
- `requirements.txt` — required Python packages
- `output/` — generated screenshots showing the reproduction process and results

## Environment
Recommended environment:
- Python 3.10+  
- Google Chrome  
- Windows / macOS / Linux

## How to Run
Create a virtual environment and install dependencies:

```bash
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt