from pathlib import Path

import fitz
from docx import Document


class ResumeExtractor:
    """
    Extract raw text from supported Formats.

    supported:
    - PDF
    - DOCX
    """

    SUPPORTED_EXTENSIONS = {".pdf", ".docx"}

    @classmethod
    def extract_text(cls, file_path: str | Path) -> str:
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Resume Not Found : {file_path}")

        extension = file_path.suffix.lower()

        if extension not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"unsupported file extension : {extension}."
                f"Expected : {', '.join(cls.SUPPORTED_EXTENSIONS)}"
            )

        if extension == ".pdf":
            return cls._extract_pdf(file_path)
        if extension == ".docx":
            return cls._extract_docx(file_path)

        return ""

    @staticmethod
    def _extract_pdf(file_path: Path) -> str:
        text = []
        with fitz.open(file_path) as pdf:
            for page in pdf:
                page_text = page.get_text("text", sort=True)
                if page_text:
                    text.append(page_text)
        return ResumeExtractor._clean_text("\n".join(text))

    @staticmethod
    def _extract_docx(file_path: Path) -> str:
        document = Document(file_path)
        text = [
            paragraph.text
            for paragraph in document.paragraphs
            if paragraph.text.strip()
        ]
        return ResumeExtractor._clean_text("\n".join(text))

    @staticmethod
    def _clean_text(text: str) -> str:
        """
        Basic text Normalization
        More Advance processing will be handled by the resume parsing agent
        """
        dash_variants = ["\u2011", "\u2013", "\u2014", "\u2010", "\u2012", "\u2015", "\u00ad", "\ufe63", "\uff0d", "\u25a0"]
        for d in dash_variants:
            text = text.replace(d, "-")

        lines = []
        for line in text.splitlines():
            cleaned = " ".join(line.split())
            if cleaned:
                lines.append(cleaned)
        return "\n".join(lines)
