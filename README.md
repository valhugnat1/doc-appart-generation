# Bail Generator Project

This project is an AI-powered tool for generating French rental lease documents (Bail de location). It consists of two main components: an AI agent to gather lease information and a PDF generator to create the final contract.

## Project Structure

- **`ai_bail_agent/`**: Contains the AI agent (LangGraph/LangChain) that interacts with the user to fill out the lease details in a JSON format.
- **`creation_bail/`**: Contains Python scripts to generate the PDF lease from the JSON data.
- **`data/`**: Stores the session data (JSON files) and templates.

## Prerequisites

- Python 3.8+
- OpenAI API Key (or compatible LLM provider)

## Installation

1.  **Clone the repository** (if not already done).
2.  **Install dependencies**:
    ```bash
    pip install -r ai_bail_agent/requirements.txt
    # Note: You might need to install reportlab manually if not in requirements
    pip install reportlab
    ```
3.  **Environment Setup**:
    - Create a `.env` file in `ai_bail_agent/` (copy from `.env.example` if available).
    - Add your API key:
      ```
      OPENAI_API_KEY=your_api_key_here
      ```

## Usage

### Step 1: Gather Information with the AI Agent

Run the agent to start an interactive session. The agent will ask you questions to fill in the necessary lease details.

```bash
cd ai_bail_agent
python main.py
```

- Follow the conversation prompts.
- The agent will save the session data to `../data/sessions/<session_id>.json`.
- Note the `<session_id>` displayed at the start of the session.

### Step 2: Generate the PDF Lease

Once the JSON data is complete, use the generator script to create the PDF.

```bash
cd ../creation_bail
python generate_bail_complet.py ../data/sessions/<session_id>.json
```

- Replace `<session_id>` with the actual ID from Step 1.
- The PDF will be generated in the current directory (e.g., `contrat_location_complet.pdf`).

## Customization

- **Templates**: The data structure is based on `data/template_data.json`.
- **PDF Styles**: You can modify the PDF layout and styles in `creation_bail/generate_bail_complet.py`.
