import motor.motor_asyncio
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection string - you'll need to set this in your .env file
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "dhobighat")

# Create motor client for async operations
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
database = client[DATABASE_NAME]

# Get collections
clothing_collection = database.clothing_items
users_collection = database.users

# Create indexes for better performance
async def create_indexes():
    """Create database indexes for better query performance"""
    # Clothing items indexes
    await clothing_collection.create_index("name")
    await clothing_collection.create_index("last_cleaned")
    await clothing_collection.create_index("next_cleaning_date")
    
    # Users indexes
    await users_collection.create_index("email", unique=True)
    await users_collection.create_index("name")

def get_database():
    """Get the database instance"""
    return database

# Test database connection
async def test_connection():
    """Test the database connection"""
    try:
        await client.admin.command('ping')
        print("✅ Successfully connected to MongoDB!")
        return True
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        return False 