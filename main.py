#!/usr/bin/env python3
"""
Lyrics and Music Generator using Anthropic for lyrics and Suno API for music generation.
"""
import os
import json
import time
import argparse
import requests
from dotenv import load_dotenv
from anthropic import Anthropic

# Load environment variables
load_dotenv(override=True)

# API keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
SUNO_API_KEY = os.getenv("SUNO_API_KEY")

if SUNO_API_KEY:
    print(f"Loaded SUNO API key: {SUNO_API_KEY[:8]}...")
else:
    print("WARNING: SUNO API key not found in .env file.")
# API endpoints
SUNO_API_BASE_URL = "https://apibox.erweima.ai/api/v1"

# Suno API Status Codes
SUNO_STATUS = {
    "PENDING": "Pending execution",
    "TEXT_SUCCESS": "Text generation successful",
    "FIRST_SUCCESS": "First song generation successful",
    "SUCCESS": "Generation successful",
    "CREATE_TASK_FAILED": "Task creation failed",
    "GENERATE_AUDIO_FAILED": "Song generation failed",
    "CALLBACK_EXCEPTION": "Callback exception",
    "SENSITIVE_WORD_ERROR": "Sensitive word error"
}

class LyricsGenerator:
    """Class to generate lyrics using Anthropic's Claude model."""
    
    def __init__(self):
        """Initialize the Anthropic client."""
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
    
    def generate_lyrics(self, prompt, style=None, num_verses=2, has_chorus=True):
        """
        Generate lyrics using Anthropic's Claude model.
        
        Args:
            prompt: The main theme or idea for the lyrics
            style: Music style (e.g., "rock", "pop", "rap")
            num_verses: Number of verses to generate
            has_chorus: Whether to include a chorus
            
        Returns:
            dict: Generated lyrics with title and content
        """
        # Construct a detailed prompt for Claude
        system_prompt = """You are a professional songwriter with expertise in many musical styles.
        Create original, creative, and emotionally resonant lyrics that feel authentic to the requested style.
        Structure the lyrics properly and ensure they have a cohesive theme."""
        
        style_instruction = f"Write in {style} style. " if style else ""
        structure_instruction = f"Include {num_verses} verses"
        structure_instruction += " and a chorus that repeats." if has_chorus else "."
        
        user_prompt = f"{style_instruction}Write lyrics for a song about: {prompt}. {structure_instruction} \
        Include a title at the top. Format the output so verses and chorus are clearly separated."
        
        # Get response from Claude
        response = self.client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        # Extract lyrics and title
        lyrics_text = response.content[0].text
        
        # Parse out the title (assuming it's the first line)
        lines = lyrics_text.strip().split('\n')
        title = lines[0].replace("#", "").strip()
        content = '\n'.join(lines[1:]).strip()
        
        return {
            "title": title,
            "content": content,
            "full_text": lyrics_text
        }


