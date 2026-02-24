#!/usr/bin/env python3
"""
Test script for the Instagram Reels Scraper API
"""

import asyncio
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Fix for Windows asyncio event loop policy
if asyncio.get_event_loop_policy() != asyncio.WindowsSelectorEventLoopPolicy():
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import requests
import json
import time
from datetime import datetime

def test_api_endpoint():
    """Test the API endpoints"""
    base_url = "http://127.0.0.1:8000"

    print("🧪 Testing Instagram Reels Scraper API")
    print("=" * 50)

    # Test 1: Root endpoint
    print("1. Testing root endpoint...")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print(f"✅ Root endpoint: {response.json()}")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Root endpoint error: {e}")

    # Test 2: Health endpoint
    print("\n2. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print(f"✅ Health check: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")

    # Test 3: Scrape reels from a public account
    print("\n3. Testing reel scraping (instagram account)...")
    try:
        response = requests.get(f"{base_url}/scrape/user/instagram?limit=3")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Scraped {data['reels_count']} reels from @{data['username']}")
            print(f"   Status: {data['status']}")

            # Show first reel details
            if data['reels']:
                reel = data['reels'][0]
                print(f"   Sample reel: {reel['id']}")
                print(f"   Caption: {reel['caption'][:50]}..." if reel['caption'] else "   No caption")
                print(f"   Views: {reel.get('views', 'N/A')}")
        elif response.status_code == 403:
            print(f"❌ Account is private")
        elif response.status_code == 404:
            print(f"❌ Account not found")
        elif response.status_code == 429:
            print(f"❌ Rate limited")
        else:
            print(f"❌ Scraping failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Scraping error: {e}")

    # Test 4: Scrape from another public account
    print("\n4. Testing reel scraping (natgeo account)...")
    try:
        response = requests.get(f"{base_url}/scrape/user/natgeo?limit=2")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Scraped {data['reels_count']} reels from @{data['username']}")
        elif response.status_code == 403:
            print(f"❌ Account is private")
        elif response.status_code == 404:
            print(f"❌ Account not found")
        else:
            print(f"❌ Scraping failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Scraping error: {e}")

    print("\n" + "=" * 50)
    print("✨ Test completed!")

def test_api_with_different_limits():
    """Test API with different limit values"""
    base_url = "http://127.0.0.1:8000"

    print("\n🔢 Testing different limit values...")

    for limit in [1, 5, 10]:
        print(f"\nTesting limit={limit}...")
        try:
            start_time = time.time()
            response = requests.get(f"{base_url}/scrape/user/instagram?limit={limit}")
            end_time = time.time()

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Limit {limit}: {data['reels_count']} reels in {end_time-start_time:.2f}s")
            else:
                print(f"❌ Limit {limit}: Failed ({response.status_code})")
        except Exception as e:
            print(f"❌ Limit {limit}: Error - {e}")

if __name__ == "__main__":
    # First check if server is running
    try:
        requests.get("http://127.0.0.1:8000/", timeout=5)
        print("🚀 API server is running!")
        test_api_endpoint()
        test_api_with_different_limits()
    except requests.exceptions.ConnectionError:
        print("❌ API server is not running!")
        print("Please start the server first:")
        print("  uvicorn main:app --host 127.0.0.1 --port 8000 --reload")
    except Exception as e:
        print(f"❌ Error connecting to API: {e}")
