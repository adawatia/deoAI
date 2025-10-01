import os
import torch
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler # ✨ NEW: Import a faster scheduler

class VisualGenerator:
    def __init__(self, output_dir="generated_images"):
        self.output_dir = os.path.join(os.getcwd(), output_dir)
        os.makedirs(self.output_dir, exist_ok=True)
        
        if torch.cuda.is_available(): self.device = "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available(): self.device = "mps"
        else: self.device = "cpu"
        print(f"VisualGenerator using device: {self.device}")
        self.pipelines = {}

    def _load_pipeline(self, model_id="runwayml/stable-diffusion-v1-5"):
        if model_id in self.pipelines: return self.pipelines[model_id]
        print(f"Loading visual model: {model_id}...")
        try:
            pipeline = StableDiffusionPipeline.from_pretrained(
                model_id, torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
            )
            
            # ✨ NEW: Replace the default scheduler with the faster DPM-Solver
            pipeline.scheduler = DPMSolverMultistepScheduler.from_config(pipeline.scheduler.config)
            
            pipeline.to(self.device)

            # ✨ NEW: Apply torch.compile for a significant speed-up on compatible GPUs
            # This works best on PyTorch 2.0+ and NVIDIA Ampere GPUs or newer.
            if self.device == "cuda":
                pipeline.unet = torch.compile(pipeline.unet, mode="reduce-overhead", fullgraph=True)
                print("Torch compile enabled for UNet.")

            self.pipelines[model_id] = pipeline
            print(f"Model {model_id} loaded and optimized.")
            return pipeline
        except Exception as e:
            print(f"Error loading model {model_id}: {e}")
            return None

    def generate_visual_for_scene(self, scene_text: str, scene_index: int, 
                                  model_id: str = "runwayml/stable-diffusion-v1-5", 
                                  negative_prompt: str = None,
                                  width: int = 1920, height: int = 1080) -> str:
        pipeline = self._load_pipeline(model_id)
        if pipeline is None: return ""

        output_filepath = os.path.join(self.output_dir, f"scene_{scene_index}.png")
        try:
            print(f"Generating visual for scene {scene_index} with size {width}x{height}...")
            
            # ✨ NEW: Reduced inference steps from 50 to 25 because the new scheduler is more efficient
            image = pipeline(
                prompt=scene_text, negative_prompt=negative_prompt,
                width=width, height=height,
                num_inference_steps=25, # Drastically reduces generation time
                guidance_scale=7.5
            ).images[0]

            image.save(output_filepath)
            return output_filepath
        except Exception as e:
            print(f"Error generating visual for scene {scene_index}: {e}")
            return ""