class MusicGenerator:
    """Class to generate music using Suno API with lyrics."""
    
    def __init__(self, debug=False):
        """
        Initialize with the Suno API key.
        
        Args:
            debug: Enable detailed logging
        """
        self.api_key = SUNO_API_KEY
        self.debug = debug
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Verify API key is set
        if not self.api_key or self.api_key.strip() == "":
            print("ERROR: SUNO_API_KEY environment variable is not set or is empty.")
            print("Please add your Suno API key to the .env file.")
    
    def generate_music(self, title, lyrics, style, custom_mode=True, instrumental=False, model="V3_5"):
        """
        Generate music with lyrics using Suno API.
        
        Args:
            title: Song title
            lyrics: Lyrics content
            style: Music style description
            custom_mode: Whether to use custom mode (True) or non-custom mode (False)
            instrumental: Whether to generate instrumental music (no lyrics)
            model: Model version to use (V3_5 or V4)
            
        Returns:
            dict: Response from Suno API containing task ID and other details
        """
        # Prepare request payload
        payload = {
            "prompt": lyrics,
            "style": style if custom_mode else "",
            "title": title if custom_mode else "",
            "customMode": custom_mode,
            "instrumental": instrumental,
            "model": model,
            "callBackUrl": "https://example.com/callback"  # Placeholder, won't be used
        }
        
        # Log request for debugging
        print(f"Sending request to Suno API: {json.dumps(payload, indent=2)}")
        print(f"API URL: {SUNO_API_BASE_URL}/generate")
        
        # Make API request to generate audio
        try:
            response = requests.post(
                f"{SUNO_API_BASE_URL}/generate",
                headers=self.headers,
                json=payload,
                timeout=30  # Add timeout to prevent hanging
            )
            
            # Check for successful response
            if response.status_code == 200:
                resp_json = response.json()
                if self.debug:
                    print(f"API Response: {json.dumps(resp_json, indent=2)}")
                return resp_json
            else:
                print(f"Error generating music: Status code {response.status_code}")
                print(f"Response: {response.text}")
                
                # Try to parse as JSON to provide better error info
                try:
                    error_data = response.json()
                    if 'code' in error_data and 'msg' in error_data:
                        print(f"API Error Code: {error_data['code']}")
                        print(f"Error Message: {error_data['msg']}")
                        
                        if error_data['code'] == 401:
                            print("Authentication failed. Please check your API key.")
                        elif error_data['code'] == 429:
                            print("Insufficient credits. Please add credits to your account.")
                        elif error_data['code'] == 413:
                            print("Theme or prompt too long. Please use a shorter theme or lyrics.")
                except:
                    pass  # Ignore if not JSON
                
                return None
        except requests.exceptions.RequestException as e:
            print(f"Network error when contacting Suno API: {e}")
            return None
    
    def find_audio_url(self, obj):
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
                if key in obj and obj[key]:
                    return obj[key]
            
            # Check for common paths for audio URL
            if 'data' in obj and isinstance(obj['data'], dict):
                data = obj['data']
                
                # Check for direct audio_url in data
                if 'audio_url' in data:
                    return data['audio_url']
                
                # Check for results array in data
                if 'results' in data and isinstance(data['results'], list) and data['results']:
                    result = data['results'][0]  # Take first result
                    if isinstance(result, dict) and 'audio_url' in result:
                        return result['audio_url']
            
            # Recursive search
            for k, v in obj.items():
                result = self.find_audio_url(v)
                if result:
                    return result
        elif isinstance(obj, list):
            for item in obj:
                result = self.find_audio_url(item)
                if result:
                    return result
        
        return None
        
    def find_audio_id(self, obj):
        """
        Recursively search for audio ID in a nested JSON object.
        
        Args:
            obj: JSON object to search
            
        Returns:
            str: Audio ID if found, None otherwise
        """
        if isinstance(obj, dict):
            # Direct field matches
            for key in ['audioId', 'audio_id', 'id']:
                if key in obj and obj[key]:
                    return obj[key]
            
            # Check for common paths for audio ID
            if 'data' in obj and isinstance(obj['data'], dict):
                data = obj['data']
                
                # Check for direct audioId in data
                if 'audioId' in data:
                    return data['audioId']
                
                # Check for results array in data
                if 'results' in data and isinstance(data['results'], list) and data['results']:
                    result = data['results'][0]  # Take first result
                    if isinstance(result, dict) and 'audioId' in result:
                        return result['audioId']
            
            # Recursive search
            for k, v in obj.items():
                result = self.find_audio_id(v)
                if result:
                    return result
        elif isinstance(obj, list):
            for item in obj:
                result = self.find_audio_id(item)
                if result:
                    return result
        
        return None
    
    def check_generation_status(self, task_id):
        """
        Check the status of a generation task.
        
        Args:
            task_id: The task ID returned from generate_music
            
        Returns:
            dict: Task details including status and results if available
        """
        # The primary endpoint according to documentation
        primary_endpoint = f"{SUNO_API_BASE_URL}/generate/record-info?taskId={task_id}"
        print(f"Checking status at: {primary_endpoint}")
        
        try:
            response = requests.get(primary_endpoint, headers=self.headers, timeout=30)
            if response.status_code == 200:
                print("Status check successful")
                return response.json()
            
            # If primary endpoint fails, try these alternative endpoints
            alternate_endpoints = [
                f"{SUNO_API_BASE_URL}/generate/status?taskId={task_id}",
                f"{SUNO_API_BASE_URL}/generate/result?taskId={task_id}",
                f"{SUNO_API_BASE_URL}/task/{task_id}",
                f"{SUNO_API_BASE_URL}/generate/{task_id}"
            ]
            
            for endpoint in alternate_endpoints:
                print(f"Primary endpoint failed, trying: {endpoint}")
                alt_response = requests.get(endpoint, headers=self.headers, timeout=30)
                
                if alt_response.status_code == 200:
                    print(f"Success with alternate endpoint: {endpoint}")
                    return alt_response.json()
            
            print("All endpoints failed for status check")
            return None
        
        except requests.exceptions.RequestException as e:
            print(f"Network error when checking status: {e}")
            return None
    
    def get_status_description(self, status_code):
        """
        Get a human-readable description of a status code.
        
        Args:
            status_code: Status code from the API
            
        Returns:
        """
        return SUNO_STATUS.get(status_code, f"Unknown status: {status_code}")
    
    def generate_mp4(self, task_id, audio_id, output_path):
        """
        Generate an MP4 video for an existing audio track.
        
        Args:
            task_id: Task ID from the audio generation
            audio_id: Audio ID of the generated audio
            output_path: Path where to save the MP4 file
            
        Returns:
            dict: Response from the API with a standardized structure
        """
        # Prepare request payload
        payload = {
            "taskId": task_id,
            "audioId": audio_id,
            "callBackUrl": "https://example.com/callback"  # Placeholder
        }
        
        # Log request for debugging
        print(f"Sending MP4 generation request to Suno API: {json.dumps(payload, indent=2)}")
        print(f"API URL: {SUNO_API_BASE_URL}/mp4/generate")
        
        # Make API request to generate MP4
        try:
            response = requests.post(
                f"{SUNO_API_BASE_URL}/mp4/generate",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            print(f"Response status code: {response.status_code}")
            
            # Try to parse response as JSON
            try:
                resp_json = response.json()
                print(f"Raw API response: {response.text}")
            except ValueError:
                print(f"Error: Response is not valid JSON: {response.text}")
                return {
                    "success": False, 
                    "error": "Invalid JSON response", 
                    "error_code": "PARSE_ERROR",
                    "data": {}
                }
            
            # Check for successful response
            if response.status_code == 200:
                if self.debug:
                    print(f"API Response: {json.dumps(resp_json, indent=2)}")
                
                # Check if the API returned an error code in the response
                if isinstance(resp_json, dict) and resp_json.get('code') != 200:
                    error_code = resp_json.get('code')
                    error_message = resp_json.get('msg', 'Unknown error')
                    print(f"API Error Code: {error_code}")
                    print(f"Error Message: {error_message}")
                    
                    return {
                        "success": False,
                        "error": error_message,
                        "error_code": error_code,
                        "data": resp_json.get('data', {})
                    }
                
                # Ensure we have a standardized response structure
                if not isinstance(resp_json, dict):
                    print(f"Warning: Response is not a dictionary, converting: {type(resp_json)}")
                    resp_json = {"data": resp_json}
                
                # Add success flag
                resp_json["success"] = True
                
                # Ensure data field exists
                if "data" not in resp_json:
                    resp_json["data"] = {}
                
                # Extract task ID if available
                task_id = None
                if "data" in resp_json and isinstance(resp_json["data"], dict):
                    task_id = resp_json["data"].get("taskId")
                    if task_id:
                        print(f"Found MP4 task ID in response: {task_id}")
                
                # If no task ID in data, try to find it elsewhere in the response
                if not task_id:
                    if "taskId" in resp_json:
                        task_id = resp_json["taskId"]
                        resp_json["data"]["taskId"] = task_id
                        print(f"Found MP4 task ID at root level: {task_id}")
                
                return resp_json
            elif response.status_code == 401:
                print("Authentication error: You do not have access permissions for MP4 generation")
                print("Please check your API key and ensure you have MP4 generation permissions")
                return {
                    "success": False, 
                    "error": "Authentication error: You do not have access permissions", 
                    "error_code": 401,
                    "data": {}
                }
            else:
                print(f"Error generating MP4: Status code {response.status_code}")
                print(f"Response: {response.text}")
                
                # Provide better error info
                error_message = "Unknown error"
                error_code = response.status_code
                
                if isinstance(resp_json, dict):
                    if 'code' in resp_json and 'msg' in resp_json:
                        error_code = resp_json['code']
                        error_message = resp_json['msg']
                        print(f"API Error Code: {error_code}")
                        print(f"Error Message: {error_message}")
                
                return {
                    "success": False, 
                    "error": error_message, 
                    "error_code": error_code,
                    "data": {}
                }
        except requests.exceptions.RequestException as e:
            print(f"Network error when contacting Suno API for MP4 generation: {e}")
            return {
                "success": False, 
                "error": str(e), 
                "error_code": "NETWORK_ERROR",
                "data": {}
            }
            
    def check_mp4_status(self, task_id):
        """
        Check the status of an MP4 generation task.
        
        Args:
            task_id: The task ID returned from generate_mp4
            
        Returns:
            dict: Task details including status and results if available
        """
        # Try different endpoint formats based on the API documentation
        endpoints = [
            f"{SUNO_API_BASE_URL}/mp4/record-info?taskId={task_id}",  # Same format as audio endpoint
            f"{SUNO_API_BASE_URL}/mp4/generate/record-info?taskId={task_id}",  # Alternative format
            f"{SUNO_API_BASE_URL}/mp4/status?taskId={task_id}"  # Original format
        ]
        
        for endpoint in endpoints:
            try:
                print(f"Checking MP4 status at: {endpoint}")
                response = requests.get(
                    endpoint,
                    headers=self.headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    resp_json = response.json()
                    if self.debug:
                        print(f"MP4 Status API Response: {json.dumps(resp_json, indent=2)}")
                    else:
                        print(f"Status check successful")
                    return resp_json
                elif response.status_code != 404:  # If not 404, might be a valid error response
                    print(f"Error checking MP4 status: Status code {response.status_code}")
                    print(f"Response: {response.text}")
                    # If we get a non-404 error, it might be a valid endpoint with an error
                    # So we'll stop trying other endpoints
                    return None
            except requests.exceptions.RequestException as e:
                print(f"Network error when checking MP4 status at {endpoint}: {e}")
        
        print("All MP4 status endpoints returned 404 or failed. The API endpoint may have changed.")
        return None
    
    def download_mp4(self, video_url, output_path, max_retries=5):
        """
        Download the generated MP4 video to a local file with retry mechanism.
        
        Args:
            video_url: URL to the generated video
            output_path: Path where to save the downloaded file
            max_retries: Maximum number of retry attempts
            
        Returns:
            bool: True if download was successful, False otherwise
        """
        print(f"Downloading MP4 video to {output_path}...")
        
        retry_count = 0
        while retry_count < max_retries:
            try:
                # Stream the download to handle large files
                with requests.get(video_url, stream=True, timeout=60) as r:
                    r.raise_for_status()
                    
                    # Create directory if it doesn't exist
                    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                    
                    # Write to file
                    with open(output_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                
                print(f"MP4 video downloaded successfully to {output_path}")
                return True
            
            except requests.exceptions.RequestException as e:
                retry_count += 1
                print(f"Download attempt {retry_count}/{max_retries} failed: {e}")
                
                if retry_count < max_retries:
                    wait_time = 5 * retry_count  # Exponential backoff
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print("Maximum retry attempts reached. Download failed.")
                    return False
        
        return False
    
    def monitor_and_download_mp4(self, task_id, output_path, max_checks=30, check_interval=10):
        """
        Monitor an MP4 generation task until completion and download the result.
        
        Args:
            task_id: MP4 Task ID to monitor
            output_path: Where to save the downloaded MP4 file
            max_checks: Maximum number of status checks
            check_interval: Seconds between checks
            
        Returns:
            bool: True if download was successful, False otherwise
        """
        print(f"Monitoring MP4 task ID: {task_id}")
        print(f"Will save MP4 to: {output_path}")
        
        # Save MP4 task ID to a file for later use if needed
        with open('last_mp4_task_id.txt', 'w') as f:
            f.write(task_id)
        
        checks = 0
        while checks < max_checks:
            print(f"\nMP4 Check {checks + 1}/{max_checks}...")
            
            task_details = self.check_mp4_status(task_id)
            if not task_details:
                print("Could not retrieve MP4 task details, waiting before retry...")
                time.sleep(check_interval)
                checks += 1
                continue
            
            # Check if we have an error in the API response
            api_code = task_details.get('code')
            if api_code and api_code != 200:
                error_msg = task_details.get('msg', 'Unknown error')
                print(f"API error: {api_code} - {error_msg}")
                return False
            
            # Check if the MP4 is ready
            # First, check if the response has the expected structure
            data = task_details.get('data', {})
            
            # If data is empty, the response might be directly at the root level
            if not data and isinstance(task_details, dict):
                # Check if this looks like a direct response
                if 'taskId' in task_details and 'musicId' in task_details:
                    data = task_details
            
            # Try to determine status
            status = data.get('status')
            
            # Check for completion based on the completeTime field
            complete_time = data.get('completeTime')
            if complete_time and not status:
                status = 'complete'
            
            # Display more detailed status information if available
            status_desc = ""
            if data.get('statusDesc'):
                status_desc = data.get('statusDesc')
            elif data.get('status_desc'):
                status_desc = data.get('status_desc')
            
            if status_desc:
                print(f"Current MP4 status: {status} - {status_desc}")
            elif status:
                print(f"Current MP4 status: {status}")
            else:
                print(f"MP4 status: Processing")
                if self.debug:
                    print(f"Raw data: {json.dumps(data, indent=2)[:200]}...")
            
            # Check for completion or failure
            if status == 'complete' or status == 'SUCCESS' or status == 'FIRST_SUCCESS':
                print("MP4 generation is complete!")
                
                # Get the video URL - try different possible field names
                video_url = None
                for field in ['video_url', 'videoUrl', 'url', 'mp4Url', 'mp4_url', 'videoPath']:
                    if field in data:
                        video_url = data.get(field)
                        break
                
                # Check for a videoPath that needs to be converted to a full URL
                if video_url and not video_url.startswith('http'):
                    # This might be just a path, try to construct a full URL
                    if video_url.startswith('/'):
                        video_url = f"https://apiboxfiles.erweima.ai{video_url}"
                    else:
                        video_url = f"https://apiboxfiles.erweima.ai/{video_url}"
                    print(f"Constructed full video URL: {video_url}")
                
                # If still not found, search recursively
                if not video_url:
                    def find_url(obj, keys):
                        if isinstance(obj, dict):
                            for key in keys:
                                if key in obj:
                                    return obj[key]
                            for k, v in obj.items():
                                result = find_url(v, keys)
                                if result:
                                    return result
                        elif isinstance(obj, list):
                            for item in obj:
                                result = find_url(item, keys)
                                if result:
                                    return result
                        return None
                    
                    video_url = find_url(task_details, ['video_url', 'videoUrl', 'url', 'mp4Url', 'mp4_url', 'videoPath'])
                
                if video_url:
                    print(f"Found video URL: {video_url}")
                    success = self.download_mp4(video_url, output_path)
                    return success
                else:
                    print("No video URL found in the response.")
                    if self.debug:
                        print(f"Full response: {json.dumps(task_details, indent=2)}")
                    return False
            elif status == 'failed' or status == 'FAILED' or status == 'ERROR':
                print("MP4 generation failed.")
                error_reason = data.get('error') or data.get('errorReason') or data.get('error_reason') or ''
                if error_reason:
                    print(f"Error reason: {error_reason}")
                return False
            else:
                print(f"MP4 still processing. Checking again in {check_interval} seconds...")
            
            checks += 1
            time.sleep(check_interval)
        
        print("Exceeded maximum checks. MP4 task may still be processing.")
        print(f"You can check again later using: python main.py --check-mp4-task {task_id} --mp4-output {output_path}")
        return False
        
    def download_music(self, audio_url, output_path, max_retries=5):
        """
        Download the generated music to a local file with retry mechanism.
        
        Args:
            audio_url: URL to the generated audio
            output_path: Path where to save the downloaded file
            max_retries: Maximum number of retry attempts
            
        Returns:
            bool: True if download was successful, False otherwise
        """
        retry_count = 0
        while retry_count < max_retries:
            try:
                print(f"Download attempt {retry_count + 1}/{max_retries} from {audio_url}")
                
                # Try with streaming (better for large files)
                with requests.get(audio_url, stream=True, timeout=60) as response:
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
    
    def monitor_and_download(self, task_id, output_path, max_checks=30, check_interval=10, generate_mp4=False, mp4_output_path=None):
        """
        Monitor a task until completion and download the result.
        
        Args:
            task_id: Task ID to monitor
            output_path: Where to save the downloaded file
            max_checks: Maximum number of status checks
            check_interval: Seconds between checks
            generate_mp4: Whether to generate an MP4 video after audio generation
            mp4_output_path: Path to save the MP4 file (defaults to output_path with .mp4 extension)
            
        Returns:
            bool: True if download was successful, False otherwise
        """
        print(f"Monitoring task ID: {task_id}")
        print(f"Will save to: {output_path}")
        
        # Save task ID to a file for later use if needed
        with open('last_task_id.txt', 'w') as f:
            f.write(task_id)
        print(f"Task ID saved to last_task_id.txt")
        
        checks = 0
        while checks < max_checks:
            print(f"\nCheck {checks + 1}/{max_checks}...")
            
            task_details = self.check_generation_status(task_id)
            if not task_details:
                print("Could not retrieve task details, waiting before retry...")
                time.sleep(check_interval)
                checks += 1
                continue
            
            # Check if we have an error in the API response
            api_code = task_details.get('code')
            if api_code and api_code != 200:
                error_msg = task_details.get('msg', 'Unknown error')
                print(f"API error: {api_code} - {error_msg}")
                
                if api_code == 429:
                    print("Insufficient credits. Please add more credits to your account.")
                elif api_code == 455:
                    print("System is under maintenance. Please try again later.")
                
                # For most errors, we should stop polling
                if api_code not in [200, 404]:  # 404 might be temporary
                    return False
            
            # For proper error handling, first check the data object
            data = task_details.get('data', {})
            
            # Try to extract status using the documented path
            status = None
            if isinstance(data, dict):
                status = data.get('status')
            
            # If status is not in data, try alternative paths
            if not status:
                status = task_details.get('status')
                
                if not status:
                    # Search recursively if needed
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
            
            status_desc = self.get_status_description(status)
            print(f"Current status: {status} - {status_desc}")
            
            # When debugging, show the full response
            if self.debug:
                print("Full API response:")
                print(json.dumps(task_details, indent=2))
        
            # Check for completion based on documented status codes
            if status == 'SUCCESS' or status == 'FIRST_SUCCESS':
                print("Task is complete!")
                
                # Find audio URL and audio ID
                audio_url = self.find_audio_url(task_details)
                audio_id = self.find_audio_id(task_details)
                
                if audio_url:
                    print(f"Found audio URL: {audio_url}")
                    success = self.download_music(audio_url, output_path)
                    
                    # If MP4 generation is requested and we have an audio ID
                    if generate_mp4 and audio_id and success:
                        # Default MP4 output path if not specified
                        if not mp4_output_path:
                            mp4_output_path = os.path.splitext(output_path)[0] + ".mp4"
                        
                        print(f"\nGenerating MP4 video for the audio...")
                        try:
                            mp4_response = self.generate_mp4(task_id, audio_id, mp4_output_path)
                            
                            # Make sure mp4_response is not None before accessing it
                            if mp4_response is None:
                                print("Failed to start MP4 generation: No response from API")
                            elif mp4_response.get('success', False):
                                print(f"MP4 generation started. You can check its status with the task ID.")
                                mp4_task_id = mp4_response.get('data', {}).get('taskId')
                                if mp4_task_id:
                                    with open('last_mp4_task_id.txt', 'w') as f:
                                        f.write(mp4_task_id)
                                    print(f"MP4 task ID saved to last_mp4_task_id.txt")
                                    # Optionally monitor the MP4 generation immediately
                                    if not mp4_output_path:
                                        mp4_output_path = os.path.splitext(output_path)[0] + ".mp4"
                                    print(f"\nMonitoring MP4 generation...")
                                    self.monitor_and_download_mp4(mp4_task_id, mp4_output_path, max_checks, check_interval)
                                else:
                                    print("No MP4 task ID returned. Cannot monitor the MP4 generation.")
                            else:
                                # Handle case where mp4_response exists but success is False
                                error_msg = mp4_response.get('error', 'Unknown error')
                                error_code = mp4_response.get('error_code', 'Unknown error code')
                                print(f"Failed to start MP4 generation: {error_msg} (Code: {error_code})")
                        except Exception as e:
                            print(f"Error during MP4 generation process: {e}")
                            print("MP4 generation may have started but cannot be monitored automatically.")
                    
                    return success
                else:
                    print("No audio URL found in the response.")
                    return False
        
            elif status in ['CREATE_TASK_FAILED', 'GENERATE_AUDIO_FAILED', 'CALLBACK_EXCEPTION', 'SENSITIVE_WORD_ERROR']:
                print(f"Task failed: {status_desc}")
                return False
        
            elif status in ['PENDING', 'TEXT_SUCCESS']:
                print(f"Task still processing ({status_desc}). Checking again in {check_interval} seconds...")
        
            checks += 1
            time.sleep(check_interval)
        
        print("Exceeded maximum checks. Task may still be processing.")
        print(f"You can check again later using: python main.py --check-task {task_id} --output {output_path}")
        return False


def main():
    """Main function to orchestrate lyrics and music generation."""
    parser = argparse.ArgumentParser(description='Generate lyrics and music')
    parser.add_argument('--theme', type=str, help='Theme or idea for the song')
    parser.add_argument('--style', type=str, default='pop', help='Music style (e.g., rock, pop, rap)')
    parser.add_argument('--verses', type=int, default=2, help='Number of verses')
    parser.add_argument('--chorus', action='store_true', help='Include a chorus')
    parser.add_argument('--custom', action='store_true', default=True, help='Use custom mode for Suno API')
    parser.add_argument('--instrumental', action='store_true', help='Generate instrumental music (no lyrics)')
    parser.add_argument('--model', type=str, default='V3_5', choices=['V3_5', 'V4'], help='Suno API model to use')
    parser.add_argument('--output', type=str, default='output.mp3', help='Output file path')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--checks', type=int, default=30, help='Maximum number of status checks')
    parser.add_argument('--interval', type=int, default=10, help='Seconds between status checks')
    parser.add_argument('--check-task', type=str, nargs='?', const=True, help='Check status of an existing task ID and download the result')
    parser.add_argument('--generate-mp4', action='store_true', help='Generate MP4 video for the audio')
    parser.add_argument('--mp4-output', type=str, help='Output file path for MP4 (defaults to audio path with .mp4 extension)')
    parser.add_argument('--check-mp4-task', type=str, nargs='?', const=True, help='Check status of an existing MP4 task ID and download the result')
    
    args = parser.parse_args()
    
    # Check for API keys first
    if not os.getenv("SUNO_API_KEY"):
        print("ERROR: SUNO_API_KEY environment variable is not set.")
        print("Please add your Suno API key to the .env file.")
        return
    
    if not args.instrumental and not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable is not set.")
        print("Please add your Anthropic API key to the .env file or use --instrumental flag.")
        return
    
    # Create music generator instance
    music_gen = MusicGenerator(debug=args.debug)
    
    # If checking an existing MP4 task
    if args.check_mp4_task:
        mp4_task_id = args.check_mp4_task
        
        # If no MP4 task ID provided but --check-mp4-task flag is used, try to read from file
        if mp4_task_id == True:
            try:
                with open('last_mp4_task_id.txt', 'r') as f:
                    mp4_task_id = f.read().strip()
                print(f"Using MP4 task ID from last_mp4_task_id.txt: {mp4_task_id}")
            except FileNotFoundError:
                print("No MP4 task ID provided and no last_mp4_task_id.txt file found.")
                return
        
        mp4_output = args.mp4_output or "output.mp4"
        print(f"Checking existing MP4 task: {mp4_task_id}")
        music_gen.monitor_and_download_mp4(mp4_task_id, mp4_output, args.checks, args.interval)
        return
    
    # If checking an existing audio task
    if args.check_task:
        task_id = args.check_task
        
        # If no task ID provided but --check-task flag is used, try to read from file
        if task_id == True:
            try:
                with open('last_task_id.txt', 'r') as f:
                    task_id = f.read().strip()
                print(f"Using task ID from last_task_id.txt: {task_id}")
            except FileNotFoundError:
                print("No task ID provided and no last_task_id.txt file found.")
                return
        
        print(f"Checking existing task: {task_id}")
        music_gen.monitor_and_download(task_id, args.output, args.checks, args.interval, generate_mp4=args.generate_mp4, mp4_output_path=args.mp4_output)
        return
    
    # Ensure theme is provided for new music generation
    if not args.theme:
        print("Please provide a theme with --theme")
        return
    
    # Generate lyrics using Anthropic (skip if instrumental is requested)
    lyrics_content = ""
    lyrics_title = ""
    
    if not args.instrumental:
        print(f"Generating lyrics about '{args.theme}' in {args.style} style...")
        lyrics_gen = LyricsGenerator()
        lyrics_result = lyrics_gen.generate_lyrics(
            args.theme, 
            style=args.style,
            num_verses=args.verses,
            has_chorus=args.chorus
        )
        
        lyrics_title = lyrics_result['title']
        lyrics_content = lyrics_result['content']
        
        print(f"\nGenerated title: {lyrics_title}")
        print("Generated lyrics:")
        print("-" * 40)
        print(lyrics_content)
        print("-" * 40)
    else:
        # If instrumental, just use the theme as prompt
        lyrics_content = args.theme
        lyrics_title = args.theme.capitalize()
        print(f"Creating instrumental music with theme: {args.theme}")
    
    # Generate music using Suno API
    print("\nGenerating music with Suno API...")
    generation_response = music_gen.generate_music(
        lyrics_title,
        lyrics_content,
        args.style,
        custom_mode=args.custom,
        instrumental=args.instrumental,
        model=args.model
    )
    
    if not generation_response:
        print("Failed to start music generation. Please check the error messages above.")
        return
    
    if args.debug:
        print("Full API response:")
        print(json.dumps(generation_response, indent=2))
    
    # Check for the task ID in the response
    task_id = None
    try:
        task_id = generation_response.get('data', {}).get('taskId')
        if not task_id:
            # Try alternative paths for task ID
            task_id = generation_response.get('taskId')
            
            if not task_id:
                # Search for taskId recursively
                def find_task_id(obj):
                    if isinstance(obj, dict):
                        if 'taskId' in obj:
                            return obj['taskId']
                        for k, v in obj.items():
                            result = find_task_id(v)
                            if result:
                                return result
                    elif isinstance(obj, list):
                        for item in obj:
                            result = find_task_id(item)
                            if result:
                                return result
                    return None
                
                task_id = find_task_id(generation_response)
    except (KeyError, TypeError, AttributeError) as e:
        print(f"Error extracting task ID: {e}")
        print("API Response structure:")
        print(json.dumps(generation_response, indent=2))
        return
    
    if not task_id:
        print("No task ID returned from Suno API.")
        print("API Response structure:")
        print(json.dumps(generation_response, indent=2))
        return
    
    print(f"Music generation started with task ID: {task_id}")
    
    # Monitor the task until completion and download
    music_gen.monitor_and_download(task_id, args.output, args.checks, args.interval, generate_mp4=args.generate_mp4, mp4_output_path=args.mp4_output)


if __name__ == "__main__":
    main()
