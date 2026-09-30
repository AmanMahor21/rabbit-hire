# backend/view_payloads.py
from qdrant_client import QdrantClient
import json

# Connect to your local Qdrant storage
client = QdrantClient(path="./qdrant_data")

# Get all points from the collection
collection_name = "talent_profiles"  # or "resume_profiles"

try:
    # Scroll through all records
    records, next_offset = client.scroll(
        collection_name=collection_name,
        limit=10,  # Show first 10 records
        with_payload=True,
        with_vectors=False
    )

    print(f"=== QDRANT DATA PREVIEW ===")
    print(f"Collection: {collection_name}")
    print(f"Showing: {len(records)} records\n")

    for i, record in enumerate(records, 1):
        print(f"\n{'='*60}")
        print(f"RECORD #{i}")
        print(f"{'='*60}")
        print(f"ID: {record.id}")
        print(f"\nPAYLOAD DATA:")
        print(json.dumps(record.payload, indent=2))

except Exception as e:
    print(f"Error: {e}")
    print("Make sure you're running this from the 'backend' directory")
