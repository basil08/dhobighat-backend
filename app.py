from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Optional
import uvicorn
from datetime import datetime, timedelta
import os
import base64
import aiohttp
import io

from models import ClothingItemCreate, ClothingItemResponse
from crud import clothing_crud
from database import test_connection, create_indexes

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    # Startup
    print("🚀 Starting DhobiGhat API...")
    
    # Test database connection
    connected = await test_connection()
    if not connected:
        print("⚠️  Warning: Database connection failed. Please check your MongoDB configuration.")
    
    # Create database indexes
    try:
        await create_indexes()
        print("✅ Database indexes created successfully!")
    except Exception as e:
        print(f"⚠️  Warning: Failed to create indexes: {e}")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down DhobiGhat API...")


# Create FastAPI app
app = FastAPI(
    title="DhobiGhat API",
    description="A FastAPI backend service for managing clothing items with cleaning schedules",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to DhobiGhat API",
        "version": "1.0.0",
        "description": "A FastAPI backend service for managing clothing items with cleaning schedules",
        "endpoints": {
            "POST /clothing-items": "Create a new clothing item",
            "GET /clothing-items": "Get all clothing items (indexed by type)",
            "GET /clothing-items/{item_id}": "Get a specific clothing item",
            "GET /clothing-items/search/{name}": "Search clothing items by name",
            "GET /clothing-items/type/{item_type}": "Get clothing items by type",
            "PUT /clothing-items/{item_id}/cleaning-interval": "Update cleaning interval for specific item",
            "PUT /clothing-items/type/{item_type}/cleaning-interval": "Update cleaning interval for all items of a type",
            "GET /clothing-items/needing-cleaning": "Get items that need cleaning",
            "GET /clothing-items/recently-cleaned": "Get recently cleaned items"
        }
    }


@app.post("/clothing-items", response_model=ClothingItemResponse, status_code=201)
async def create_clothing_item(
    name: str = Form(...),
    clothingItemType: str = Form(...),
    cleaning_interval_seconds: int = Form(...),
    image: UploadFile = File(...)
):
    """Create a new clothing item with image upload"""
    try:
        print(f"🔍 DEBUG: Starting clothing item creation")
        print(f"🔍 DEBUG: Received data - name: {name}, type: {clothingItemType}, interval: {cleaning_interval_seconds}")
        print(f"🔍 DEBUG: Image file - filename: {image.filename}, content_type: {image.content_type}, size: {image.size}")
        
        image_filename = image.filename
        
        # Upload image to ImgBB
        print(f"🔍 DEBUG: Reading image file content...")
        content = await image.read()
        print(f"🔍 DEBUG: Image content size: {len(content)} bytes")
        
        base64_image = base64.b64encode(content).decode('utf-8')
        
        print(f"🔍 DEBUG: Base64 image length: {len(base64_image)}")
        
        
        # Get API key from environment
        api_key = os.getenv('IMGBB_API_KEY')
        print(f"🔍 DEBUG: API key: {api_key}")
        print(f"🔍 DEBUG: API key present: {api_key is not None}")
        if not api_key:
            raise HTTPException(status_code=500, detail="ImgBB API key not configured")
        
        # Prepare the upload request
        upload_url = "https://api.imgbb.com/1/upload"
        
        print(f"🔍 DEBUG: Preparing upload to ImgBB...")
        
        # Upload to ImgBB
        async with aiohttp.ClientSession() as session:
            print(f"🔍 DEBUG: Making request to ImgBB...")
            
            # Prepare form data for ImgBB API
            form_data = aiohttp.FormData()
            form_data.add_field('key', api_key)
            form_data.add_field('image', content, filename=image_filename)
            
            async with session.post(upload_url, data=form_data) as response:
                print(f"🔍 DEBUG: ImgBB response status: {response.status}")
                
                if response.status != 200:
                    error_text = await response.text()
                    print(f"🔍 DEBUG: ImgBB error response: {error_text}")
                    raise HTTPException(status_code=500, detail="Failed to upload image to ImgBB")
                
                result = await response.json()
                print(f"🔍 DEBUG: ImgBB response: {result}")
                
                if not result.get('success', False):
                    print(f"🔍 DEBUG: ImgBB API error: {result.get('error', {}).get('message', 'Unknown error')}")
                    raise HTTPException(status_code=500, detail=f"ImgBB error: {result.get('error', {}).get('message', 'Unknown error')}")
                
                # Get the image URL from ImgBB response
                data = result.get('data', {})
                image_url = data.get('url')
                print(f"🔍 DEBUG: Retrieved image URL: {image_url}")
                
                if not image_url:
                    print(f"🔍 DEBUG: No image URL in response")
                    raise HTTPException(status_code=500, detail="Failed to get image URL from ImgBB")
        
        # Create clothing item with the uploaded image URL
        print(f"🔍 DEBUG: Creating ClothingItemCreate object...")
        clothing_item_data = ClothingItemCreate(
            name=name,
            clothingItemType=clothingItemType,
            image=image_url,
            last_cleaned=datetime.utcnow(),  # Set to current time for new items
            cleaning_interval_seconds=cleaning_interval_seconds
        )
        print(f"🔍 DEBUG: ClothingItemCreate object created successfully")
        
        print(f"🔍 DEBUG: Calling clothing_crud.create_clothing_item...")
        created_item = await clothing_crud.create_clothing_item(clothing_item_data)
        print(f"🔍 DEBUG: Clothing item created successfully: {created_item}")
        
        return created_item
        
    except Exception as e:
        print(f"🔍 DEBUG: Exception occurred: {str(e)}")
        print(f"🔍 DEBUG: Exception type: {type(e)}")
        import traceback
        print(f"🔍 DEBUG: Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to create clothing item: {str(e)}")


