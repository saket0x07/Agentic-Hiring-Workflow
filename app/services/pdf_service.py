from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa
from app.core.logger import logger

class PDFService:
    def __init__(self):
        self.template_dir = Path("app/templates")
        self.output_dir = Path("output/job_descriptions")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.env = Environment(loader=FileSystemLoader(self.template_dir))

    async def generate_job_description_pdf(self, job_id: str, jd: dict) -> str:
        """Generate PDF document for approved Job Description using xhtml2pdf."""
        logger.info(f"Generating PDF for approved job_id={job_id} using xhtml2pdf...")
        
        template = self.env.get_template("job_description.html")
        html_content = template.render(
            job_id=job_id,
            generated_at=datetime.now().strftime("%d-%b-%Y %I:%M %p"),
            jd=jd,
        )
        
        pdf_filename = f"{job_id}.pdf"
        pdf_path = self.output_dir / pdf_filename

        with open(pdf_path, "wb") as pdf_file:
            pisa_status = pisa.CreatePDF(html_content, dest=pdf_file)
            
        if pisa_status.err:
            logger.error(f"xhtml2pdf error rendering PDF for job_id={job_id}")
            raise RuntimeError(f"Failed to generate PDF for job_id: {job_id}")

        logger.info(f"PDF successfully created at: {pdf_path}")
        return str(pdf_path.resolve())
