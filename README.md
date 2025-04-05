# Lyrics and Music Generator

This Python script uses Anthropic's Claude model to generate song lyrics and then uses the Suno API to generate music from those lyrics.

## Features

- Generate creative song lyrics based on a theme or idea
- Customize lyrics with different music styles, number of verses, and chorus options
- Generate instrumental or vocal tracks based on your preferences
- Choose between Suno V3.5 or V4 models
- Download the generated music as an audio file
- Robust error handling and status checking
- Ability to resume incomplete downloads or check on previous tasks

## Requirements

- Python 3.7+
- Anthropic API key
- Suno API key

## Installation

1. Make sure your `.env` file contains the required API keys:
   ```
   SUNO_API_KEY=your_suno_api_key
   ANTHROPIC_API_KEY=your_anthropic_api_key
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Generate a New Song

Run the script with the following command:

```bash
python main.py --theme "love and heartbreak" --style "indie rock" --verses 2 --chorus --output "my_song.mp3"
```

### Check on a Previous Task

If your generation process was interrupted, you can resume it:

```bash
python main.py --check-task
```

This will automatically find the last task ID from the saved file and continue monitoring it.

You can also specify a specific task ID:

```bash
python main.py --check-task "your-task-id" --output "my_song.mp3"
```

### Command-line Arguments

- `--theme`: The main theme or idea for your song
- `--style` (default: "pop"): The music style (e.g., rock, pop, rap, country)
- `--verses` (default: 2): Number of verses to generate
- `--chorus`: Include this flag to add a chorus to the lyrics
- `--custom` (default: true): Use Suno API's custom mode for more control over generation
- `--instrumental`: Generate instrumental music without lyrics
- `--model` (default: "V3_5"): Suno API model to use (V3_5 or V4)
- `--output` (default: "output.mp3"): Path where to save the generated music
- `--debug`: Show detailed API response information
- `--check-task`: Check status of an existing task ID and download the result
- `--interval` (default: 10): Seconds between status checks
- `--checks` (default: 30): Maximum number of status checks

## Utility Scripts

### Check Status Script

The repository includes a standalone utility to check on existing task status:

```bash
python check_status.py --task-id "your-task-id" --output "my_song.mp3" --debug
```

### Download Song Script

For a more robust downloading experience:

```bash
python download_song.py --task-id "your-task-id" --output "my_song.mp3" --max-checks 60
```

## API Diagnostics

Test API connectivity with:

```bash
python test_api.py
```

## Example Commands

### Generate a pop song about love
```bash
python main.py --theme "finding love in unexpected places" --style "pop" --chorus
```

### Create an instrumental jazz track
```bash
python main.py --theme "rainy day in the city" --style "jazz" --instrumental --model "V4"
```

### Generate a rock song with specific output location
```bash
python main.py --theme "overcoming challenges" --style "rock" --verses 3 --chorus --output "rock_anthem.mp3"
```

## How It Works

1. The script uses Anthropic's Claude model to generate song lyrics based on your theme and style preferences
2. It sends these lyrics to the Suno API for music generation using their V3.5 or V4 models
3. The script polls the Suno API to check when the music generation is complete
4. Once complete, it downloads the generated music to your specified output file

## Notes

- Music generation can take several minutes to complete
- The Suno API retains generated files for 15 days
- Custom mode in Suno API allows for more specific control over the music generation
- Different models (V3.5 vs V4) may produce different musical qualities
