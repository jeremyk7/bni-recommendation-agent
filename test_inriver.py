import os
import sys
from app_config import get_config
from inriver_client import InRiverClient
import json

def test_connection():
    try:
        print("Loading configuration...")
        config = get_config()
        
        base_url = config["IN_RIVER_BASE_URL"]
        api_key = config["ECOM_INRIVER_API_KEY"]
        image_field = config["INRIVER_IMAGE_FIELD"]
        
        print(f"Initializing InRiverClient with URL: {base_url}")
        client = InRiverClient(base_url, api_key)
        
        print("\nFetching first 5 products...")
        products = client.get_products(start_index=0, limit=5)
        
        print(f"\nRetrieved {len(products)} products:")
             
        for p in products:
            p_id = p.get('entity_id')
            p_name = p.get('ProductNameCommercial', 'Unknown')
            image_url = p.get(image_field) or p.get('MainImage') # Fallback to MainImage if configured field name differs
            
            print(f"- ID: {p_id} | Name: {p_name}")
            if not image_url:
                print(f"  ⚠️  Image field '{image_field}' (or MainImage) not found.")
                if products.index(p) == 0:
                     print(f"  DEBUG Keys: {list(p.keys())[:10]}...")
            else:
                print(f"  📷 Image: {image_url}")
            
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        # Print full stack trace for debugging
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_connection()
