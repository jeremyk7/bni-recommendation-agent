import os
import sys
import pathlib

# Add root to sys.path
ROOT = str(pathlib.Path(__file__).resolve().parent)
if ROOT not in sys.path:
    sys.path.append(ROOT)

from tools.search_tools import search_similar_products
from image_utils import download_image
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

# Test with the Linen Top image URL
image_url = "https://asset.productmarketingcloud.com/api/assetstorage/2712_2a61df97-b261-435e-9019-96410dab94f0"
image_bytes = download_image(image_url)

if image_bytes:
    print("\n--- Testing Search with Threshold (0.2) ---")
    results = search_similar_products(image_bytes, limit=5)
    
    print(f"\nResults returned: {len(results)}")
    for idx, r in enumerate(results, 1):
        name = r.get("name", {}).get("nl-NL", "N/A")
        print(f"{idx}. {name} (ID: {r.get('entity_id')})")
    
    if len(results) == 1:
        print("\n✅ SUCCESS: Only 1 relevant result found (threshold worked).")
    else:
        print(f"\n❌ FAILED: Expected 1 result, got {len(results)}.")
else:
    print("Failed to download test image.")
