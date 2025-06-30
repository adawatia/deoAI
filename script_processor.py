import re

class ScriptProcessor:
    def __init__(self):
        # Any initialization for your script processor can go here.
        # For now, it might be empty if no state needs to be managed.
        pass

    def process_script(self, raw_script: str) -> list:
        """
        Processes a raw script string into a list of individual scene texts.
        Each scene is typically separated by a specific delimiter (e.g., "Scene X:").
        """
        if not raw_script.strip():
            print("Warning: Received empty or whitespace-only script. Returning empty list.")
            return []

        # Split by "Scene X:" or "Scene X:" where X is a number
        # re.split will include empty strings at the beginning if the pattern is at the start.
        # We also want to capture the scene title if available.
        # Let's refine the splitting to better handle various formats.

        # New strategy: Split by lines, then group lines into scenes.
        # Or, split by known scene markers and then clean.
        # The previous `re.split(r'Scene \d+:', raw_script, flags=re.IGNORECASE)` is good,
        # but let's ensure leading empty strings are handled robustly.

        scenes_raw = re.split(r'(Scene\s*\d+\s*[:.]\s*)', raw_script, flags=re.IGNORECASE)
        # The split will return: ['', 'Scene 1: ', 'Text for scene 1', 'Scene 2: ', 'Text for scene 2', ...]
        # We need to pair them up or just take the text parts.

        processed_scenes = []
        current_scene_text = ""

        # Remove the first element if it's empty due to split at beginning of string
        if scenes_raw and not scenes_raw[0].strip():
            scenes_raw = scenes_raw[1:]

        # Iterate through the split parts to reconstruct scenes
        for part in scenes_raw:
            if re.match(r'Scene\s*\d+\s*[:.]\s*', part, flags=re.IGNORECASE):
                # If we encounter a new scene marker, and we have accumulated text for the previous scene,
                # add it to our list before starting a new one.
                if current_scene_text.strip():
                    processed_scenes.append(current_scene_text.strip())
                current_scene_text = "" # Reset for the new scene
            else:
                # Accumulate text for the current scene
                current_scene_text += part.strip() + " "

        # Add the last accumulated scene if any
        if current_scene_text.strip():
            processed_scenes.append(current_scene_text.strip())

        # Final cleaning (remove multiple spaces, newlines, etc.)
        cleaned_scenes = []
        for scene in processed_scenes:
            # Replace multiple newlines/spaces with a single space
            cleaned_scene = re.sub(r'\s+', ' ', scene).strip()
            # Remove any specific formatting characters from markdown that might interfere with TTS/Image prompts
            cleaned_scene = re.sub(r'[\*_`#]', '', cleaned_scene) # Example: remove markdown bold/italic/header chars
            if cleaned_scene: # Only add non-empty scenes
                cleaned_scenes.append(cleaned_scene)

        return cleaned_scenes

# Example of how to use (for testing this module independently)
if __name__ == "__main__":
    test_script_1 = """
    Scene 1: Introduction.
    The sun rises over a serene, misty lake, casting golden hues across the water. A lone fishing boat glides gently.

    Scene 2: Problem.
    Suddenly, dark clouds gather, and a fierce storm begins. Waves crash violently against the boat, threatening to capsize it.

    Scene 3: Solution.
    A lighthouse beam cuts through the gloom, guiding the struggling vessel to safety. The storm slowly dissipates.

    Scene 4: Conclusion.
    The boat reaches the shore as the sun breaks through the clouds, symbolizing hope and resilience.
    """

    test_script_2 = """
    First Scene: Welcome to our adventure.
    It's a beautiful day, perfect for exploring new horizons.

    Second Part: The journey begins.
    We set off on an exciting path, full of discovery.
    """

    processor = ScriptProcessor()

    print("--- Processing Test Script 1 ---")
    scenes_1 = processor.process_script(test_script_1)
    if scenes_1:
        for i, scene in enumerate(scenes_1):
            print(f"Scene {i+1} (Length: {len(scene)}):")
            print(scene)
            print("-" * 30)
    else:
        print("No scenes extracted from test_script_1.")

    print("\n--- Processing Test Script 2 ---")
    scenes_2 = processor.process_script(test_script_2)
    if scenes_2:
        for i, scene in enumerate(scenes_2):
            print(f"Scene {i+1} (Length: {len(scene)}):")
            print(scene)
            print("-" * 30)
    else:
        print("No scenes extracted from test_script_2.")

    print("\n--- Processing Empty Script ---")
    empty_scenes = processor.process_script("")
    print(f"Empty script result: {empty_scenes}")