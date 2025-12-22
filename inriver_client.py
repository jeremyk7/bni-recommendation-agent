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

    def get_products(self, start_index: int = 0, limit: int = 500) -> List[Dict]:
        """
        Fetches products from InRiver using the Query API.
        """
        url = f"{self.base_url}/api/v1.0.0/query"
        
        # Correct system criteria for Entity Type
        query_payload = {
            "systemCriteria": [
                {
                    "type": "EntityTypeId",
                    "value": "Product",
                    "operator": "Equal"
                }
            ]
        }
        
        try:
            # Step 1: Find all Product IDs
            response = self.session.post(url, json=query_payload)
            if not response.ok:
                print(f"Query Failed: {response.text}")
            response.raise_for_status()
            
            # Response usually contains count and entityIds
            data = response.json()
            all_entity_ids = data.get("entityIds", [])
            
            # Step 2: Slice
            batch_ids = all_entity_ids[start_index : start_index + limit]
            
            if not batch_ids:
                return []

            # Step 3: Fetch details for these IDs (Iterative)
            # Falling back to iterative fetch as bulk endpoint /entities/fetch is not reliable/standard across versions
            
            products = []
            import concurrent.futures
            
            def fetch_one(entity_id):
                try:
                    # 1. Fetch Basic Fields
                    f_url = f"{self.base_url}/api/v1.0.0/entities/{entity_id}/summary/fields"
                    r = self.session.get(f_url, timeout=10)
                    r.raise_for_status()
                    fields_list = r.json()
                    fields_dict = {f.get('fieldTypeId'): f.get('value') for f in fields_list}

                    # 2. Fetch Image URL via Product -> Item -> Resource traversal
                    image_url = None
                    try:
                        # A. Product -> Item (LinkType: ProductItem)
                        # We look for outbound links from Product to Item
                        links_url = f"{self.base_url}/api/v1.0.0/entities/{entity_id}/links"
                        l_r = self.session.get(links_url, params={'linkDirection': 'outbound'}, timeout=10)
                        
                        item_id = None
                        if l_r.ok:
                            links = l_r.json()
                            # Find first link to an Item (LinkTypeId: ProductItem)
                            for link in links:
                                if link.get('linkTypeId') == 'ProductItem':
                                    item_id = link.get('targetEntityId')
                                    break
                        
                        if item_id:
                            # B. Item -> Resource (LinkType: ItemResource)
                            # Now get links for the Item
                            i_links_url = f"{self.base_url}/api/v1.0.0/entities/{item_id}/links"
                            il_r = self.session.get(i_links_url, params={'linkDirection': 'outbound'}, timeout=10)
                            
                            resource_id = None
                            if il_r.ok:
                                item_links = il_r.json()
                                # Find first link to a Resource (LinkTypeId: ItemResource)
                                for link in item_links:
                                    if link.get('linkTypeId') == 'ItemResource':
                                        resource_id = link.get('targetEntityId')
                                        break
                            
                            if resource_id:
                                # C. Get Resource URL (from File/Resource fields)
                                # Often the resource details or just generic fields contain the URL/Path
                                # But let's check mediadetails of the Resource entity, or just fields
                                
                                # Try mediadetails on the Resource ID itself
                                rm_url = f"{self.base_url}/api/v1.0.0/entities/{resource_id}/mediadetails"
                                rm_r = self.session.get(rm_url, timeout=10)
                                if rm_r.ok:
                                    media = rm_r.json()
                                    if media:
                                        image_url = media[0].get('url')
                                
                                # If mediadetails fail, try fetching fields of the resource
                                if not image_url:
                                    res_f_url = f"{self.base_url}/api/v1.0.0/entities/{resource_id}/summary/fields"
                                    res_r = self.session.get(res_f_url, timeout=10)
                                    if res_r.ok:
                                         res_fields = res_r.json()
                                         # Look for 'ResourceFileId' or similar which might be a URL or path
                                         # But mediadetails is usually the way for actual URLs
                                         pass 

                    except Exception as traversal_err:
                        # Keep silent on traversal errors to avoid log spam, but maybe log debug
                        # print(f"Debug: Traversal failed for {entity_id}: {traversal_err}")
                        pass
                    
                    # If we found an URL, override or set it.
                    # We map it to 'MainImage' key for consistency with config if not present.
                    if image_url:
                        fields_dict['MainImage'] = image_url

                    return {
                        "entity_id": entity_id,
                        **fields_dict
                    }
                except Exception as ex:
                    print(f"Failed to fetch entity {entity_id}: {ex}")
                    return None

            # Use ThreadPoolExecutor for concurrent fetching
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                results = executor.map(fetch_one, batch_ids)
                
            for res in results:
                if res:
                    products.append(res)
                
            return products

        except requests.RequestException as e:
            print(f"Error fetching products from InRiver: {e}")
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
