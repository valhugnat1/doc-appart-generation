import json
import os
import sys
from jinja2 import Template
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

def convert_to_pdf(html_content, output_pdf_path, output_html_path):
    """Saves HTML content and converts it to PDF."""
    try:
        # Save HTML
        with open(output_html_path, "w", encoding="utf-8") as html_file:
            html_file.write(html_content)
        print(f"HTML successfully created at {output_html_path}")

        # Convert HTML to PDF
        with open(output_pdf_path, "wb") as result_file:
            pisa_status = pisa.CreatePDF(
                html_content,
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
    
    # Default JSON path
    json_path = os.path.join(project_root, 'data', 'sessions', 'b2e7bde5-3ac0-4eda-9425-7421702c3d94.json')
    if not os.path.exists(json_path):
         json_path = os.path.join(project_root, 'data', 'template_data.json')

    # Check for command line argument
    if len(sys.argv) > 1:
        json_path = sys.argv[1]

    template_path = os.path.join(base_dir, 'bail_template.html')
    output_pdf_path = os.path.join(base_dir, 'bail_genere.pdf')
    output_html_path = os.path.join(base_dir, 'bail_genere.html')

    print(f"Loading data from {json_path}...")
    data = load_data(json_path)
    
    print(f"Rendering template from {template_path}...")
    html_content = render_template(template_path, data)
    
    print("Saving HTML and converting to PDF...")
    convert_to_pdf(html_content, output_pdf_path, output_html_path)

if __name__ == "__main__":
    main()
