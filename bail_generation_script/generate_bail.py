import json
import os
import sys
from jinja2 import Template
import markdown
from xhtml2pdf import pisa

def load_data(json_path):
    """Loads data from a JSON file."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found at {json_path}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {json_path}")
        sys.exit(1)

def render_template(template_path, data):
    """Renders a Jinja2 template with the provided data."""
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        template = Template(template_content)
        return template.render(**data)
    except FileNotFoundError:
        print(f"Error: Template not found at {template_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error rendering template: {e}")
        sys.exit(1)

def convert_to_pdf(markdown_content, output_pdf_path, output_html_path):
    """Converts Markdown content to HTML and then to PDF."""
    try:
        # Convert Markdown to HTML
        html_content = markdown.markdown(markdown_content)
        
        # Add some basic styling
        styled_html = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: sans-serif; font-size: 12px; line-height: 1.5; }}
                h1 {{ font-size: 18px; text-align: center; margin-bottom: 20px; }}
                h2 {{ font-size: 14px; margin-top: 20px; border-bottom: 1px solid #ccc; padding-bottom: 5px; }}
                p {{ margin-bottom: 10px; }}
                ul {{ margin-bottom: 10px; }}
                .page-break {{ page-break-before: always; }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """

        # Save HTML
        with open(output_html_path, "w", encoding="utf-8") as html_file:
            html_file.write(styled_html)
        print(f"HTML successfully created at {output_html_path}")

        # Convert HTML to PDF
        with open(output_pdf_path, "wb") as result_file:
            pisa_status = pisa.CreatePDF(
                styled_html,
                dest=result_file
            )

        if pisa_status.err:
            print(f"Error converting to PDF: {pisa_status.err}")
            sys.exit(1)
            
        print(f"PDF successfully created at {output_pdf_path}")

    except Exception as e:
        print(f"Error converting to PDF: {e}")
        sys.exit(1)

def main():
    # Paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_dir)
    
    json_path = os.path.join(project_root, 'data', '/Users/hugophilipp/Documents/perso/bail_generator/data/sessions/b2e7bde5-3ac0-4eda-9425-7421702c3d94.json')
    template_path = os.path.join(base_dir, 'bail_template.md')
    output_pdf_path = os.path.join(base_dir, 'bail_genere.pdf')
    output_html_path = os.path.join(base_dir, 'bail_genere.html')

    print("Loading data...")
    data = load_data(json_path)
    
    print("Rendering template...")
    markdown_content = render_template(template_path, data)
    
    print("Converting to HTML and PDF...")
    convert_to_pdf(markdown_content, output_pdf_path, output_html_path)

if __name__ == "__main__":
    main()
