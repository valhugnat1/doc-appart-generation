# French Lease Agent

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Environment Configuration**:
    - Rename `.env.example` to `.env`:
      ```bash
      cp .env.example .env
      ```
    - Edit `.env` and add your `OPENAI_API_KEY`.

## Usage

Run the agent:
```bash
python main.py
```

The agent will start a conversation to help you fill out the lease information.
The session data will be saved in `data/sessions/<session_id>.json`.
