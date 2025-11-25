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
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {json_path}")
        return None

def render_template(template_path, data):
    """Renders a Jinja2 template with the provided data."""
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        template = Template(template_content)
        return template.render(**data)
    except FileNotFoundError:
        print(f"Error: Template not found at {template_path}")
        raise
    except Exception as e:
        print(f"Error rendering template: {e}")
        raise

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
            return False
            
        print(f"PDF successfully created at {output_pdf_path}")
        return True

    except Exception as e:
        print(f"Error converting to PDF: {e}")
        return False

def generate_bail_for_session(session_id: str):
    """Generates bail HTML and PDF for a given session ID."""
    # Paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_dir)
    
    # Input JSON path
    json_path = os.path.join(project_root, 'data', 'sessions', f'{session_id}.json')
    
    # Output paths
    output_dir = os.path.join(project_root, 'data', 'generated_bails')
    os.makedirs(output_dir, exist_ok=True)
    
    output_html_path = os.path.join(output_dir, f'{session_id}.html')
    output_pdf_path = os.path.join(output_dir, f'{session_id}.pdf')
    
    template_path = os.path.join(project_root, 'data/template/bail_template.html')

    print(f"Loading data from {json_path}...")
    data = load_data(json_path)
    
    if not data:
        print(f"No data found for session {session_id}")
        return None

    # If data is a list (legacy format), we might need to extract the actual data
    # But assuming the agent saves the structured data for the bail in the session file
    # If the session file only contains messages, this won't work as expected.
    # However, per the user request, we are using the session file.
    # Let's assume the session file contains the data needed for the template.
    # If the session file is just chat history, we might need to extract the data from the last message or a specific field.
    # For now, we'll pass the whole data object.
    
    print(f"Rendering template from {template_path}...")
    try:
        html_content = render_template(template_path, data)
        
        print("Saving HTML and converting to PDF...")
        convert_to_pdf(html_content, output_pdf_path, output_html_path)
        
        return output_html_path
    except Exception as e:
        print(f"Failed to generate bail: {e}")
        return None

def main():
    # Paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_dir)
    
    # Default JSON path for testing
    json_path = os.path.join(project_root, 'data', 'sessions', 'b2e7bde5-3ac0-4eda-9425-7421702c3d94.json')
    if not os.path.exists(json_path):
         json_path = os.path.join(project_root, 'data', 'template', 'template_data.json')

    # Check for command line argument
    if len(sys.argv) > 1:
        json_path = sys.argv[1]

    template_path = os.path.join(base_dir, 'bail_template.html')
    output_pdf_path = os.path.join(base_dir, 'bail_genere.pdf')
    output_html_path = os.path.join(base_dir, 'bail_genere.html')

    print(f"Loading data from {json_path}...")
    data = load_data(json_path)
    
    if data:
        print(f"Rendering template from {template_path}...")
        html_content = render_template(template_path, data)
        
        print("Saving HTML and converting to PDF...")
        convert_to_pdf(html_content, output_pdf_path, output_html_path)

if __name__ == "__main__":
    main()