@app.get("/clothing-items", response_model=dict)
async def get_all_clothing_items(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return")
):
    """Get all clothing items indexed by clothing type"""
    try:
        items = await clothing_crud.get_all_clothing_items(skip=skip, limit=limit)
        
        # Group items by clothingItemType
        indexed_items = {}
        for item in items:
            item_type = item.clothingItemType
            if item_type not in indexed_items:
                indexed_items[item_type] = []
            indexed_items[item_type].append(item)
        
        return indexed_items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve clothing items: {str(e)}")


@app.get("/clothing-items/archived", response_model=dict)
async def get_archived_clothing_items(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return")
):
    """Get all archived clothing items indexed by clothing type"""
    try:
        items = await clothing_crud.get_archived_clothing_items(skip=skip, limit=limit)
        
        # Group items by clothingItemType
        indexed_items = {}
        for item in items:
            item_type = item.clothingItemType
            if item_type not in indexed_items:
                indexed_items[item_type] = []
            indexed_items[item_type].append(item)
        
        return indexed_items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve archived clothing items: {str(e)}")


@app.get("/clothing-items/{item_id}", response_model=ClothingItemResponse)
async def get_clothing_item(item_id: str):
    """Get a specific clothing item by ID"""
    try:
        item = await clothing_crud.get_clothing_item(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Clothing item not found")
        return item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve clothing item: {str(e)}")


@app.get("/clothing-items/search/{name}", response_model=List[ClothingItemResponse])
async def search_clothing_items_by_name(
    name: str,
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return")
):
    """Search clothing items by name (case-insensitive)"""
    try:
        items = await clothing_crud.get_clothing_items_by_name(name, skip=skip, limit=limit)
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search clothing items: {str(e)}")


@app.get("/clothing-items/type/{item_type}", response_model=List[ClothingItemResponse])
async def get_clothing_items_by_type(
    item_type: str,
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return")
):
    """Get clothing items by type (case-insensitive)"""
    try:
        items = await clothing_crud.get_clothing_items_by_type(item_type, skip=skip, limit=limit)
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get clothing items by type: {str(e)}")


@app.put("/clothing-items/{item_id}/cleaning-interval", response_model=ClothingItemResponse)
async def update_item_cleaning_interval(
    item_id: str,
    cleaning_interval_seconds: int = Query(..., ge=1, description="New cleaning interval in seconds")
):
    """Update cleaning interval for a specific clothing item"""
    try:
        updated_item = await clothing_crud.update_item_cleaning_interval(item_id, cleaning_interval_seconds)
        if not updated_item:
            raise HTTPException(status_code=404, detail="Clothing item not found")
        return updated_item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update cleaning interval: {str(e)}")


@app.put("/clothing-items/type/{item_type}/cleaning-interval")
async def update_type_cleaning_interval(
    item_type: str,
    cleaning_interval_seconds: int = Query(..., ge=1, description="New cleaning interval in seconds")
):
    """Update cleaning interval for all clothing items of a specific type"""
    try:
        result = await clothing_crud.update_type_cleaning_interval(item_type, cleaning_interval_seconds)
        return {
            "message": f"Updated cleaning interval for {result['modified_count']} items of type '{item_type}'",
            "modified_count": result['modified_count'],
            "item_type": item_type,
            "new_interval_seconds": cleaning_interval_seconds
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update cleaning interval for type: {str(e)}")


@app.get("/clothing-items/needing-cleaning", response_model=List[ClothingItemResponse])
async def get_items_needing_cleaning(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return")
):
    """Get clothing items that need cleaning (next_cleaning_date <= now)"""
    try:
        items = await clothing_crud.get_items_needing_cleaning(skip=skip, limit=limit)
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve items needing cleaning: {str(e)}")


@app.get("/clothing-items/recently-cleaned", response_model=List[ClothingItemResponse])
async def get_recently_cleaned_items(
    days: int = Query(7, ge=1, le=365, description="Number of days to look back"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return")
):
    """Get clothing items cleaned within the last N days"""
    try:
        items = await clothing_crud.get_items_cleaned_recently(days=days, skip=skip, limit=limit)
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve recently cleaned items: {str(e)}")


@app.put("/clothing-items/{item_id}/archive", response_model=ClothingItemResponse)
async def archive_clothing_item(item_id: str):
    """Archive a clothing item"""
    try:
        archived_item = await clothing_crud.archive_clothing_item(item_id)
        if not archived_item:
            raise HTTPException(status_code=404, detail="Clothing item not found")
        return archived_item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to archive clothing item: {str(e)}")


@app.put("/clothing-items/{item_id}/unarchive", response_model=ClothingItemResponse)
async def unarchive_clothing_item(item_id: str):
    """Unarchive a clothing item"""
    try:
        unarchived_item = await clothing_crud.unarchive_clothing_item(item_id)
        if not unarchived_item:
            raise HTTPException(status_code=404, detail="Clothing item not found")
        return unarchived_item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to unarchive clothing item: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "DhobiGhat API"
    }


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
