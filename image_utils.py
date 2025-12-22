import requests
import hashlib
from typing import Optional

def download_image(url: str, timeout: int = 10) -> Optional[bytes]:
    """
    Downloads an image from a URL.
    Returns bytes if successful, None otherwise.
    """
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        print(f"Error downloading image {url}: {e}")
        return None

def calculate_image_hash(image_bytes: bytes) -> str:
    """
    Calculates SHA256 hash of image bytes.
    """
    return hashlib.sha256(image_bytes).hexdigest()
