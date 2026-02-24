# Instagram Reels Scraper API 🎬

A FastAPI-based REST API for scraping Instagram Reels data.

## Features ✨

- **Fast & Modern**: Built with FastAPI for high performance
- **Type-Safe**: Pydantic models for request/response validation
- **Logging**: Comprehensive logging for debugging and monitoring
- **Error Handling**: Proper HTTP exceptions and error messages
- **Auto Documentation**: Interactive API docs at `/docs`

## Project Structure 📁

```
insta_api/
├── main.py              # Main FastAPI application
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Installation 🚀

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. **Clone or navigate to the project directory**:
   ```bash
   cd o:\python\django_web\insta_api
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the API 🏃

### Development Mode

Start the server with auto-reload:

```bash
uvicorn main:app --reload
```

Or using Python module:

```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## API Endpoints 📡

### 1. Root Endpoint
**GET** `/`

Returns a welcome message confirming the API is operational.

**Response**:
```json
{
  "message": "Instagram Reels Scraper API operational"
}
```

### 2. Health Check
**GET** `/health`

Returns the health status of the API.

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-01T12:13:29.123456"
}
```

### 3. Scrape Reel
**POST** `/scrape`

Scrapes Instagram reel data from the provided URL.

**Request Body**:
```json
{
  "reel_url": "https://www.instagram.com/reel/ABC123/"
}
```

**Response** (200 OK):
```json
{
  "id": "ABC123",
  "reel_url": "https://www.instagram.com/reel/ABC123/",
  "video_url": "https://example.com/video.mp4",
  "thumbnail_url": "https://example.com/thumbnail.jpg",
  "caption": "Sample caption",
  "posted_at": "2025-10-01T12:00:00",
  "views": 1000,
  "likes": 100,
  "comments": 10
}
```

**Error Responses**:
- `400 Bad Request`: Invalid URL format
- `500 Internal Server Error`: Scraping failed

## Data Models 📊

### ScrapeRequest
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| reel_url | string | Yes | Instagram reel URL |

**Validation**:
- Must contain `instagram.com` or `instagr.am`
- Must contain `/reel/` or `/p/` in the path

### ReelData
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Unique reel identifier |
| reel_url | string | Yes | Original reel URL |
| video_url | string | No | Direct video URL |
| thumbnail_url | string | Yes | Thumbnail image URL |
| caption | string | No | Reel caption/description |
| posted_at | datetime | Yes | Publication timestamp |
| views | integer | No | View count |
| likes | integer | No | Like count |
| comments | integer | No | Comment count |

## Usage Examples 💡

### Using cURL

```bash
# Test root endpoint
curl http://localhost:8000/

# Scrape a reel
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{"reel_url": "https://www.instagram.com/reel/ABC123/"}'
```

### Using Python requests

```python
import requests

# Scrape a reel
response = requests.post(
    "http://localhost:8000/scrape",
    json={"reel_url": "https://www.instagram.com/reel/ABC123/"}
)

if response.status_code == 200:
    reel_data = response.json()
    print(f"Scraped reel: {reel_data['id']}")
else:
    print(f"Error: {response.json()['detail']}")
```

### Using JavaScript fetch

```javascript
fetch('http://localhost:8000/scrape', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    reel_url: 'https://www.instagram.com/reel/ABC123/'
  })
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));
```

## Development Notes 🔧

### Current Implementation

The scraper function (`scrape_instagram_reel`) currently returns **mock data**. This is a placeholder for actual scraping logic.

### Implementing Real Scraping

To implement actual Instagram scraping, you can use libraries like:

1. **instaloader**: Official Instagram scraper
   ```bash
   pip install instaloader
   ```

2. **requests + BeautifulSoup**: For HTML parsing
   ```bash
   pip install requests beautifulsoup4
   ```

3. **selenium**: For JavaScript-heavy pages
   ```bash
   pip install selenium
   ```

**⚠️ Important**: Instagram scraping may violate their Terms of Service. Use responsibly and consider using official APIs when available.

### Adding to requirements.txt

If you add new dependencies, update `requirements.txt`:

```bash
pip freeze > requirements.txt
```

## Logging 📝

The API uses Python's built-in logging module with INFO level. Logs include:
- Endpoint access
- Scraping attempts
- Errors and exceptions

Log format:
```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

## Environment Variables 🔐

For production deployment, consider using environment variables for:
- API keys
- Database connections
- Rate limiting settings
- CORS origins

Create a `.env` file and use `python-dotenv` (already in requirements):

```python
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("INSTAGRAM_API_KEY")
```

## Production Deployment 🚀

### Using Gunicorn

```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Using Docker

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t insta-scraper-api .
docker run -p 8000:8000 insta-scraper-api
```

## License 📄

This project is for educational purposes. Please respect Instagram's Terms of Service and robots.txt.

## Contributing 🤝

Contributions are welcome! Please ensure:
- Code follows PEP 8 style guidelines
- All endpoints have proper documentation
- Error handling is comprehensive
- Tests are included for new features

## How to install the playwright 
.venv\Scripts\python.exe -m playwright install

## Support 💬

For issues or questions, please open an issue in the repository.

---

**Built with FastAPI** ⚡
