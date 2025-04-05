#!/usr/bin/env python3
"""
Utility script to download a generated song from Suno API.
This script retries multiple times with different download strategies.
"""
import os
import sys
import json
import time
import argparse
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys
SUNO_API_KEY = os.getenv("SUNO_API_KEY")

# API endpoints
SUNO_API_BASE_URL = "https://apibox.erweima.ai/api/v1"

def download_file(url, output_path, max_retries=5):
    """
    Download a file from a URL with retries.
    
    Args:
        url: URL to download
        output_path: Where to save the file
        max_retries: Maximum number of retry attempts
        
    Returns:
        bool: Whether download was successful
    """
    retry_count = 0
    while retry_count < max_retries:
        try:
            print(f"Download attempt {retry_count + 1}/{max_retries} from {url}")
            
            # Try with streaming (better for large files)
            with requests.get(url, stream=True) as response:
                response.raise_for_status()
                
                # Get file size if available
                file_size = int(response.headers.get('content-length', 0))
                if file_size:
                    print(f"File size: {file_size / 1024 / 1024:.2f} MB")
                
                # Download with progress tracking
                with open(output_path, 'wb') as f:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if file_size:
                                progress = (downloaded / file_size) * 100
                                print(f"\rProgress: {progress:.1f}%", end='')
                print("\nDownload complete!")
                
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    print(f"File saved to {output_path}")
                    return True
                else:
                    print("Downloaded file is empty. Retrying...")
            
        except Exception as e:
            print(f"Download error: {e}")
        
        # Increase wait time between retries
        wait_time = 2 ** retry_count
        print(f"Retrying in {wait_time} seconds...")
        time.sleep(wait_time)
        retry_count += 1
    
    return False

def get_task_details(task_id):
    """
    Retrieve task details from the API.
    
    Args:
        task_id: The task ID to check
        
    Returns:
        dict: Task details if successful, None otherwise
    """
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {SUNO_API_KEY}"
    }
    
    # Try different endpoint formats
    endpoints = [
        f"{SUNO_API_BASE_URL}/generate/status?taskId={task_id}",
        f"{SUNO_API_BASE_URL}/generate/result?taskId={task_id}",
        f"{SUNO_API_BASE_URL}/task/{task_id}",
        f"{SUNO_API_BASE_URL}/generate/{task_id}",
        f"{SUNO_API_BASE_URL}/generate/audio?taskId={task_id}"
    ]
    
    for endpoint in endpoints:
        print(f"Trying endpoint: {endpoint}")
        try:
            response = requests.get(endpoint, headers=headers)
            if response.status_code == 200:
                print(f"Success with endpoint: {endpoint}")
                return response.json()
            else:
                print(f"Failed with status {response.status_code}: {endpoint}")
        except Exception as e:
            print(f"Error with endpoint {endpoint}: {e}")
    
    return None

def find_audio_url(obj):
    """
    Recursively search for audio URL in a nested JSON object.
    
    Args:
        obj: JSON object to search
        
    Returns:
        str: Audio URL if found, None otherwise
    """
    if isinstance(obj, dict):
        # Direct field matches
        for key in ['audioUrl', 'audio_url', 'url', 'mp3Url', 'streamUrl']:
            if key in obj and isinstance(obj[key], str) and (
                    obj[key].startswith('http') and 
                    ('.mp3' in obj[key] or '.wav' in obj[key] or '/audio/' in obj[key])
                ):
                return obj[key]
        
        # Search recursively in all values
        for k, v in obj.items():
            result = find_audio_url(v)
            if result:
                return result
    
    elif isinstance(obj, list):
        for item in obj:
            result = find_audio_url(item)
            if result:
                return result
    
    return None

def download_song(task_id, output_file, check_interval=10, max_checks=30):
    """
    Check for song completion and download when ready.
    
    Args:
        task_id: The task ID to check
        output_file: Path to save the audio file
        check_interval: Seconds between status checks
        max_checks: Maximum number of status checks
        
    Returns:
        bool: Whether download was successful
    """
    print(f"Monitoring task ID: {task_id}")
    print(f"Will save to: {output_file}")
    
    # If output file already exists, ask for confirmation to overwrite
    if os.path.exists(output_file):
        print(f"Warning: {output_file} already exists.")
        response = input("Overwrite? (y/n): ")
        if response.lower() != 'y':
            print("Aborted.")
            return False
    
    checks = 0
    while checks < max_checks:
        print(f"\nCheck {checks + 1}/{max_checks}...")
        
        task_details = get_task_details(task_id)
        if not task_details:
            print("Could not retrieve task details.")
            checks += 1
            time.sleep(check_interval)
            continue
        
        # Print the full response for debugging
        print("API Response:")
        print(json.dumps(task_details, indent=2))
        
        # Look for status
        status = None
        if isinstance(task_details, dict):
            # Try common status paths
            status = task_details.get('data', {}).get('status')
            if not status:
                status = task_details.get('status')
        
        print(f"Task status: {status}")
        
        # Check if complete
        if status in ['complete', 'finished', 'success', 'done']:
            # Find audio URL in the response
            audio_url = find_audio_url(task_details)
            
            if audio_url:
                print(f"Audio URL found: {audio_url}")
                success = download_file(audio_url, output_file)
                if success:
                    return True
                else:
                    print("Download failed. Will retry on next check.")
            else:
                print("No audio URL found in response. Will check again.")
        
        elif status in ['failed', 'error']:
            print("Task failed.")
            return False
        
        else:
            print(f"Task still processing (status: {status}). Checking again in {check_interval} seconds...")
        
        checks += 1
        time.sleep(check_interval)
    
    print(f"Exceeded maximum checks ({max_checks}). Task may still be processing.")
    return False

def main():
    """Main function to download song from command line."""
    parser = argparse.ArgumentParser(description='Download song from Suno API')
    parser.add_argument('--task-id', type=str, help='Task ID to download')
    parser.add_argument('--output', type=str, default='output.mp3', help='Output file path')
    parser.add_argument('--interval', type=int, default=10, help='Check interval in seconds')
    parser.add_argument('--max-checks', type=int, default=30, help='Maximum number of status checks')
    
    args = parser.parse_args()
    
    task_id = args.task_id
    
    # If no task ID provided, try to read from file
    if not task_id:
        try:
            with open('last_task_id.txt', 'r') as f:
                task_id = f.read().strip()
            print(f"Using task ID from last_task_id.txt: {task_id}")
        except FileNotFoundError:
            print("No task ID provided and no last_task_id.txt file found.")
            sys.exit(1)
    
    download_song(task_id, args.output, args.interval, args.max_checks)

if __name__ == "__main__":
    main()
