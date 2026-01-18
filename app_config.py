import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_config():
    """
    Validates and returns configuration from environment variables.
    """
    config = {}
    
    # GCP Config
    config["GOOGLE_CLOUD_PROJECT"] = os.getenv("GOOGLE_CLOUD_PROJECT") or "bni-oostzaan"
    config["VERTEX_LOCATION"] = os.getenv("VERTEX_LOCATION", "europe-west1")
    
    return config
