#!/usr/bin/env python3
"""
Test script to debug St. Louis 311 API connection
"""

import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_stl311_api():
    """Test the St. Louis 311 API directly"""
    
    api_key = os.getenv("STL311_API_KEY")
    print(f"API Key: {api_key[:10]}..." if api_key else "No API key found")
    
    # Use the exact format from the original project
    base_url = "https://www.stlouis-mo.gov/powernap/stlouis/api.cfm"
    url = f"{base_url}/requests.json"
    
    print(f"\n=== Testing API: {url} ===")
    
    # Test with different parameter combinations
    test_cases = [
        {
            'name': 'Basic request with API key',
            'params': {
                'api_key': api_key,
                'start_date': '2024-08-01',
                'end_date': '2024-08-08'
            }
        },
        {
            'name': 'Request without status',
            'params': {
                'api_key': api_key,
                'start_date': '2024-08-01',
                'end_date': '2024-08-08',
                'page_size': 10
            }
        },
        {
            'name': 'Request with status=open',
            'params': {
                'api_key': api_key,
                'start_date': '2024-08-01',
                'end_date': '2024-08-08',
                'status': 'open',
                'page_size': 10
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n--- {test_case['name']} ---")
        try:
            response = requests.get(url, params=test_case['params'], timeout=30)
            print(f"Status Code: {response.status_code}")
            print(f"Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
            
            if response.status_code == 200:
                print("SUCCESS! API responded with 200")
                try:
                    data = response.json()
                    print(f"Response type: {type(data)}")
                    if isinstance(data, dict):
                        print(f"Response keys: {list(data.keys())}")
                        if 'service_requests' in data:
                            print(f"Service requests count: {len(data['service_requests'])}")
                    elif isinstance(data, list):
                        print(f"Response list length: {len(data)}")
                except Exception as e:
                    print(f"JSON parse error: {e}")
                    print(f"Response text (first 500 chars): {response.text[:500]}")
            else:
                print(f"Error response: {response.text[:500]}")
                
        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    test_stl311_api() 