import google.cloud.firestore as firestore
from google.cloud.firestore_v1.vector import Vector
from google.cloud.firestore_v1.base_vector_query import DistanceMeasure
from typing import List, Dict, Any
from vision_client import VisionEmbeddingGenerator
from firestore_client import FirestoreClient
from app_config import get_config

def search_similar_products(image_bytes: bytes, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Takes image bytes, generates an embedding, and finds the nearest matches in Firestore.
    """
    config = get_config()
    vision = VisionEmbeddingGenerator()
    db_client = FirestoreClient()
    
    from vertexai.vision_models import Image
    import logging
    logger = logging.getLogger("search_tools")
    
    logger.info(f"Generating embedding for {len(image_bytes)} bytes of type {type(image_bytes)}...")
    
    try:
        image = Image(image_bytes)
    except Exception as e:
        logger.error(f"Failed to create Image object: {e}")
        raise ValueError(f"Could not create Vertex AI Image from bytes: {e}")
    
    try:
        embeddings = vision.model.get_embeddings(
            image=image,
            dimension=1408
        )
    except Exception as e:
        logger.error(f"Vertex AI Embedding Error: {str(e)}")
        raise
    
    if not embeddings or not embeddings.image_embedding:
        logger.warning("No embeddings returned from Vertex AI")
        return []
    
    query_vector = embeddings.image_embedding
    logger.info(f"✓ Generated embedding vector with {len(query_vector)} dimensions")

    # 2. Perform Vector Search in Firestore
    collection_name = config.get("FIRESTORE_PRODUCTS_COLLECTION", "products")
    logger.info(f"Querying Firestore collection: {collection_name}")
    collection = db_client.db.collection(collection_name)
    
    threshold = 0.2 # Similarity > 80% (Distance < 0.2)
    
    try:
        vector_query = collection.find_nearest(
            vector_field="embedding",
            query_vector=Vector(query_vector),
            distance_measure=DistanceMeasure.COSINE,
            limit=limit,
            distance_result_field="vector_distance"
        )
    except Exception as e:
        logger.error(f"Firestore vector query error: {e}")
        raise
    
    results = []
    for doc in vector_query.stream():
        data = doc.to_dict()
        distance = data.get("vector_distance", 1.0)
        
        if distance > threshold:
            logger.info(f"Skipping result {doc.id} due to distance {distance:.3f} > {threshold}")
            continue
            
        if "embedding" in data:
            del data["embedding"]
        results.append(data)
    
    logger.info(f"✓ Found {len(results)} relevant results from Firestore")
    return results
