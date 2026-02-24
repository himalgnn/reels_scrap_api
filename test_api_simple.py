#!/usr/bin/env python3
"""
Simple test script for Instagram Reels Scraper API
Tests the basic endpoints without complex async operations
"""

import requests
import time
import sys

def test_api_basic():
    """Test basic API endpoints"""
    base_url = "http://127.0.0.1:8000"

    print("🧪 Testing Instagram Reels Scraper API (Basic)")
    print("=" * 50)

    # Test 1: Root endpoint
    print("1. Testing root endpoint...")
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Root: {data['message']}")
        else:
            print(f"❌ Root failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Root error: {e}")
        return False

    # Test 2: Health endpoint
    print("\n2. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health: {data['status']}")
        else:
            print(f"❌ Health failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health error: {e}")
        return False

    print("\n✅ Basic API tests passed!")
    print("🎯 API server is running correctly")
    print("🔗 Try: http://localhost:8000/docs for interactive testing")
    return True

def check_server_status():
    """Check if server is running"""
    try:
        requests.get("http://127.0.0.1:8000/", timeout=5)
        return True
    except:
        print("❌ API server is not running!")
        print("Please start the server first:")
        print("  uvicorn main:app --host 127.0.0.1 --port 8000 --reload")
        return False

if __name__ == "__main__":
    if check_server_status():
        test_api_basic()
    else:
        sys.exit(1)
