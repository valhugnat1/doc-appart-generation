import os

# Get the current directory (fastapi_app)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Parent directory (backend root)
PARENT_DIR = os.path.dirname(CURRENT_DIR)

# Paths
AGENT_DIR = os.path.join(PARENT_DIR, "agent_recup_info")
BAIL_SCRIPT_DIR = os.path.join(PARENT_DIR, "bail_generation_script")
CONVERSATIONS_DIR = os.path.join(PARENT_DIR, "data", "conversations")
GENERATED_BAILS_DIR = os.path.join(PARENT_DIR, "data", "generated_bails")

# Ensure directories exist
os.makedirs(CONVERSATIONS_DIR, exist_ok=True)

# Add parent directories to sys.path to allow imports from sibling directories
import sys
if AGENT_DIR not in sys.path:
    sys.path.append(AGENT_DIR)
if BAIL_SCRIPT_DIR not in sys.path:
    sys.path.append(BAIL_SCRIPT_DIR)
