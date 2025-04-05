# Lyrics and Music Generator

This Python application uses Anthropic's Claude model to generate song lyrics and the Suno API to generate music from those lyrics. It also supports instrumental music generation and MP4 video creation.

## Features

- Generate creative song lyrics based on a theme or idea using Claude AI
- Customize lyrics with different music styles, number of verses, and chorus options
- Generate instrumental or vocal tracks based on your preferences
- Choose between Suno V3.5 or V4 models for music generation
- Download the generated music as an MP3 file
- Generate MP4 video visualizations for your music
- Robust error handling and status checking
- Resume incomplete downloads or check on previous tasks

## Requirements

- Python 3.7+
- Anthropic API key
- Suno API key
- Virtual environment (recommended)

## Installation

1. Clone this repository and set up a virtual environment:
   ```bash
   git clone <repository-url>
   cd suno-322
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root with your API keys:
   ```
   SUNO_API_KEY=your_suno_api_key
   ANTHROPIC_API_KEY=your_anthropic_api_key
   ```

## Usage

### Recommended Command Format

The following command format has been tested and works reliably:

```bash
./venv/bin/python main.py --theme "your theme here" --style "music style" --instrumental --model "V4" --generate-mp4
```

Example:
```bash
./venv/bin/python main.py --theme "fairies dancing in the rain" --style "indie" --instrumental --model "V4" --generate-mp4
```

### Generate a Song with Lyrics

To generate a song with lyrics (using Claude for lyrics generation):

```bash
./venv/bin/python main.py --theme "sunset at the beach" --style "lofi" --verses 2 --chorus --output "beach_sunset.mp3"
```

### Generate Instrumental Music Only

To generate instrumental music without lyrics:

```bash
./venv/bin/python main.py --theme "midnight forest" --style "ambient" --instrumental --output "forest.mp3"
```

### Generate Music with MP4 Video

To generate music and create an MP4 video visualization:

```bash
./venv/bin/python main.py --theme "space journey" --style "electronic" --instrumental --model "V4" --generate-mp4
```

### Check on a Previous Task

If your generation process was interrupted, you can resume it:

```bash
./venv/bin/python main.py --check-task
```

This will automatically find the last task ID from the saved file and continue monitoring it.

You can also specify a specific task ID:

```bash
./venv/bin/python main.py --check-task "your-task-id" --output "my_song.mp3"
```

## Command-line Arguments

- `--theme`: The main theme or idea for your song
- `--style` (default: "pop"): The music style (e.g., rock, pop, jazz, indie)
- `--verses` (default: 2): Number of verses to generate
- `--chorus`: Include this flag to add a chorus to the lyrics
- `--custom` (default: true): Use Suno API's custom mode for more control over generation
- `--instrumental`: Generate instrumental music (no lyrics)
- `--model` (default: "V3_5"): Suno API model to use (V3_5 or V4)
- `--output` (default: "output.mp3"): Path where to save the generated music
- `--debug`: Show detailed API response information
- `--check-task`: Check status of an existing task ID and download the result
- `--interval` (default: 10): Seconds between status checks
- `--checks` (default: 30): Maximum number of status checks
- `--generate-mp4`: Generate an MP4 video for the audio
- `--mp4-output`: Output file path for MP4 (defaults to audio path with .mp4 extension)
- `--check-mp4-task`: Check status of an existing MP4 task ID and download the result

## Utility Scripts

### Check Status Script

Check on existing task status:

```bash
./venv/bin/python check_status.py --task-id "your-task-id" --output "my_song.mp3" --debug
```

### Download Song Script

For a more robust downloading experience:

```bash
./venv/bin/python download_song.py --task-id "your-task-id" --output "my_song.mp3" --max-checks 60
```

### Test API Connectivity

Test your API connectivity with:

```bash
./venv/bin/python test_api.py
```

## Troubleshooting

### MP4 Generation Issues

If you encounter issues with MP4 generation through the Suno API (error code 400 with "Record not generated successfully"), this may be due to:

1. API limitations or permissions with your current API key
2. The MP4 generation service being temporarily unavailable
3. Specific requirements for MP4 generation that aren't being met

The script will still successfully generate and download the MP3 audio file even if MP4 generation fails.

### API Authentication

If you receive authentication errors (401), check that:
1. Your API keys in the `.env` file are correct
2. The API keys have the necessary permissions
3. Your account has sufficient credits for generation

## Notes

- The Suno API may take several minutes to generate music, especially with the V4 model
- MP4 generation is an additional step after audio generation and may not always succeed
- Using the virtual environment's Python interpreter directly (`./venv/bin/python`) ensures all dependencies are available
