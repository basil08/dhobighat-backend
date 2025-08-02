from datetime import datetime, timedelta
from typing import List, Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from models import ClothingItemCreate, ClothingItemResponse
from database import clothing_collection


class ClothingItemCRUD:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def create_clothing_item(self, clothing_item: ClothingItemCreate) -> ClothingItemResponse:
        """Create a new clothing item"""
        try:
            print(f"🔍 DEBUG: CRUD - Starting create_clothing_item")
            print(f"🔍 DEBUG: CRUD - Input clothing_item: {clothing_item}")
            
            # Calculate next cleaning date using seconds
            next_cleaning_date = clothing_item.last_cleaned + timedelta(seconds=clothing_item.cleaning_interval_seconds)
            print(f"🔍 DEBUG: CRUD - Calculated next_cleaning_date: {next_cleaning_date}")
            
            # Prepare document for insertion
            clothing_doc = clothing_item.model_dump()
            clothing_doc["next_cleaning_date"] = next_cleaning_date
            print(f"🔍 DEBUG: CRUD - Prepared document for insertion: {clothing_doc}")
            
            # Insert into database
            print(f"🔍 DEBUG: CRUD - Inserting into database...")
            result = await self.collection.insert_one(clothing_doc)
            print(f"🔍 DEBUG: CRUD - Insert result: {result.inserted_id}")
            
            # Get the inserted document
            print(f"🔍 DEBUG: CRUD - Retrieving inserted document...")
            inserted_doc = await self.collection.find_one({"_id": result.inserted_id})
            print(f"🔍 DEBUG: CRUD - Retrieved document: {inserted_doc}")
            
            # Convert ObjectId to string for Pydantic
            if inserted_doc:
                inserted_doc["_id"] = str(inserted_doc["_id"])
                print(f"🔍 DEBUG: CRUD - Converted ObjectId to string")
            
            # Convert to response model
            print(f"🔍 DEBUG: CRUD - Creating ClothingItemResponse...")
            response = ClothingItemResponse(**inserted_doc)
            print(f"🔍 DEBUG: CRUD - Created response: {response}")
            
            return response
            
        except Exception as e:
            print(f"🔍 DEBUG: CRUD - Exception in create_clothing_item: {str(e)}")
            print(f"🔍 DEBUG: CRUD - Exception type: {type(e)}")
            import traceback
            print(f"🔍 DEBUG: CRUD - Full traceback: {traceback.format_exc()}")
            raise

    async def get_clothing_item(self, item_id: str) -> Optional[ClothingItemResponse]:
        """Get a single clothing item by ID"""
        try:
            object_id = ObjectId(item_id)
            doc = await self.collection.find_one({"_id": object_id})
            if doc:
                # Convert ObjectId to string for Pydantic
                doc["_id"] = str(doc["_id"])
                # Ensure all required fields are present
                doc = self._normalize_document(doc)
                return ClothingItemResponse(**doc)
            return None
        except Exception:
            return None

    async def get_all_clothing_items(self, skip: int = 0, limit: int = 100, include_archived: bool = False) -> List[ClothingItemResponse]:
        """Get all clothing items with pagination"""
        query = {}
        if not include_archived:
            query["is_archived"] = {"$ne": True}
        
        cursor = self.collection.find(query).skip(skip).limit(limit)
        clothing_items = []
        async for doc in cursor:
            # Convert ObjectId to string for Pydantic
            doc["_id"] = str(doc["_id"])
            # Ensure all required fields are present
            doc = self._normalize_document(doc)
            clothing_items.append(ClothingItemResponse(**doc))
        return clothing_items

    async def get_clothing_items_by_name(self, name: str, skip: int = 0, limit: int = 100, include_archived: bool = False) -> List[ClothingItemResponse]:
        """Get clothing items by name (case-insensitive search)"""
        query = {"name": {"$regex": name, "$options": "i"}}
        if not include_archived:
            query["is_archived"] = {"$ne": True}
        
        cursor = self.collection.find(query).skip(skip).limit(limit)
        clothing_items = []
        async for doc in cursor:
            # Convert ObjectId to string for Pydantic
            doc["_id"] = str(doc["_id"])
            # Ensure all required fields are present
            doc = self._normalize_document(doc)
            clothing_items.append(ClothingItemResponse(**doc))
        return clothing_items

    async def get_clothing_items_by_type(self, item_type: str, skip: int = 0, limit: int = 100, include_archived: bool = False) -> List[ClothingItemResponse]:
        """Get clothing items by type (case-insensitive search)"""
        query = {"clothingItemType": {"$regex": item_type, "$options": "i"}}
        if not include_archived:
            query["is_archived"] = {"$ne": True}
        
        cursor = self.collection.find(query).skip(skip).limit(limit)
        clothing_items = []
        async for doc in cursor:
            # Convert ObjectId to string for Pydantic
            doc["_id"] = str(doc["_id"])
            # Ensure all required fields are present
            doc = self._normalize_document(doc)
            clothing_items.append(ClothingItemResponse(**doc))
        return clothing_items

    async def get_items_needing_cleaning(self, skip: int = 0, limit: int = 100, include_archived: bool = False) -> List[ClothingItemResponse]:
        """Get clothing items that need cleaning (next_cleaning_date <= now)"""
        now = datetime.utcnow()
        query = {"next_cleaning_date": {"$lte": now}}
        if not include_archived:
            query["is_archived"] = {"$ne": True}
        
        cursor = self.collection.find(query).skip(skip).limit(limit)
        clothing_items = []
        async for doc in cursor:
            # Convert ObjectId to string for Pydantic
            doc["_id"] = str(doc["_id"])
            # Ensure all required fields are present
            doc = self._normalize_document(doc)
            clothing_items.append(ClothingItemResponse(**doc))
        return clothing_items

    async def get_items_cleaned_recently(self, days: int = 7, skip: int = 0, limit: int = 100, include_archived: bool = False) -> List[ClothingItemResponse]:
        """Get clothing items cleaned within the last N days"""
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = {"last_cleaned": {"$gte": cutoff_date}}
        if not include_archived:
            query["is_archived"] = {"$ne": True}
        
        cursor = self.collection.find(query).skip(skip).limit(limit)
        clothing_items = []
        async for doc in cursor:
            # Convert ObjectId to string for Pydantic
            doc["_id"] = str(doc["_id"])
            # Ensure all required fields are present
            doc = self._normalize_document(doc)
            clothing_items.append(ClothingItemResponse(**doc))
        return clothing_items

    async def update_item_cleaning_interval(self, item_id: str, new_interval_seconds: int) -> Optional[ClothingItemResponse]:
        """Update cleaning interval for a specific clothing item"""
        try:
            object_id = ObjectId(item_id)
            
            # Get the current item to calculate new next_cleaning_date
            current_item = await self.collection.find_one({"_id": object_id})
            if not current_item:
                return None
            
            # Calculate new next_cleaning_date based on last_cleaned and new interval
            last_cleaned = current_item["last_cleaned"]
            new_next_cleaning_date = last_cleaned + timedelta(seconds=new_interval_seconds)
            
            # Update the item
            result = await self.collection.update_one(
                {"_id": object_id},
                {
                    "$set": {
                        "cleaning_interval_seconds": new_interval_seconds,
                        "next_cleaning_date": new_next_cleaning_date
                    }
                }
            )
            
            if result.modified_count > 0:
                # Get the updated item
                updated_doc = await self.collection.find_one({"_id": object_id})
                updated_doc["_id"] = str(updated_doc["_id"])
                # Ensure all required fields are present
                updated_doc = self._normalize_document(updated_doc)
                return ClothingItemResponse(**updated_doc)
            
            return None
        except Exception:
            return None

    async def update_type_cleaning_interval(self, item_type: str, new_interval_seconds: int) -> dict:
        """Update cleaning interval for all clothing items of a specific type"""
        try:
            # Get all items of this type
            cursor = self.collection.find({"clothingItemType": {"$regex": item_type, "$options": "i"}})
            
            modified_count = 0
            async for doc in cursor:
                # Calculate new next_cleaning_date for each item
                last_cleaned = doc["last_cleaned"]
                new_next_cleaning_date = last_cleaned + timedelta(seconds=new_interval_seconds)
                
                # Update this item
                result = await self.collection.update_one(
                    {"_id": doc["_id"]},
                    {
                        "$set": {
                            "cleaning_interval_seconds": new_interval_seconds,
                            "next_cleaning_date": new_next_cleaning_date
                        }
                    }
                )
                
                if result.modified_count > 0:
                    modified_count += 1
            
            return {
                "modified_count": modified_count,
                "item_type": item_type,
                "new_interval_seconds": new_interval_seconds
            }
        except Exception as e:
            raise Exception(f"Failed to update cleaning interval for type {item_type}: {str(e)}")

    async def archive_clothing_item(self, item_id: str) -> Optional[ClothingItemResponse]:
        """Archive a clothing item"""
        try:
            object_id = ObjectId(item_id)
            result = await self.collection.update_one(
                {"_id": object_id},
                {"$set": {"is_archived": True}}
            )
            
            if result.modified_count > 0:
                # Get the updated item
                updated_doc = await self.collection.find_one({"_id": object_id})
                updated_doc["_id"] = str(updated_doc["_id"])
                # Ensure all required fields are present
                updated_doc = self._normalize_document(updated_doc)
                return ClothingItemResponse(**updated_doc)
            
            return None
        except Exception:
            return None

    async def unarchive_clothing_item(self, item_id: str) -> Optional[ClothingItemResponse]:
        """Unarchive a clothing item"""
        try:
            object_id = ObjectId(item_id)
            result = await self.collection.update_one(
                {"_id": object_id},
                {"$set": {"is_archived": False}}
            )
            
            if result.modified_count > 0:
                # Get the updated item
                updated_doc = await self.collection.find_one({"_id": object_id})
                updated_doc["_id"] = str(updated_doc["_id"])
                # Ensure all required fields are present
                updated_doc = self._normalize_document(updated_doc)
                return ClothingItemResponse(**updated_doc)
            
            return None
        except Exception:
            return None

    async def get_archived_clothing_items(self, skip: int = 0, limit: int = 100) -> List[ClothingItemResponse]:
        """Get only archived clothing items"""
        # Query for items that are explicitly archived (is_archived: true)
        query = {"is_archived": True}
        
        cursor = self.collection.find(query).skip(skip).limit(limit)
        clothing_items = []
        async for doc in cursor:
            # Convert ObjectId to string for Pydantic
            doc["_id"] = str(doc["_id"])
            # Ensure all required fields are present
            doc = self._normalize_document(doc)
            clothing_items.append(ClothingItemResponse(**doc))
        return clothing_items

    def _normalize_document(self, doc: dict) -> dict:
        """Normalize document to ensure all required fields are present with correct names"""
        # Handle potential field name variations
        normalized = doc.copy()
        
        # Ensure clothingItemType field exists (handle potential variations)
        if "clothingItemType" not in normalized:
            if "clothing_item_type" in normalized:
                normalized["clothingItemType"] = normalized["clothing_item_type"]
            elif "type" in normalized:
                normalized["clothingItemType"] = normalized["type"]
            else:
                # Default fallback
                normalized["clothingItemType"] = "unknown"
        
        # Ensure last_cleaned field exists
        if "last_cleaned" not in normalized:
            if "lastCleaned" in normalized:
                normalized["last_cleaned"] = normalized["lastCleaned"]
            else:
                # Default to current time if missing
                normalized["last_cleaned"] = datetime.utcnow()
        
        # Ensure cleaning_interval_seconds field exists
        if "cleaning_interval_seconds" not in normalized:
            if "cleaningIntervalSeconds" in normalized:
                normalized["cleaning_interval_seconds"] = normalized["cleaningIntervalSeconds"]
            else:
                # Default to 7 days
                normalized["cleaning_interval_seconds"] = 7 * 24 * 60 * 60
        
        # Ensure next_cleaning_date field exists
        if "next_cleaning_date" not in normalized:
            if "nextCleaningDate" in normalized:
                normalized["next_cleaning_date"] = normalized["nextCleaningDate"]
            else:
                # Calculate from last_cleaned and interval
                last_cleaned = normalized["last_cleaned"]
                interval = normalized["cleaning_interval_seconds"]
                normalized["next_cleaning_date"] = last_cleaned + timedelta(seconds=interval)
        
        # Ensure image field exists
        if "image" not in normalized:
            normalized["image"] = ""
        
        # Ensure is_archived field exists
        if "is_archived" not in normalized:
            normalized["is_archived"] = False
        
        return normalized


# Create CRUD instance
clothing_crud = ClothingItemCRUD(clothing_collection) 