# DhobiGhat Backend API

A FastAPI backend service for managing clothing items with cleaning schedules. Built with FastAPI, MongoDB, and Motor for async operations.

## Features

- ✅ Create clothing items with cleaning schedules
- ✅ Read clothing items with various filters
- ✅ Search clothing items by name
- ✅ Get items that need cleaning
- ✅ Get recently cleaned items
- ✅ Automatic calculation of next cleaning dates
- ✅ MongoDB Cloud integration
- ✅ Async operations for better performance
- ✅ Comprehensive API documentation

## Clothing Item Model

Each clothing item has the following properties:

- **name**: String - Name of the clothing item
- **clothingItemType**: String - Type of clothing item (e.g., shirt, pants, socks, jacket)
- **image**: String - URL or base64 encoded image
- **last_cleaned**: DateTime - Timestamp when the item was last cleaned
- **cleaning_interval_seconds**: Integer - Time interval between cleanings in seconds
- **next_cleaning_date**: DateTime - Automatically calculated next cleaning date

## Setup

### 1. Install Dependencies

**Option A: Using Virtual Environment (Recommended)**
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Option B: Using the setup script**
```bash
chmod +x setup_venv.sh
./setup_venv.sh
```

**Option C: Using conda**
```bash
# Create and activate conda environment
conda env create -f environment.yml
conda activate dhobighat-env

# Or if you already have a conda environment:
conda env update -f environment.yml
```

**Option D: Manual installation**
```bash
pip install fastapi uvicorn motor==3.3.1 pymongo==4.6.0 pydantic python-multipart python-dotenv httpx
```

### Troubleshooting

**If you encounter motor/pymongo import errors:**
```bash
# Run the fix script
chmod +x fix_dependencies.sh
./fix_dependencies.sh

# Or manually fix:
pip uninstall -y motor pymongo
pip install motor==3.3.1 pymongo==4.6.0
```

### 2. Configure MongoDB

1. Create a MongoDB Cloud account and cluster
2. Get your connection string from MongoDB Cloud
3. Copy `env.example` to `.env`:
   ```bash
   cp env.example .env
   ```
4. Update the `.env` file with your MongoDB connection string:
   ```
   MONGODB_URL=mongodb+srv://your-username:your-password@your-cluster.mongodb.net/dhobighat?retryWrites=true&w=majority
   DATABASE_NAME=dhobighat
   ```

### 3. Run the Application

```bash
# Development mode with auto-reload
python app.py

# Or using uvicorn directly
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Base URL: `http://localhost:8000`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information and available endpoints |
| GET | `/health` | Health check |
| POST | `/clothing-items` | Create a new clothing item |
| GET | `/clothing-items` | Get all clothing items (indexed by type) |
| GET | `/clothing-items/{item_id}` | Get a specific clothing item |
| GET | `/clothing-items/search/{name}` | Search clothing items by name |
| GET | `/clothing-items/type/{item_type}` | Get clothing items by type |
| PUT | `/clothing-items/{item_id}/cleaning-interval` | Update cleaning interval for specific item |
| PUT | `/clothing-items/type/{item_type}/cleaning-interval` | Update cleaning interval for all items of a type |
| GET | `/clothing-items/needing-cleaning` | Get items that need cleaning |
| GET | `/clothing-items/recently-cleaned` | Get recently cleaned items |

### Interactive API Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Example Usage

### Create a Clothing Item

```bash
curl -X POST "http://localhost:8000/clothing-items" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Blue T-Shirt",
    "clothingItemType": "shirt",
    "image": "https://example.com/blue-tshirt.jpg",
    "last_cleaned": "2024-01-15T10:30:00",
    "cleaning_interval_seconds": 604800
  }'
```
```

### Get All Clothing Items (Indexed by Type)

```bash
curl "http://localhost:8000/clothing-items?skip=0&limit=10"
```

**Response format:**
```json
{
  "shirt": [
    {
      "_id": "507f1f77bcf86cd799439011",
      "name": "Blue T-Shirt",
      "clothingItemType": "shirt",
      "image": "https://example.com/image.jpg",
      "last_cleaned": "2024-01-15T10:30:00",
      "cleaning_interval_seconds": 604800,
      "next_cleaning_date": "2024-01-22T10:30:00"
    }
  ],
  "pants": [
    {
      "_id": "507f1f77bcf86cd799439012",
      "name": "Red Jeans",
      "clothingItemType": "pants",
      "image": "https://example.com/image.jpg",
      "last_cleaned": "2024-01-15T10:30:00",
      "cleaning_interval_seconds": 259200,
      "next_cleaning_date": "2024-01-18T10:30:00"
    }
  ]
}
```

### Update Cleaning Interval for Specific Item

```bash
curl -X PUT "http://localhost:8000/clothing-items/{item_id}/cleaning-interval?cleaning_interval_seconds=86400"
```

### Update Cleaning Interval for All Items of a Type

```bash
curl -X PUT "http://localhost:8000/clothing-items/type/shirt/cleaning-interval?cleaning_interval_seconds=259200"
```

**Response:**
```json
{
  "message": "Updated cleaning interval for 3 items of type 'shirt'",
  "modified_count": 3,
  "item_type": "shirt",
  "new_interval_seconds": 259200
}
```

### Get Items Needing Cleaning

```bash
curl "http://localhost:8000/clothing-items/needing-cleaning"
```

## Data Models

### ClothingItemCreate
```json
{
  "name": "string",
  "clothingItemType": "string",
  "image": "string",
  "last_cleaned": "datetime",
  "cleaning_interval_seconds": "integer"
}
```

### ClothingItemResponse
```json
{
  "_id": "string",
  "name": "string",
  "clothingItemType": "string",
  "image": "string",
  "last_cleaned": "datetime",
  "cleaning_interval_seconds": "integer",
  "next_cleaning_date": "datetime"
}
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGODB_URL` | MongoDB connection string | `mongodb://localhost:27017` |
| `DATABASE_NAME` | Database name | `dhobighat` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |

## Development

### Project Structure

```
backend/
├── app.py              # Main FastAPI application
├── models.py           # Pydantic models
├── database.py         # MongoDB connection and configuration
├── crud.py            # CRUD operations
├── requirements.txt    # Python dependencies
├── env.example        # Environment variables example
└── README.md          # This file
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

## Production Deployment

1. Set up proper environment variables
2. Configure CORS origins for production
3. Use a production ASGI server like Gunicorn with Uvicorn workers
4. Set up proper MongoDB security and networking
5. Configure logging and monitoring

## License

MIT License

