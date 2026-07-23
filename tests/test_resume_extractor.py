import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.resume_extractor import ResumeExtractor


def test_resume_extraction():
    resume_path = "data/resumes/Saket-Resume.pdf"
    raw_text = ResumeExtractor.extract_text(resume_path)
    assert len(raw_text) > 0
    print(f"Extracted {len(raw_text)} characters.")


if __name__ == "__main__":
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    test_resume_extraction()

