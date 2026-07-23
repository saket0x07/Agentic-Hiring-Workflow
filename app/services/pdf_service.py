from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa
from app.core.logger import logger

def clean_hyphens(data):
    """
    Replace non-standard unicode hyphen/dash characters with standard ASCII hyphens (-).
    Fixes rendering issues in xhtml2pdf where unicode hyphens appear as black box rectangles (■).
    """
    dash_variants = [
        "\u2011",  # non-breaking hyphen
        "\u2013",  # en-dash
        "\u2014",  # em-dash
        "\u2010",  # hyphen
        "\u2012",  # figure dash
        "\u2015",  # horizontal bar
        "\u00ad",  # soft hyphen
        "\ufe63",  # small hyphen-minus
        "\uff0d",  # fullwidth hyphen-minus
        "\u25a0",  # solid square box
    ]
    if isinstance(data, str):
        cleaned = data
        for d in dash_variants:
            cleaned = cleaned.replace(d, "-")
        return cleaned
    elif isinstance(data, dict):
        return {k: clean_hyphens(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_hyphens(item) for item in data]
    return data

class PDFService:
    def __init__(self):
        self.template_dir = Path("app/templates")
        self.output_dir = Path("output/job_descriptions")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.env = Environment(loader=FileSystemLoader(self.template_dir))

    async def generate_job_description_pdf(self, job_id: str, jd: dict) -> str:
        """Generate PDF document for approved Job Description using xhtml2pdf."""
        logger.info(f"Generating PDF for approved job_id={job_id} using xhtml2pdf...")
        
        cleaned_jd = clean_hyphens(jd)

        template = self.env.get_template("job_description.html")
        html_content = template.render(
            job_id=job_id,
            generated_at=datetime.now().strftime("%d-%b-%Y %I:%M %p"),
            jd=cleaned_jd,
        )
        
        html_content = clean_hyphens(html_content)

        pdf_filename = f"{job_id}.pdf"
        pdf_path = self.output_dir / pdf_filename

        with open(pdf_path, "wb") as pdf_file:
            pisa_status = pisa.CreatePDF(html_content, dest=pdf_file)
            
        if pisa_status.err:
            logger.error(f"xhtml2pdf error rendering PDF for job_id={job_id}")
            raise RuntimeError(f"Failed to generate PDF for job_id: {job_id}")

        logger.info(f"PDF successfully created at: {pdf_path}")
        return str(pdf_path.resolve())
