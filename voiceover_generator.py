import os
import torch # For checking CUDA availability
import torchaudio as ta # For saving audio
from pydub import AudioSegment # For silent audio fallback

import re # For text cleaning

# --- Chatterbox-TTS Specific Imports and Model Loading ---
try:
    from chatterbox.tts import ChatterboxTTS
    print("Chatterbox-TTS imported successfully.")
    CHATTTERBOX_TTS_AVAILABLE = True
except ImportError:
    print("Chatterbox-TTS library not found. Voiceover generation will be unavailable.")
    print("Please ensure 'chatterbox-tts' is installed correctly.")
    CHATTTERBOX_TTS_AVAILABLE = False
except Exception as e:
    print(f"An unexpected error occurred during Chatterbox-TTS import: {e}")
    CHATTTERBOX_TTS_AVAILABLE = False

# Global flag for overall availability
CHATTTERBOX_AVAILABLE = CHATTTERBOX_TTS_AVAILABLE


class VoiceoverGenerator:
    def __init__(self, output_dir="generated_audio"):
        global CHATTTERBOX_AVAILABLE # Declare global if you modify it in __init__

        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.model = None # Renamed from synthesizer to model as per ChatterboxTTS class
        self.sample_rate = 22050 # Default sample rate, will be updated by model.sr

        if CHATTTERBOX_AVAILABLE:
            try:
                # Dynamically select device (CUDA if available, else CPU)
                if torch.cuda.is_available():
                    self.device = "cuda"
                    print("CUDA is available. Initializing ChatterboxTTS on GPU.")
                else:
                    self.device = "cpu"
                    print("CUDA not available. Initializing ChatterboxTTS on CPU.")

                # Load the ChatterboxTTS model from Hugging Face
                # The .from_pretrained() method handles downloading the model from the hub.
                self.model = ChatterboxTTS.from_pretrained(device=self.device)
                self.sample_rate = self.model.sr # Get the actual sample rate from the model

                print(f"ChatterboxTTS model loaded successfully on {self.device}.")
                print(f"Model sample rate: {self.sample_rate} Hz")

            except Exception as e:
                print(f"Error initializing ChatterboxTTS model: {e}")
                print("Please ensure your PyTorch installation is compatible with your device,")
                print("and that the model can be downloaded from Hugging Face.")
                self.model = None
                CHATTTERBOX_AVAILABLE = False # Mark as unavailable if initialization fails


    def generate_voiceover_for_scene(self, scene_text: str, scene_index: int, voice_style: str = "default") -> str:
        """
        Generates a voiceover for a single scene and saves it as a WAV file.
        Returns the path to the generated audio file.
        """
        if not CHATTTERBOX_AVAILABLE or self.model is None:
            print("ChatterboxTTS model is not initialized. Cannot generate voiceover.")
            # Fallback: create a silent audio file
            output_filepath_wav = os.path.join(self.output_dir, f"scene_{scene_index}_silent.wav")
            AudioSegment.silent(duration=2000).export(output_filepath_wav, format="wav")
            return output_filepath_wav

        # Sanitize scene text for TTS
        cleaned_text = re.sub(r'[\*_`#]', '', scene_text)
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()

        if not cleaned_text:
            print(f"Scene {scene_index} has no clean text, generating silent audio.")
            output_filepath_wav = os.path.join(self.output_dir, f"scene_{scene_index}_silent.wav")
            AudioSegment.silent(duration=1000).export(output_filepath_wav, format="wav")
            return output_filepath_wav

        output_filepath_wav = os.path.join(self.output_dir, f"scene_{scene_index}.wav")

        try:
            print(f"Generating voiceover for scene {scene_index} (length: {len(cleaned_text)} chars) on {self.device}: '{cleaned_text[:70]}...'")

            # --- ACTUAL CHATTERBOX-TTS SYNTHESIS CALL ---
            # The generate method returns a torch.Tensor and the sample rate is available from model.sr
            wav_tensor = self.model.generate(cleaned_text)

            # --- Save audio using torchaudio ---
            # torchaudio.save expects a tensor, and will handle the .wav format.
            ta.save(output_filepath_wav, wav_tensor, self.sample_rate)

            print(f"Generated voiceover for scene {scene_index} at: {output_filepath_wav}")
            return output_filepath_wav

        except Exception as e:
            print(f"Error generating voiceover for scene {scene_index}: {e}")
            # On error, generate a silent audio file
            output_filepath_wav = os.path.join(self.output_dir, f"scene_{scene_index}_error.wav")
            AudioSegment.silent(duration=3000).export(output_filepath_wav, format="wav")
            return output_filepath_wav

    def get_chatterbox_availability(self):
        return CHATTTERBOX_AVAILABLE

# Example of how to use (for testing this module independently)
if __name__ == "__main__":
    vo_gen = VoiceoverGenerator()
    if vo_gen.get_chatterbox_availability():
        print("ChatterboxTTS model is available. Attempting to generate test voiceover.")
        test_scene_text = "This is a test voiceover generated by the ChatterboxTTS model. It's exciting to see it working!"
        # You can add an audio prompt path here for voice cloning if you have a file.
        # Ensure 'YOUR_AUDIO_PROMPT.wav' exists and is a valid audio file.
        # audio_prompt_for_cloning = "YOUR_AUDIO_PROMPT.wav"
        # if os.path.exists(audio_prompt_for_cloning):
        #     test_scene_text_2 = "This voice should sound like the audio prompt."
        #     try:
        #         audio_path_2 = vo_gen.generate_voiceover_for_scene(test_scene_text_2, 1, audio_prompt=audio_prompt_for_cloning)
        #         print(f"Test audio with prompt generated at: {audio_path_2}")
        #     except Exception as e:
        #         print(f"Failed to generate test audio with prompt: {e}")
        try:
            audio_path = vo_gen.generate_voiceover_for_scene(test_scene_text, 0, "default")
            print(f"Test audio generated at: {audio_path}")
            # Optional: Play back the audio (requires sound device, e.g., 'pydub.playback')
            # from pydub.playback import play
            # play(AudioSegment.from_file(audio_path))
        except Exception as e:
            print(f"Failed to generate test audio: {e}")
    else:
        print("ChatterboxTTS is not fully set up. Cannot run voiceover test.")
        print("Please ensure 'chatterbox-tts' and 'torchaudio' are installed,")
        print("and PyTorch is correctly configured for your device (CPU/GPU).")