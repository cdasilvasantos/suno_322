#!/usr/bin/env python3
"""
Generate MP4 video from audio file with visualizations.
This script creates a video visualization for audio files when the Suno API MP4 generation fails.
"""
import os
import sys
import argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import moviepy.editor as mp
from pydub import AudioSegment
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

def create_waveform_video(audio_path, output_path, title=None, style=None, fps=30):
    """
    Create a video with audio waveform visualization.
    
    Args:
        audio_path: Path to the audio file
        output_path: Path where to save the MP4 file
        title: Optional title to display in the video
        style: Optional style description to display
        fps: Frames per second for the video
    
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"Generating MP4 video for {audio_path}...")
    
    try:
        # Load audio file
        audio = AudioSegment.from_file(audio_path)
        audio_array = np.array(audio.get_array_of_samples())
        
        # If stereo, take average of channels
        if audio.channels == 2:
            audio_array = audio_array.reshape((-1, 2))
            audio_array = audio_array.mean(axis=1)
        
        # Get audio duration and calculate number of frames
        duration = audio.duration_seconds
        n_frames = int(duration * fps)
        
        # Video dimensions
        width, height = 1280, 720
        
        # Create a figure for the visualization
        fig, ax = plt.figure(figsize=(width/100, height/100), dpi=100), plt.axes()
        fig.patch.set_facecolor('#000000')  # Black background
        
        # Set up the plot
        ax.set_facecolor('#000000')  # Black background
        ax.set_xlim(0, 1)
        ax.set_ylim(-1.2, 1.2)
        ax.axis('off')  # Hide axes
        
        # Add title if provided
        if title:
            display_title = title
            if style:
                display_title += f" ({style} style)"
            ax.set_title(display_title, color='white', fontsize=24, pad=20)
        
        # Create line objects for the waveform
        line, = ax.plot([], [], lw=2, color='#3498db')  # Blue line
        
        # Function to initialize the animation
        def init():
            line.set_data([], [])
            return line,
        
        # Function to update the animation for each frame
        def animate(i):
            # Calculate the segment of audio to display
            segment_size = len(audio_array) // n_frames
            start_idx = i * segment_size
            end_idx = min(start_idx + segment_size * 20, len(audio_array))  # Show a window of audio
            
            # Create x and y data for the current frame
            x = np.linspace(0, 1, end_idx - start_idx)
            y = audio_array[start_idx:end_idx] / 32768.0  # Normalize to [-1, 1]
            
            line.set_data(x, y)
            return line,
        
        # Create the animation
        print("Creating animation frames...")
        anim = FuncAnimation(fig, animate, init_func=init, frames=n_frames, 
                             interval=1000/fps, blit=True)
        
        # Save as temporary file
        temp_video = 'temp_video.mp4'
        print(f"Saving animation to temporary file: {temp_video}")
        anim.save(temp_video, fps=fps, extra_args=['-vcodec', 'libx264', '-pix_fmt', 'yuv420p'])
        
        # Add audio to the video
        print("Adding audio to video...")
        video = mp.VideoFileClip(temp_video)
        audio_clip = mp.AudioFileClip(audio_path)
        final_clip = video.set_audio(audio_clip)
        
        # Write the final video
        print(f"Writing final video to: {output_path}")
        final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
        
        # Clean up temporary files
        video.close()
        audio_clip.close()
        final_clip.close()
        if os.path.exists(temp_video):
            os.remove(temp_video)
            
        print(f"MP4 generation complete! File saved to: {output_path}")
        return True
        
    except Exception as e:
        print(f"Error generating MP4: {e}")
        return False

def create_spectrum_video(audio_path, output_path, title=None, style=None, fps=30):
    """
    Create a video with audio spectrum visualization.
    
    Args:
        audio_path: Path to the audio file
        output_path: Path where to save the MP4 file
        title: Optional title to display in the video
        style: Optional style description to display
        fps: Frames per second for the video
    
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"Generating spectrum MP4 video for {audio_path}...")
    
    try:
        # Load audio file
        audio = AudioSegment.from_file(audio_path)
        audio_array = np.array(audio.get_array_of_samples())
        
        # If stereo, take average of channels
        if audio.channels == 2:
            audio_array = audio_array.reshape((-1, 2))
            audio_array = audio_array.mean(axis=1)
        
        # Get audio duration and calculate number of frames
        duration = audio.duration_seconds
        n_frames = int(duration * fps)
        
        # Video dimensions
        width, height = 1280, 720
        
        # Create a figure for the visualization
        fig, ax = plt.figure(figsize=(width/100, height/100), dpi=100), plt.axes()
        fig.patch.set_facecolor('#000000')  # Black background
        
        # Set up the plot
        ax.set_facecolor('#000000')  # Black background
        ax.axis('off')  # Hide axes
        
        # Add title if provided
        if title:
            display_title = title
            if style:
                display_title += f" ({style} style)"
            ax.set_title(display_title, color='white', fontsize=24, pad=20)
        
        # Function to calculate FFT for a segment of audio
        def get_fft(segment):
            fft = np.abs(np.fft.rfft(segment))
            # Apply logarithmic scaling for better visualization
            fft = np.log10(fft + 1)
            return fft
        
        # Number of frequency bins to display
        n_bins = 100
        
        # Create bar objects for the spectrum
        x = np.arange(n_bins)
        bars = ax.bar(x, np.zeros(n_bins), color='#3498db', alpha=0.7)
        
        # Set up the plot limits
        ax.set_xlim(-1, n_bins)
        ax.set_ylim(0, 5)  # Adjust based on your audio levels
        
        # Function to initialize the animation
        def init():
            for bar in bars:
                bar.set_height(0)
            return bars
        
        # Function to update the animation for each frame
        def animate(i):
            # Calculate the segment of audio to analyze
            segment_size = len(audio_array) // n_frames
            start_idx = i * segment_size
            end_idx = min(start_idx + segment_size * 2, len(audio_array))
            
            # Get FFT for the current segment
            fft = get_fft(audio_array[start_idx:end_idx])
            
            # Resize to n_bins
            if len(fft) > n_bins:
                # Take a subset of frequencies (focus on lower frequencies)
                fft = fft[:n_bins]
            else:
                # Pad with zeros if needed
                fft = np.pad(fft, (0, n_bins - len(fft)))
            
            # Update bar heights
            for bar, h in zip(bars, fft):
                bar.set_height(h)
                
                # Change color based on height for visual effect
                if h > 3:
                    bar.set_color('#e74c3c')  # Red for high frequencies
                elif h > 2:
                    bar.set_color('#f39c12')  # Orange for medium frequencies
                else:
                    bar.set_color('#3498db')  # Blue for low frequencies
            
            return bars
        
        # Create the animation
        print("Creating animation frames...")
        anim = FuncAnimation(fig, animate, init_func=init, frames=n_frames, 
                             interval=1000/fps, blit=True)
        
        # Save as temporary file
        temp_video = 'temp_video.mp4'
        print(f"Saving animation to temporary file: {temp_video}")
        anim.save(temp_video, fps=fps, extra_args=['-vcodec', 'libx264', '-pix_fmt', 'yuv420p'])
        
        # Add audio to the video
        print("Adding audio to video...")
        video = mp.VideoFileClip(temp_video)
        audio_clip = mp.AudioFileClip(audio_path)
        final_clip = video.set_audio(audio_clip)
        
        # Write the final video
        print(f"Writing final video to: {output_path}")
        final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
        
        # Clean up temporary files
        video.close()
        audio_clip.close()
        final_clip.close()
        if os.path.exists(temp_video):
            os.remove(temp_video)
            
        print(f"MP4 generation complete! File saved to: {output_path}")
        return True
        
    except Exception as e:
        print(f"Error generating MP4: {e}")
        return False

def main():
    """Main function to parse arguments and generate MP4."""
    parser = argparse.ArgumentParser(description='Generate MP4 video from audio file')
    parser.add_argument('--audio', type=str, required=True, help='Path to audio file')
    parser.add_argument('--output', type=str, help='Output MP4 file path')
    parser.add_argument('--title', type=str, help='Title to display in the video')
    parser.add_argument('--style', type=str, help='Style description to display')
    parser.add_argument('--type', type=str, default='spectrum', choices=['waveform', 'spectrum'], 
                        help='Type of visualization')
    parser.add_argument('--fps', type=int, default=30, help='Frames per second')
    
    args = parser.parse_args()
    
    # Default output path if not specified
    if not args.output:
        base_name = os.path.splitext(args.audio)[0]
        args.output = f"{base_name}.mp4"
    
    # Generate the appropriate visualization
    if args.type == 'waveform':
        success = create_waveform_video(args.audio, args.output, args.title, args.style, args.fps)
    else:  # spectrum
        success = create_spectrum_video(args.audio, args.output, args.title, args.style, args.fps)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
