import os
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip, ColorClip

class VideoAssembler:
    def __init__(self, output_dir="final_videos"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def assemble_video(self, scene_data: list, background_music_path: str = None, output_filename="final_video.mp4"):
        """
        Assembles a video from a list of scene data (image paths and audio paths).

        Args:
            scene_data (list): A list of dictionaries, where each dict contains
                               'image_path' and 'audio_path' for a scene.
            background_music_path (str, optional): Path to a background music file. Defaults to None.
            output_filename (str, optional): Name of the final output video file. Defaults to "final_video.mp4".
        """
        video_clips = []
        total_audio_duration = 0

        for i, scene in enumerate(scene_data):
            image_path = scene.get("image_path")
            audio_path = scene.get("audio_path")

            if not image_path or not os.path.exists(image_path):
                print(f"Warning: Image not found for scene {i}. Skipping or using placeholder.")
                # You might want a default image or black screen here
                # For simplicity, if image is missing, we'll create a black clip
                # You'd need to know the desired resolution if using ColorClip
                img_clip = ColorClip(size=(1920, 1080), color=(0,0,0)) # Example resolution
            else:
                img_clip = ImageClip(image_path)

            if not audio_path or not os.path.exists(audio_path):
                print(f"Warning: Audio not found for scene {i}. Using silent audio.")
                audio_clip = AudioFileClip(os.path.join(os.path.dirname(__file__), "silent.wav")) # Create a silent.wav file for this.
                # For robust silent audio:
                # from pydub import AudioSegment
                # silent_audio = AudioSegment.silent(duration=2000) # 2 seconds
                # silent_audio.export("temp_silent.wav", format="wav")
                # audio_clip = AudioFileClip("temp_silent.wav")
            else:
                audio_clip = AudioFileClip(audio_path)

            # Set the duration of the image clip to match the audio clip
            img_clip = img_clip.set_duration(audio_clip.duration)
            img_clip = img_clip.set_audio(audio_clip)

            video_clips.append(img_clip)
            total_audio_duration += audio_clip.duration

        if not video_clips:
            print("No valid scene clips to assemble. Exiting.")
            return None

        # Concatenate all scene clips
        final_video_clip = concatenate_videoclips(video_clips)

        # Add background music if provided
        if background_music_path and os.path.exists(background_music_path):
            try:
                bg_music = AudioFileClip(background_music_path)
                # Loop background music if it's shorter than the video
                if bg_music.duration < final_video_clip.duration:
                    bg_music = bg_music.fx(lambda clip: clip.loop(duration=final_video_clip.duration))
                else:
                    bg_music = bg_music.subclip(0, final_video_clip.duration)

                # Adjust volume of background music (e.g., 0.2 for quiet background)
                bg_music = bg_music.volumex(0.2)

                # Mix voiceover and background music
                final_audio = CompositeAudioClip([final_video_clip.audio, bg_music])
                final_video_clip = final_video_clip.set_audio(final_audio)
                print("Background music added to the video.")
            except Exception as e:
                print(f"Error adding background music: {e}. Proceeding without background music.")


        output_filepath = os.path.join(self.output_dir, output_filename)
        print(f"Writing final video to: {output_filepath}")

        # Write the final video file
        # 'codec' and 'fps' might need adjustment based on desired quality/file size
        # 'fps' can be low for static images, but needs to be sufficient for smooth video.
        # For images, 1 or 2 FPS might be sufficient if you just want to display the image.
        # If you have subtle animations, higher FPS (e.g., 24 or 30) is better.
        final_video_clip.write_videofile(output_filepath, codec="libx264", fps=24) # Using 24 FPS for smoother output.

        print("Video assembly complete.")
        return output_filepath

# Example of how to use (for testing this module independently)
if __name__ == "__main__":
    # Create dummy image and audio files for testing
    # You would replace this with actual generated files
    dummy_image_dir = "test_images"
    dummy_audio_dir = "test_audio"
    os.makedirs(dummy_image_dir, exist_ok=True)
    os.makedirs(dummy_audio_dir, exist_ok=True)

    # Create dummy image
    from PIL import Image
    Image.new('RGB', (1920, 1080), color = 'red').save(os.path.join(dummy_image_dir, "scene_0.png"))
    Image.new('RGB', (1920, 1080), color = 'blue').save(os.path.join(dummy_image_dir, "scene_1.png"))

    # Create dummy silent audio
    from pydub import AudioSegment
    AudioSegment.silent(duration=5000).export(os.path.join(dummy_audio_dir, "scene_0.wav"), format="wav")
    AudioSegment.silent(duration=3000).export(os.path.join(dummy_audio_dir, "scene_1.wav"), format="wav")

    # Example background music (create a dummy one if you don't have)
    # bg_music_path = "path/to/your/background_music.mp3"
    # For testing, we can create a short silent background music
    AudioSegment.silent(duration=10000).export("dummy_bg_music.mp3", format="mp3")
    bg_music_path = "dummy_bg_music.mp3"


    scene_data_for_assembly = [
        {"image_path": os.path.join(dummy_image_dir, "scene_0.png"), "audio_path": os.path.join(dummy_audio_dir, "scene_0.wav")},
        {"image_path": os.path.join(dummy_image_dir, "scene_1.png"), "audio_path": os.path.join(dummy_audio_dir, "scene_1.wav")},
    ]

    va = VideoAssembler()
    final_video_path = va.assemble_video(scene_data_for_assembly, background_music_path=bg_music_path, output_filename="my_faceless_video.mp4")
    print(f"Final video should be at: {final_video_path}")

    # Clean up dummy files
    # import shutil
    # shutil.rmtree(dummy_image_dir)
    # shutil.rmtree(dummy_audio_dir)
    # os.remove("dummy_bg_music.mp3")