import os
import datetime
import shutil
from typing import List, Dict, Any
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa

class ReportExporter:
    def __init__(self, steps: List[Dict[str, Any]], output_dir: str = "output"):
        self.steps = steps
        self.output_dir = output_dir
        self.template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def generate_pdf(self):
        print("Generating PDF report...")
        
        # Prepare Jinja2 environment
        env = Environment(loader=FileSystemLoader(self.template_dir))
        template = env.get_template("report.html")
        
        # Render HTML
        # xhtml2pdf usually works best with absolute paths for images on local disk
        # or file:/// URIs. Let's ensure paths are absolute.
        # Although pynput capture stores relative paths typically (or absolute depending on impl),
        # let's make sure they are absolute.
        
        cleaned_steps = []
        for step in self.steps:
            new_step = step.copy()
            if os.path.exists(new_step['screenshot']):
                new_step['screenshot'] = os.path.abspath(new_step['screenshot'])
            cleaned_steps.append(new_step)

        html_content = template.render(
            steps=cleaned_steps,
            generation_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        # Output filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"report_{timestamp}.pdf"
        output_path = os.path.join(self.output_dir, output_filename)
        
        # Generate PDF
        with open(output_path, "w+b") as result_file:
            pisa_status = pisa.CreatePDF(
                html_content,
                dest=result_file,
                encoding='UTF-8'
            )

        if pisa_status.err:
            print(f"Error generating PDF: {pisa_status.err}")
        else:
            print(f"PDF successfully generated: {output_path}")

    def cleanup_temp(self, temp_dir: str = "temp_screenshots"):
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                print(f"Temporary folder '{temp_dir}' deleted.")
            except Exception as e:
                print(f"Error deleting temporary folder: {e}")
