import os
from app_config import get_config
from inriver_client import InRiverClient
from vision_client import VisionEmbeddingGenerator
from firestore_client import FirestoreClient
from image_utils import calculate_image_hash, download_image
from google.cloud import firestore

def test_pipeline_one_product():
    print("🚀 Starting Pipeline Test (1 Product)...")
    
    # 1. Setup Clients
    print("🔹 Initializing clients...")
    config = get_config()
    inriver = InRiverClient(config["IN_RIVER_BASE_URL"], config["ECOM_INRIVER_API_KEY"])
    vision = VisionEmbeddingGenerator()
    db = FirestoreClient()
    
    # 2. Fetch Product from InRiver
    print("🔹 Fetching product from InRiver...")
    products = inriver.get_products(start_index=0, limit=20) # Get a few to ensure we find one with an image
    
    target_product = None
    target_image_url = None
    
    for p in products:
        img = p.get(config.get("INRIVER_IMAGE_FIELD", "MainImage")) or p.get("MainImage")
        if img:
            target_product = p
            target_image_url = img
            break
            
    if not target_product:
        print("❌ No product with image found in first 20 items.")
        return

    print(f"✅ Found product: {target_product.get('entity_id')} - {target_product.get('ProductNameCommercial')}")
    print(f"   Image URL: {target_image_url}")

    # 3. Image Processing
    print("🔹 Downloading and Hashing image...")
    image_bytes = download_image(target_image_url)
    if not image_bytes:
        print("❌ Failed to download image.")
        return
        
    img_hash = calculate_image_hash(image_bytes)
    print(f"✅ Image Hash: {img_hash} (Length: {len(image_bytes)} bytes)")
    
    # 4. Generate Embedding
    print("🔹 Generating Embedding via Vertex AI...")
    embedding = vision.get_embedding(target_image_url)
    
    if not embedding:
        print("❌ Failed to generate embedding.")
        return
        
    print(f"✅ Embedding generated. Dimension: {len(embedding)}")
    if len(embedding) != 1408:
        print(f"⚠️  WARNING: Embedding dimension is {len(embedding)}, expected 1408.")
    
    # 5. Store in Firestore
    print("🔹 Storing in Firestore...")
    
    # Prepare document
    product_doc = {
        "entity_id": target_product.get("entity_id"),
        "name": target_product.get("ProductNameCommercial"),
        "image_url": target_image_url,
        "image_hash": img_hash,
        "embedding": embedding,
        "last_updated": firestore.SERVER_TIMESTAMP
    }
    # Need to import firestore for SERVER_TIMESTAMP or just skip it for test?
    # Actually client has firestore import internally? No, we need it here if we use the sentinel.
    # Let's import datetime instead for simplicity in test
    from datetime import datetime
    product_doc["last_updated"] = datetime.now()

    try:
        db.upsert_product(product_doc)
        print("✅ Firestore write successful.")
    except Exception as e:
        print(f"❌ Firestore write failed: {e}")
        return

    # 6. Verify Read
    print("🔹 Verifying valid write...")
    stored_doc = db.get_product(target_product.get("entity_id"))
    if stored_doc and stored_doc.get("image_hash") == img_hash:
        print("✅ Verification successful! Data matches.")
    else:
        print("❌ Verification failed. Data mismatch or not found.")

if __name__ == "__main__":
    test_pipeline_one_product()
