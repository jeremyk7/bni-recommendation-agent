from google.cloud import firestore
from app_config import get_config

db = firestore.Client(project="ecom-agents", database="product")
collection = db.collection("products")

docs = collection.stream()
found_any = False
for doc in docs:
    found_any = True
    data = doc.to_dict()
    if "embedding" in data:
        emb = data["embedding"]
        print(f"Doc ID: {doc.id}")
        print(f"  Type: {type(emb)}")
        print(f"  Length: {len(emb)}")
        if len(emb) != 1408:
            print(f"  ⚠️  WARNING: Dimension mismatch! Expected 1408, got {len(emb)}")
    else:
        print(f"Doc ID: {doc.id} - No embedding field found")

if not found_any:
    print("No documents found in collection 'products'")
