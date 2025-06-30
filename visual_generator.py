import os
from PIL import Image # Pillow for image manipulation/saving

try:
    from diffusers import StableDiffusionPipeline
    import torch
    print("Diffusers and PyTorch imported successfully for visual generation.")
    VISUAL_GENERATOR_AVAILABLE = True
except ImportError:
    print("Diffusers or PyTorch not found. Image generation will be unavailable.")
    print("Please install with: uv pip install diffusers transformers accelerate torch")
    VISUAL_GENERATOR_AVAILABLE = False
except Exception as e:
    print(f"An unexpected error occurred during visual generator import: {e}")
    VISUAL_GENERATOR_AVAILABLE = False

class VisualGenerator:
    def __init__(self, output_dir="generated_images"):
        global VISUAL_GENERATOR_AVAILABLE

        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.pipeline = None
        self.device = "cpu" # Default to CPU

        if VISUAL_GENERATOR_AVAILABLE:
            try:
                if torch.cuda.is_available():
                    self.device = "cuda"
                    print("CUDA is available. Initializing Stable Diffusion on GPU.")
                elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available(): # For Apple Silicon
                    self.device = "mps"
                    print("MPS is available. Initializing Stable Diffusion on Apple Silicon GPU.")
                else:
                    print("CUDA/MPS not available. Initializing Stable Diffusion on CPU (will be slow).")

                # You can choose a different Stable Diffusion model here.
                # 'runwayml/stable-diffusion-v1-5' is a common starting point.
                # For SDXL: 'stabilityai/stable-diffusion-xl-base-1.0' (requires more VRAM)
                model_id = "runwayml/stable-diffusion-v1-5"
                self.pipeline = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16 if self.device == "cuda" else torch.float32)
                self.pipeline.to(self.device)
                self.pipeline.safety_checker = lambda images, **kwargs: (images, [False] * len(images)) # Disable safety checker for development (use with caution)

                print(f"Stable Diffusion pipeline loaded successfully on {self.device}.")

            except Exception as e:
                print(f"Error initializing Stable Diffusion pipeline: {e}")
                print("Please ensure your PyTorch installation is compatible with your device,")
                print("and that the model can be downloaded from Hugging Face.")
                self.pipeline = None
                VISUAL_GENERATOR_AVAILABLE = False

    def generate_visual_for_scene(self, scene_text: str, scene_index: int) -> str:
        """
        Generates an image for a single scene based on its text.
        Returns the path to the generated image file.
        """
        if not VISUAL_GENERATOR_AVAILABLE or self.pipeline is None:
            print("Visual generator is not initialized. Cannot generate image.")
            # Fallback: return a placeholder image path (you'd need a default image)
            # For now, let's just return an empty string or raise an error.
            return "" # Or path to a default blank image.

        # Refine the prompt for better image generation.
        # This is crucial for good results!
        prompt = f"High-quality, cinematic, detailed illustration: {scene_text}, a captivating scene, concept art, digital painting."
        # You can add negative prompts too:
        # negative_prompt = "blurry, low quality, deformed, bad anatomy, ugly, tiling, poorly drawn face"

        output_filepath = os.path.join(self.output_dir, f"scene_{scene_index}.png")

        try:
            print(f"Generating visual for scene {scene_index} with prompt: '{prompt[:100]}...'")
            # Generate image
            # num_inference_steps can be adjusted for quality vs speed
            # guidance_scale impacts how much the prompt influences the image
            image = self.pipeline(prompt, num_inference_steps=30, guidance_scale=7.5).images[0]

            # Save the image
            image.save(output_filepath)

            print(f"Generated visual for scene {scene_index} at: {output_filepath}")
            return output_filepath

        except Exception as e:
            print(f"Error generating visual for scene {scene_index}: {e}")
            return "" # Or path to a default blank image

    def get_visual_generator_availability(self):
        return VISUAL_GENERATOR_AVAILABLE

# Example of how to use (for testing this module independently)
if __name__ == "__main__":
    vg = VisualGenerator()
    if vg.get_visual_generator_availability():
        print("Visual Generator is available. Attempting to generate test image.")
        test_scene_text = "A majestic dragon soaring over a futuristic cityscape at sunset, highly detailed, dramatic lighting."
        try:
            image_path = vg.generate_visual_for_scene(test_scene_text, 0)
            print(f"Test image generated at: {image_path}")
            # You can open the image to view it:
            # if os.path.exists(image_path):
            #     Image.open(image_path).show()
        except Exception as e:
            print(f"Failed to generate test image: {e}")
    else:
        print("Visual Generator not set up. Cannot run image generation test.")