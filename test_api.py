#!/usr/bin/env python3
"""
Simple test script to check Suno API connectivity.
"""
import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API key
SUNO_API_KEY = os.getenv("SUNO_API_KEY")

# API base URL
SUNO_API_BASE_URL = "https://apibox.erweima.ai/api/v1"

def test_api_connection():
    """Test basic connection to the Suno API."""
    print("Testing Suno API connection...")
    print(f"API Key: {SUNO_API_KEY[:5]}...{SUNO_API_KEY[-5:] if SUNO_API_KEY else 'Not set'}")
    
    if not SUNO_API_KEY:
        print("ERROR: SUNO_API_KEY is not set in the .env file")
        return False
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {SUNO_API_KEY}"
    }
    
    # Try a simple GET request first
    try:
        url = f"{SUNO_API_BASE_URL}/info"  # This endpoint may not exist, but let's try
        print(f"Testing GET request to: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text[:500]}")  # Show first 500 chars
        
        # If that fails, let's try another endpoint
        if response.status_code >= 400:
            print("\nTrying alternative endpoint...")
            alt_url = f"{SUNO_API_BASE_URL}/credit/balance"  # Try a credit balance check
            print(f"Testing GET request to: {alt_url}")
            alt_response = requests.get(alt_url, headers=headers, timeout=10)
            
            print(f"Status code: {alt_response.status_code}")
            print(f"Response: {alt_response.text[:500]}")
            
            if alt_response.status_code == 200:
                print("\nSUCCESS: Successfully connected to the Suno API!")
                try:
                    data = alt_response.json()
                    print(f"Credit balance: {json.dumps(data, indent=2)}")
                except:
                    pass
                return True
    except Exception as e:
        print(f"ERROR: Exception occurred: {e}")
    
    # If we got here, let's try a simple POST request
    try:
        print("\nTrying a minimal generation request...")
        payload = {
            "prompt": "Test connection",
            "style": "test",
            "title": "API Test",
            "customMode": True,
            "instrumental": True,  # Instrumental mode for smaller/faster generation
            "model": "V3_5"
        }
        
        gen_url = f"{SUNO_API_BASE_URL}/generate"
        print(f"Testing POST request to: {gen_url}")
        gen_response = requests.post(
            gen_url, 
            headers=headers, 
            json=payload,
            timeout=20
        )
        
        print(f"Status code: {gen_response.status_code}")
        print(f"Response: {gen_response.text[:500]}")
        
        if gen_response.status_code == 200:
            print("\nSUCCESS: Successfully sent a generation request!")
            return True
    except Exception as e:
        print(f"ERROR: Exception occurred during generation test: {e}")
    
    return False

if __name__ == "__main__":
    success = test_api_connection()
    print("\nTest result:", "SUCCESS" if success else "FAILURE")
