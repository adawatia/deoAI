import re
import os
import json
from openai import OpenAI

class ScriptProcessor:
    def __init__(self):
        """Initializes the ScriptProcessor and configures the OpenAI client for OpenRouter."""
        self.client = None
        if os.getenv("OPENROUTER_API_KEY"):
            try:
                self.client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=os.getenv("OPENROUTER_API_KEY"),
                )
                print("OpenRouter client initialized successfully.")
            except Exception as e:
                print(f"Error initializing OpenRouter client: {e}")

    def process_script(self, raw_script: str) -> list:
        # ... (This method is unchanged)
        if not raw_script.strip(): return []
        scenes_raw = re.split(r'(Scene\s*\d+\s*[:.]\s*)', raw_script, flags=re.IGNORECASE)
        processed_scenes = []
        current_scene_text = ""
        if scenes_raw and not scenes_raw[0].strip(): scenes_raw = scenes_raw[1:]
        for part in scenes_raw:
            if re.match(r'Scene\s*\d+\s*[:.]\s*', part, flags=re.IGNORECASE):
                if current_scene_text.strip(): processed_scenes.append(current_scene_text.strip())
                current_scene_text = ""
            else:
                current_scene_text += part.strip() + " "
        if current_scene_text.strip(): processed_scenes.append(current_scene_text.strip())
        return [re.sub(r'\s+', ' ', scene).strip() for scene in processed_scenes if scene.strip()]

    def generate_full_script(self, topic: str, num_scenes: int = 4) -> list:
        """
        Uses an OpenRouter model to generate a video script with distinct visual prompts
        and voiceover scripts for each scene, returned as a structured list.
        """
        if not self.client:
            raise Exception("OpenRouter client is not initialized. Please check your API key.")

        system_prompt = f"""
        You are a creative director. Your task is to generate a script for a short video based on a topic.
        The script must be divided into exactly {num_scenes} scenes.
        For each scene, provide two distinct things:
        1.  'visual_prompt': A concise, visual sentence for an AI image generator.
        2.  'voiceover_script': A narrative sentence for an AI voiceover that complements the visual.

        You MUST return the output as a valid JSON array of objects. Even if the number of scenes is small, like 2, you must still adhere to this exact format:
        [
          {{"scene": 1, "visual_prompt": "...", "voiceover_script": "..."}},
          {{"scene": 2, "visual_prompt": "...", "voiceover_script": "..."}}
        ]
        """
        try:
            completion = self.client.chat.completions.create(
              model="openai/gpt-4o",
              messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": f"Topic: \"{topic}\""}],
              response_format={"type": "json_object"},
            )
            response_data = json.loads(completion.choices[0].message.content)
            if isinstance(response_data, dict):
                for key, value in response_data.items():
                    if isinstance(value, list): return value
            elif isinstance(response_data, list): return response_data
            raise ValueError("Invalid JSON structure received from API.")
        except Exception as e:
            print(f"Error generating full script: {e}")
            return []

    def modify_voiceover_style(self, scenes: list, style: str) -> list:
        # ... (This method is unchanged)
        if not self.client or style.lower() == 'default': return scenes
        original_scripts = [scene['voiceover_script'] for scene in scenes]
        system_prompt = f"""
        You are a script editor. Rewrite the following voiceover scripts to fit a '{style}' style.
        Return the rewritten scripts as a valid JSON array of strings, with the same number of scripts as the input.
        Example output: ["Rewritten script 1.", "Rewritten script 2."]
        """
        try:
            completion = self.client.chat.completions.create(
              model="openai/gpt-4o",
              messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": json.dumps(original_scripts)}],
              response_format={"type": "json_object"},
            )
            response_data = json.loads(completion.choices[0].message.content)
            rewritten_scripts = []
            if isinstance(response_data, dict):
                 for key, value in response_data.items():
                    if isinstance(value, list): rewritten_scripts = value; break
            elif isinstance(response_data, list): rewritten_scripts = response_data
            if not rewritten_scripts or len(rewritten_scripts) != len(scenes):
                raise ValueError("Rewritten scripts count does not match original.")
            for i, scene in enumerate(scenes):
                scene['voiceover_script'] = rewritten_scripts[i]
            return scenes
        except Exception as e:
            print(f"Error modifying voiceover style: {e}. Using original scripts.")
            return scenes

    def enhance_prompt_for_visuals(self, scene_text: str) -> str:
        # ... (This method is unchanged)
        if not self.client: return scene_text
        system_prompt = """
        You are an expert prompt engineer for an AI image generator with a 77-token limit.
        Your task is to take a simple scene description and rewrite it into a detailed, artistic prompt.
        Incorporate style and lighting, but keep the final prompt concise and **ideally under 60 words**.
        Only return the final prompt itself, with no preamble.
        """
        try:
            completion = self.client.chat.completions.create(
              model="openai/gpt-4o",
              messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": f'Simple description: "{scene_text}"'}]
            )
            return completion.choices[0].message.content.strip().replace("\n", " ")
        except Exception as e:
            print(f"Error enhancing prompt: {e}. Using original text.")
            return scene_text