import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.resume_extractor import ResumeExtractor


if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

raw_text = ResumeExtractor.extract_text("data/resumes/saloni resume.pdf")
print(f"Extracted {len(raw_text)} characters.")
print(raw_text[:500])

