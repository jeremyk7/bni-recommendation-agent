import sys
import os
import io
import json
import logging
from PIL import Image

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("visual_search_debug")

# Add root to path
sys.path.append(os.getcwd())

from image_utils import detect_clothing_items, crop_to_box

def analyze_blazer():
    image_path = "/Users/jeremykhothesting.com/.gemini/antigravity/brain/d118c52c-b3ef-4024-b1d8-6163e1e81364/uploaded_image_1767088375565.png"
    query = "blazer"
    
    if not os.path.exists(image_path):
        print(f"Error: Image not found at {image_path}")
        return

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    print(f"--- Analyzing for query: '{query}' ---")
    
    print("Step 1: Detecting items...")
    detected_items = detect_clothing_items(image_bytes)
    
    print(f"Detected {len(detected_items)} items:")
    for i, item in enumerate(detected_items):
        print(f"[{i}] Label: '{item['label']}', Box: {item['box_2d']}, Desc: {item['description']}")
        
    if not detected_items:
        print("✗ No items detected.")
        return

    # Mock the current agent.py logic
    synonyms = {
        "trui": ["sweater", "pullover", "knitwear", "trui", "vest"],
        "rok": ["skirt", "rok"],
        "broek": ["pants", "trousers", "jeans", "broek", "shorts"],
        "blouse": ["blouse", "shirt", "top"],
        "schoenen": ["shoes", "boots", "laarzen", "schoenen", "sneakers"]
    }
    
    matched_item = None
    query_lower = query.lower()
    
    for item in detected_items:
        label = item['label'].lower()
        description = item['description'].lower()
        
        if label in query_lower or query_lower in label:
            matched_item = item
            print(f"✓ Direct label match hit: {label}")
            break
        
        if query_lower in description:
            matched_item = item
            print(f"✓ Description match hit: {description}")
            break
            
        for Dutch, eng_list in synonyms.items():
            if Dutch in query_lower:
                if any(s in label for s in eng_list):
                    matched_item = item
                    print(f"✓ Synonym match hit: {label} via {Dutch}")
                    break
        if matched_item:
            break

    if matched_item:
        print(f"\nStep 2: Cropping to item: {matched_item['label']}...")
        cropped_bytes = crop_to_box(image_bytes, matched_item['box_2d'])
        
        output_path = "/Users/jeremykhothesting.com/.gemini/antigravity/brain/d118c52c-b3ef-4024-b1d8-6163e1e81364/blazer_cropped_debug.png"
        with open(output_path, "wb") as f:
            f.write(cropped_bytes)
        print(f"✓ Debug cropped image saved to {output_path}")
    else:
        print("\n✗ No match found for 'blazer'.")

if __name__ == "__main__":
    analyze_blazer()
