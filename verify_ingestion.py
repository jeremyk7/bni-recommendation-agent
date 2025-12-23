import os
import sys
import pathlib
from google.cloud import firestore

# Add root to sys.path
ROOT = str(pathlib.Path(__file__).resolve().parent)
if ROOT not in sys.path:
    sys.path.append(ROOT)

from inriver_client import InRiverClient
from app_config import get_config

def verify():
    config = get_config()
    inriver = InRiverClient(config["IN_RIVER_BASE_URL"], config["ECOM_INRIVER_API_KEY"])
    
    formula = config.get("INRIVER_FILTER_FORMULA", "C")
    min_year = config.get("INRIVER_FILTER_MIN_YEAR", 2025)
    
    print(f"--- InRiver Verification (Filter: {formula}, Year >= {min_year}) ---")
    
    # 1. Fetch ALL matching Entity IDs from InRiver
    url = f"{inriver.base_url}/api/v1.0.0/query"
    query_payload = {
        "systemCriteria": [{"type": "EntityTypeId", "value": "Item", "operator": "Equal"}],
        "dataCriteria": [
            {"fieldTypeId": "ItemBusinessFormula", "value": formula, "operator": "Equal"},
            {"fieldTypeId": "ItemSeasonYear", "value": min_year, "operator": "GreaterThanOrEqual"}
        ]
    }
    
    try:
        response = inriver.session.post(url, json=query_payload)
        response.raise_for_status()
        inriver_ids = set(response.json().get("entityIds", []))
        print(f"✓ Found {len(inriver_ids)} Items in InRiver matching criteria.")
    except Exception as e:
        print(f"Error querying InRiver: {e}")
        return

    # 2. Query Firestore for ingested unique item_ids
    print("\n--- Firestore Verification ---")
    db = firestore.Client(project=config["GOOGLE_CLOUD_PROJECT"], database=config.get("FIRESTORE_DATABASE", "product"))
    products_col = config.get("FIRESTORE_PRODUCTS_COLLECTION", "products")
    errors_col = config.get("FIRESTORE_ERRORS_COLLECTION", "processingErrors")
    
    # We use a set to collect unique item_ids from Firestore
    ingested_item_ids = set()
    docs = db.collection(products_col).select(["item_id"]).stream()
    for doc in docs:
        item_id = doc.get("item_id")
        if item_id:
            ingested_item_ids.add(int(item_id))
    
    print(f"✓ Found {len(ingested_item_ids)} unique Items in Firestore.")
    
    # 3. Check for Errors
    error_item_ids = set()
    error_docs = db.collection(errors_col).select(["item_id"]).stream()
    for doc in error_docs:
        item_id = doc.get("item_id")
        if item_id:
            error_item_ids.add(int(item_id))
    
    print(f"✓ Found {len(error_item_ids)} unique Items with recorded errors.")

    # 4. Comparison
    missing_ids = inriver_ids - ingested_item_ids
    true_missing = missing_ids - error_item_ids
    
    print("\n" + "="*40)
    print("INGESTION STATUS REPORT")
    print("="*40)
    print(f"Total Target Items (InRiver): {len(inriver_ids)}")
    print(f"Successfully Ingested:       {len(ingested_item_ids)}")
    print(f"Failed (Recorded Errors):    {len(error_item_ids)}")
    print(f"Not Processed Yet:           {len(true_missing)}")
    print("="*40)
    
    if true_missing:
        print(f"\nTip: Run 'python3 batch_processor_cli.py --limit {len(inriver_ids)}' to process the remaining items.")
    elif len(ingested_item_ids) >= len(inriver_ids):
        print("\nSUCCESS: All matching items are in Firestore!")
    else:
        print("\nSome items are missing or failed. Check the errors collection for details.")

if __name__ == "__main__":
    verify()
