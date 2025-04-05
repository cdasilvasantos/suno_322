#!/usr/bin/env python3
"""
Utility script to check the status of a previously submitted Suno API task
and download the result if it's complete.
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

def check_task_status(task_id, output_file=None, debug=False):
    """
    Check the status of a task and download the result if complete.
    
    Args:
        task_id: The task ID to check
        output_file: Path to save the audio file if task is complete
        debug: Whether to print debug information
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
        f"{SUNO_API_BASE_URL}/task/{task_id}"
    ]
    
    task_details = None
    successful_endpoint = None
    
    for endpoint in endpoints:
        print(f"Trying endpoint: {endpoint}")
        response = requests.get(endpoint, headers=headers)
        
        if response.status_code == 200:
            print(f"Success with endpoint: {endpoint}")
            task_details = response.json()
            successful_endpoint = endpoint
            break
        else:
            print(f"Failed with status {response.status_code}: {endpoint}")
            print(f"Response: {response.text}")
    
    if not task_details:
        print("Failed to get task details from any endpoint.")
        return False
    
    if debug:
        print("Full API response:")
        print(json.dumps(task_details, indent=2))
    
    # Try to extract status using different possible paths
    status = None
    try:
        # Check various possible paths to status
        status = task_details.get('data', {}).get('status')
        if not status:
            status = task_details.get('status')
        if not status:
            # Search for any status field recursively in the JSON
            def find_status(obj):
                if isinstance(obj, dict):
                    if 'status' in obj:
                        return obj['status']
                    for k, v in obj.items():
                        result = find_status(v)
                        if result:
                            return result
                elif isinstance(obj, list):
                    for item in obj:
                        result = find_status(item)
                        if result:
                            return result
                return None
            
            status = find_status(task_details)
    except Exception as e:
        print(f"Error extracting status: {e}")
    
    print(f"Task status: {status}")
    
    # Check for completion
    if status == 'complete' or status == 'finished' or status == 'success':
        print("Task is complete!")
        
        # Try to extract audio URL
        audio_url = None
        try:
            # Look for various possible paths to the audio URL
            results = task_details.get('data', {}).get('results', [])
            if results and len(results) > 0:
                audio_url = results[0].get('audioUrl') or results[0].get('audio_url')
            
            if not audio_url:
                # Try alternative paths
                audio_url = task_details.get('data', {}).get('audioUrl')
            
            if not audio_url:
                # Search recursively for audioUrl or audio_url
                def find_audio_url(obj):
                    if isinstance(obj, dict):
                        if 'audioUrl' in obj:
                            return obj['audioUrl']
                        if 'audio_url' in obj:
                            return obj['audio_url']
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
                
                audio_url = find_audio_url(task_details)
        except Exception as e:
            print(f"Error extracting audio URL: {e}")
        
        if audio_url:
            print(f"Found audio URL: {audio_url}")
            
            if output_file:
                print(f"Downloading to {output_file}...")
                response = requests.get(audio_url)
                
                if response.status_code == 200:
                    with open(output_file, 'wb') as f:
                        f.write(response.content)
                    print(f"Download complete. File saved to {output_file}")
                    return True
                else:
                    print(f"Failed to download audio: {response.status_code}")
                    return False
            else:
                print("No output file specified. Use --output to download the file.")
                print(f"Audio URL: {audio_url}")
                return True
        else:
            print("No audio URL found in the response.")
            return False
    elif status == 'failed' or status == 'error':
        print("Task failed.")
        return False
    else:
        print("Task is still processing.")
        return False


def main():
    """Main function to check task status from command line."""
    parser = argparse.ArgumentParser(description='Check Suno API task status')
    parser.add_argument('--task-id', type=str, help='Task ID to check')
    parser.add_argument('--output', type=str, help='Output file path for audio')
    parser.add_argument('--debug', action='store_true', help='Print debug information')
    
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
            return
    
    check_task_status(task_id, args.output, args.debug)


if __name__ == "__main__":
    main()
