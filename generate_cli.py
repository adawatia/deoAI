import os
import shutil
import time # For basic timing/progress
from datetime import datetime # To create unique filenames

# Import your custom modules
from script_processor import ScriptProcessor
from voiceover_generator import VoiceoverGenerator
from visual_generator import VisualGenerator
from video_assembler import VideoAssembler

# --- Configuration ---
# Output directories for generated assets
GENERATED_AUDIO_DIR = "generated_audio"
GENERATED_IMAGES_DIR = "generated_images"
FINAL_VIDEOS_DIR = "final_videos"
TEMP_DIR = "temp_assets" # For temporary files during processing, if needed

# Ensure output directories exist
os.makedirs(GENERATED_AUDIO_DIR, exist_ok=True)
os.makedirs(GENERATED_IMAGES_DIR, exist_ok=True)
os.makedirs(FINAL_VIDEOS_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True) # Create temp dir


# --- Main Application Logic ---
class FacelessVideoApp:
    def __init__(self):
        print("Initializing Faceless Video App components...")
        self.script_processor = ScriptProcessor()
        self.voiceover_generator = VoiceoverGenerator(output_dir=GENERATED_AUDIO_DIR)
        self.visual_generator = VisualGenerator(output_dir=GENERATED_IMAGES_DIR)
        self.video_assembler = VideoAssembler(output_dir=FINAL_VIDEOS_DIR)
        print("Components initialized.")

    def generate_video_from_script(self, raw_script: str, background_music_path: str = None):
        """
        Orchestrates the entire video generation process from a raw script.
        """
        print("\n--- Starting Video Generation Process ---")
        start_time = time.time()

        # 1. Process the script into scenes
        print("1. Processing script into scenes...")
        processed_scenes = self.script_processor.process_script(raw_script)
        if not processed_scenes:
            print("No scenes processed. Aborting video generation.")
            return None
        print(f"Script processed into {len(processed_scenes)} scenes.")

        scene_assets = [] # To store paths of generated audio and images for each scene

        # 2. Generate voiceovers and visuals for each scene
        print("2. Generating voiceovers and visuals for each scene...")
        for i, scene_text in enumerate(processed_scenes):
            print(f"\n  -- Processing Scene {i+1}/{len(processed_scenes)} --")
            scene_start_time = time.time()

            # Generate Voiceover
            audio_path = self.voiceover_generator.generate_voiceover_for_scene(scene_text, i)
            if not audio_path:
                print(f"  Warning: Voiceover failed for scene {i+1}. Using fallback/silent audio.")
                # You might want to create a silent audio here as a fallback if not already handled
                # by voiceover_generator. This is crucial for MoviePy not to crash.
                from pydub import AudioSegment
                silent_audio = AudioSegment.silent(duration=2000) # Default silent duration
                fallback_audio_path = os.path.join(TEMP_DIR, f"silent_fallback_{i}.wav")
                silent_audio.export(fallback_audio_path, format="wav")
                audio_path = fallback_audio_path
            print(f"  Voiceover for scene {i+1} saved to: {audio_path}")

            # Generate Visual
            image_path = self.visual_generator.generate_visual_for_scene(scene_text, i)
            if not image_path:
                print(f"  Warning: Visual generation failed for scene {i+1}. Using a black placeholder image.")
                # Create a black placeholder image if visual generation fails
                from PIL import Image
                from pydub import AudioSegment # To get audio duration for image placeholder
                
                # Get audio duration to make image placeholder match
                audio_for_duration = AudioSegment.from_wav(audio_path)
                placeholder_duration_ms = audio_for_duration.duration_seconds * 1000

                placeholder_image = Image.new('RGB', (1920, 1080), color = 'black') # Standard HD resolution
                fallback_image_path = os.path.join(TEMP_DIR, f"black_placeholder_{i}.png")
                placeholder_image.save(fallback_image_path)
                image_path = fallback_image_path
            print(f"  Visual for scene {i+1} saved to: {image_path}")

            scene_assets.append({
                "image_path": image_path,
                "audio_path": audio_path
            })
            print(f"  Scene {i+1} processing finished in {time.time() - scene_start_time:.2f} seconds.")

        # 3. Assemble the final video
        print("\n3. Assembling the final video...")
        # Generate a unique filename for the output video
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_video_filename = f"faceless_video_{timestamp}.mp4"

        final_video_path = self.video_assembler.assemble_video(
            scene_assets,
            background_music_path=background_music_path,
            output_filename=output_video_filename
        )

        if final_video_path:
            print(f"\n--- Video Generation Complete! ---")
            print(f"Final video saved to: {os.path.abspath(final_video_path)}")
        else:
            print("\n--- Video Generation Failed ---")

        end_time = time.time()
        print(f"Total processing time: {end_time - start_time:.2f} seconds.")

        # Optional: Clean up temporary files (uncomment if you want to remove temp_assets)
        # print("Cleaning up temporary assets...")
        # shutil.rmtree(TEMP_DIR)
        # print("Temporary assets removed.")

        return final_video_path

# --- Main Execution Block ---
if __name__ == "__main__":
    app = FacelessVideoApp()

    # Define a sample script
    sample_script = """
    Scene 1: Introduction.
    The sun rises over a serene, misty lake, casting golden hues across the water. A lone fishing boat glides gently.

    Scene 2: Problem.
    Suddenly, dark clouds gather, and a fierce storm begins. Waves crash violently against the boat, threatening to capsize it.

    Scene 3: Solution.
    A lighthouse beam cuts through the gloom, guiding the struggling vessel to safety. The storm slowly dissipates.

    Scene 4: Conclusion.
    The boat reaches the shore as the sun breaks through the clouds, symbolizing hope and resilience.
    """

    # Optional: Path to a background music file.
    # Make sure you have an MP3 file, e.g., 'background_music.mp3' in your project root.
    # You can download royalty-free music for testing.
    # Example: Create a dummy one for initial testing if you don't have.
    # from pydub import AudioSegment
    # if not os.path.exists("sample_background_music.mp3"):
    #     AudioSegment.silent(duration=30000).export("sample_background_music.mp3", format="mp3")
    background_music_file = None # Set to "sample_background_music.mp3" if you generate one

    # Check if generators are available before attempting to run
    if (app.voiceover_generator.get_chatterbox_availability() and
            app.visual_generator.get_visual_generator_availability()):
        print("\nAll generators available. Running video generation...")
        final_video = app.generate_video_from_script(sample_script, background_music_path=background_music_file)
        if final_video:
            print(f"\nFinal video available at: {final_video}")
            print("\nRemember to check the 'generated_audio', 'generated_images', and 'final_videos' folders.")
    else:
        print("\nSome generators are not available. Please check the logs above for missing libraries or model issues.")
        print("Ensure 'chatterbox-tts', 'torchaudio', 'diffusers', 'transformers', 'accelerate', 'moviepy',")
        print("and their dependencies (including PyTorch/CUDA/FFmpeg) are correctly installed.")

