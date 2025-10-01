import os
from moviepy.editor import (
    ImageClip, AudioFileClip, CompositeAudioClip,
    CompositeVideoClip, ColorClip
)
import numpy as np

class VideoAssembler:
    def __init__(self, output_dir="final_videos"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def _create_ken_burns_effect(self, clip, duration, zoom_factor=1.25):
        def effect(get_frame, t):
            frame = get_frame(t)
            img_h, img_w, _ = frame.shape
            zoom_progress = 1 + (zoom_factor - 1) * (t / duration)
            new_w, new_h = int(img_w / zoom_progress), int(img_h / zoom_progress)
            start_x, start_y = (img_w - new_w) // 2, (img_h - new_h) // 2
            cropped_frame = frame[start_y:start_y + new_h, start_x:start_x + new_w]
            from PIL import Image
            pil_img = Image.fromarray(cropped_frame)
            resized_img = pil_img.resize((img_w, img_h), Image.Resampling.LANCZOS)
            return np.array(resized_img)
        return clip.fl(effect)

    def assemble_video(self, scene_data: list, background_music_path: str = None, 
                       output_filename="final_video.mp4", dimensions=(1920, 1080)):
        if not scene_data: return None
        width, height = dimensions
        transition_duration = 1
        clips_with_effects = []

        for i, scene in enumerate(scene_data):
            image_path = scene.get("image_path")
            audio_path = scene.get("audio_path")

            if not image_path or not os.path.exists(image_path):
                print(f"Image not found for scene {i+1}. Using black screen.")
                img_clip = ColorClip(size=(width, height), color=(0,0,0))
            else:
                img_clip = ImageClip(image_path)
            
            if not audio_path or not os.path.exists(audio_path):
                print(f"Audio not found for scene {i+1}. Using 5s silence.")
                from moviepy.editor import AudioArrayClip
                audio_clip = AudioArrayClip(np.zeros((1, 2)), fps=44100).set_duration(5)
            else:
                audio_clip = AudioFileClip(audio_path)
            
            img_clip = img_clip.set_duration(audio_clip.duration)
            img_clip_with_fx = self._create_ken_burns_effect(img_clip, audio_clip.duration)
            img_clip_with_fx = img_clip_with_fx.set_audio(audio_clip)
            clips_with_effects.append(img_clip_with_fx)

        if not clips_with_effects: return None

        video_clips_with_transitions = []
        current_pos = 0
        for i, clip in enumerate(clips_with_effects):
            if i > 0: current_pos -= transition_duration
            video_clips_with_transitions.append(clip.set_start(current_pos).crossfadein(transition_duration))
            current_pos += clip.duration
        
        final_video_clip = CompositeVideoClip(video_clips_with_transitions, size=dimensions)
        
        if background_music_path and os.path.exists(background_music_path):
            try:
                bg_music = AudioFileClip(background_music_path).volumex(0.2)
                if bg_music.duration < final_video_clip.duration:
                    bg_music = bg_music.fx(lambda c: c.loop(duration=final_video_clip.duration))
                else:
                    bg_music = bg_music.subclip(0, final_video_clip.duration)
                final_audio = CompositeAudioClip([final_video_clip.audio, bg_music])
                final_video_clip = final_video_clip.set_audio(final_audio)
            except Exception as e: print(f"Could not add background music: {e}")

        output_filepath = os.path.join(self.output_dir, output_filename)
        # ✅ THE FIX IS ON THIS LINE
        final_video_clip.write_videofile(output_filepath, codec="libx264", fps=24)
        return output_filepath