import requests
from typing import List, Dict, Optional
import time

class InRiverClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            "X-inRiver-APIKey": api_key,
            "Accept": "application/json"
        })

    def get_products(self, start_index: int = 0, limit: int = 500, data_criteria: Optional[List[Dict]] = None) -> List[Dict]:
        """
        Fetches Items from InRiver.
        If data_criteria is provided, it searches for Items.
        For each Item, it fetches Parent Product fields and ALL Resource images.
        """
        url = f"{self.base_url}/api/v1.0.0/query"
        
        # 1. Search for Items
        query_payload = {
            "systemCriteria": [{"type": "EntityTypeId", "value": "Item", "operator": "Equal"}],
            "dataCriteria": data_criteria or []
        }
        
        try:
            response = self.session.post(url, json=query_payload)
            if not response.ok:
                print(f"Item Query Failed: {response.text}")
                return []
            
            all_item_ids = response.json().get("entityIds", [])
            print(f"✓ Found {len(all_item_ids)} Items matching filters.")
            
            # Slice for the requested batch
            batch_ids = all_item_ids[start_index : start_index + limit]
            
            if not batch_ids:
                return []

            items_data = []
            
            def fetch_item_details(item_id):
                try:
                    # A. Fetch Item Fields
                    f_url = f"{self.base_url}/api/v1.0.0/entities/{item_id}/summary/fields"
                    r = self.session.get(f_url, timeout=10)
                    r.raise_for_status()
                    item_fields = {f.get('fieldTypeId'): f.get('value') for f in r.json()}
                    
                    # B. Fetch Parent Product Details
                    product_data = {}
                    links_url = f"{self.base_url}/api/v1.0.0/entities/{item_id}/links"
                    l_r = self.session.get(links_url, params={'linkDirection': 'inbound'}, timeout=10)
                    if l_r.ok:
                        links = l_r.json()
                        parent_id = next((l.get('sourceEntityId') for l in links if l.get('linkTypeId') == 'ProductItem'), None)
                        if parent_id:
                            pf_url = f"{self.base_url}/api/v1.0.0/entities/{parent_id}/summary/fields"
                            p_r = self.session.get(pf_url, timeout=10)
                            if p_r.ok:
                                product_data = {f.get('fieldTypeId'): f.get('value') for f in p_r.json()}
                                product_data['product_entity_id'] = parent_id

                    # C. Fetch ALL Resource Images
                    image_urls = []
                    # Get outbound links from Item to Resource
                    i_links_url = f"{self.base_url}/api/v1.0.0/entities/{item_id}/links"
                    il_r = self.session.get(i_links_url, params={'linkDirection': 'outbound'}, timeout=10)
                    if il_r.ok:
                        resource_ids = [l.get('targetEntityId') for l in il_r.json() if l.get('linkTypeId') == 'ItemResource']
                        for rid in resource_ids:
                            rm_url = f"{self.base_url}/api/v1.0.0/entities/{rid}/mediadetails"
                            rm_r = self.session.get(rm_url, timeout=10)
                            if rm_r.ok:
                                media = rm_r.json()
                                if media:
                                    # Take the first URL found for this resource (usually just one)
                                    image_urls.append(media[0].get('url'))
                    
                    # Deduplicate URLs
                    image_urls = list(dict.fromkeys([u for u in image_urls if u]))

                    return {
                        "entity_id": item_id,
                        "item_fields": item_fields,
                        "product_fields": product_data,
                        "image_urls": image_urls
                    }
                except Exception as ex:
                    print(f"Failed to fetch item {item_id}: {ex}")
                    return None

            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                results = executor.map(fetch_item_details, batch_ids)
                
            for res in results:
                if res:
                    items_data.append(res)
                
            return items_data

        except requests.RequestException as e:
            print(f"Error fetching items from InRiver: {e}")
            raise

    def get_total_count(self) -> int:
        """
        Returns total count of products.
        """
        url = f"{self.base_url}/api/v1.0.0/query"
        query_payload = {
            "systemCriteria": [
                {
                    "type": "EntityTypeId",
                    "value": "Product",
                    "operator": "Equal"
                }
            ]
        }
        response = self.session.post(url, json=query_payload)
        if not response.ok:
            print(f"Count Query Failed: {response.text}")
        response.raise_for_status()
        return response.json().get("count", 0)
