#!/usr/bin/env python3
"""
Simple test script to demonstrate the DhobiGhat API functionality.
Run this after starting the server to test the endpoints.
"""

import asyncio
import httpx
import json
from datetime import datetime, timedelta, timezone

BASE_URL = "http://localhost:8000"


def get_common_intervals():
    """Return common cleaning intervals in seconds"""
    return {
        "1_day": 86400,
        "3_days": 259200,
        "1_week": 604800,
        "2_weeks": 1209600,
        "1_month": 2592000
    }


async def test_api():
    """Test the API endpoints"""
    async with httpx.AsyncClient() as client:
        print("🧪 Testing DhobiGhat API...\n")

        # Test health check
        print("1. Testing health check...")
        response = await client.get(f"{BASE_URL}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}\n")

        # Test root endpoint
        print("2. Testing root endpoint...")
        response = await client.get(f"{BASE_URL}/")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}\n")

        # Test creating a clothing item
        print("3. Testing create clothing item...")
        intervals = get_common_intervals()
        clothing_item = {
            "name": "Blue T-Shirt",
            "clothingItemType": "shirt",
            "image": "https://example.com/blue-tshirt.jpg",
            "last_cleaned": datetime.now(timezone.utc).isoformat(),
            "cleaning_interval_seconds": intervals["1_week"]  # 7 days in seconds
        }
        
        response = await client.post(
            f"{BASE_URL}/clothing-items",
            json=clothing_item
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 201:
            created_item = response.json()
            print(f"   Created item ID: {created_item['_id']}")
            print(f"   Item name: {created_item['name']}")
            print(f"   Next cleaning: {created_item['next_cleaning_date']}")
            item_id = created_item['_id']
        else:
            print(f"   Error: {response.text}")
            return
        print()

        # Test getting all clothing items
        print("4. Testing get all clothing items...")
        response = await client.get(f"{BASE_URL}/clothing-items")
        print(f"   Status: {response.status_code}")
        items = response.json()
        print(f"   Found {len(items)} items")
        print()

        # Test getting specific item
        print("5. Testing get specific item...")
        response = await client.get(f"{BASE_URL}/clothing-items/{item_id}")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            item = response.json()
            print(f"   Item name: {item['name']}")
            print(f"   Next cleaning: {item['next_cleaning_date']}")
        else:
            print(f"   Error: {response.text}")
        print()

        # Test search functionality
        print("6. Testing search by name...")
        response = await client.get(f"{BASE_URL}/clothing-items/search/Blue")
        print(f"   Status: {response.status_code}")
        items = response.json()
        print(f"   Found {len(items)} items matching 'Blue'")
        print()

        # Test search by type
        print("6.5. Testing search by type...")
        response = await client.get(f"{BASE_URL}/clothing-items/type/shirt")
        print(f"   Status: {response.status_code}")
        items = response.json()
        print(f"   Found {len(items)} items of type 'shirt'")
        print()

        # Test items needing cleaning
        print("7. Testing items needing cleaning...")
        response = await client.get(f"{BASE_URL}/clothing-items/needing-cleaning")
        print(f"   Status: {response.status_code}")
        items = response.json()
        print(f"   Found {len(items)} items needing cleaning")
        print()

        # Test recently cleaned items
        print("8. Testing recently cleaned items...")
        response = await client.get(f"{BASE_URL}/clothing-items/recently-cleaned?days=7")
        print(f"   Status: {response.status_code}")
        items = response.json()
        print(f"   Found {len(items)} items cleaned in last 7 days")
        print()

        # Test creating multiple items
        print("9. Testing create multiple items...")
        test_items = [
            {
                "name": "Red Jeans",
                "clothingItemType": "pants",
                "image": "https://example.com/red-jeans.jpg",
                "last_cleaned": datetime.now(timezone.utc).isoformat(),
                "cleaning_interval_seconds": intervals["3_days"]
            },
            {
                "name": "White Socks",
                "clothingItemType": "socks",
                "image": "https://example.com/white-socks.jpg",
                "last_cleaned": datetime.now(timezone.utc).isoformat(),
                "cleaning_interval_seconds": intervals["1_day"]
            },
            {
                "name": "Winter Jacket",
                "clothingItemType": "jacket",
                "image": "https://example.com/winter-jacket.jpg",
                "last_cleaned": datetime.now(timezone.utc).isoformat(),
                "cleaning_interval_seconds": intervals["1_month"]
            }
        ]
        
        created_items = []
        for i, item in enumerate(test_items, 1):
            response = await client.post(f"{BASE_URL}/clothing-items", json=item)
            if response.status_code == 201:
                created_item = response.json()
                created_items.append(created_item['_id'])
                print(f"   Created item {i}: {created_item['name']} (ID: {created_item['_id']})")
            else:
                print(f"   Failed to create item {i}: {response.text}")
        print()

        # Test updating cleaning interval for specific item
        print("10. Testing update cleaning interval for specific item...")
        if created_items:
            item_id = created_items[0]
            new_interval = 86400  # 1 day
            response = await client.put(f"{BASE_URL}/clothing-items/{item_id}/cleaning-interval?cleaning_interval_seconds={new_interval}")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                updated_item = response.json()
                print(f"   Updated item: {updated_item['name']}")
                print(f"   New interval: {updated_item['cleaning_interval_seconds']} seconds")
            else:
                print(f"   Error: {response.text}")
        print()

        # Test updating cleaning interval for all items of a type
        print("11. Testing update cleaning interval for all shirts...")
        new_interval = 259200  # 3 days
        response = await client.put(f"{BASE_URL}/clothing-items/type/shirt/cleaning-interval?cleaning_interval_seconds={new_interval}")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Updated {result['modified_count']} items of type '{result['item_type']}'")
            print(f"   New interval: {result['new_interval_seconds']} seconds")
        else:
            print(f"   Error: {response.text}")
        print()

        print("✅ API testing completed!")
        print(f"📊 Summary: Created {len(created_items) + 1} clothing items")
        print(f"🔗 API Documentation: {BASE_URL}/docs")
        print(f"🔍 Alternative Docs: {BASE_URL}/redoc")


if __name__ == "__main__":
    asyncio.run(test_api()) 