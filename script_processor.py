import nltk
from nltk.tokenize import sent_tokenize
import re
import os
import google.generativeai as genai
import textwrap
from dotenv import load_dotenv # Import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Download necessary NLTK data (only run this once or put it in your app's startup)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    print("NLTK 'punkt' tokenizer not found. Attempting to download...")
    try:
        nltk.download('punkt')
        print("NLTK 'punkt' tokenizer downloaded successfully.")
    except Exception as e:
        print(f"Error downloading NLTK 'punkt' tokenizer: {e}")
        print("Please try downloading it manually by running 'python -c \"import nltk; nltk.download(\'punkt\')\"' in your terminal.")
        raise RuntimeError("Failed to download NLTK 'punkt' tokenizer. Please check your internet connection or try manual download.")

# Configure Gemini API
API_KEY = os.getenv("GOOGLE_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    print("WARNING: GOOGLE_API_KEY environment variable not set. Gemini features will be unavailable.")
    print("Please ensure you have a .env file with GOOGLE_API_KEY='YOUR_KEY' or set it as a system environment variable.")


class ScriptProcessor:
    def __init__(self):
        self.model = None
        if API_KEY: # Only try to initialize model if API_KEY was found
            try:
                self.model = genai.GenerativeModel('gemini-pro')
                # A quick test call to check API key and connectivity (optional, can add more robust check)
                # For example: self.model.generate_content("hello").text
            except Exception as e:
                print(f"Error initializing Gemini model: {e}")
                self.model = None # Set to None if initialization fails

    def split_script_into_scenes(self, script_text: str) -> list[str]:
        """
        Splits a raw script text into a list of individual scene texts.
        This version uses a combination of paragraph breaks and basic sentence
        analysis to identify potential scene changes.
        """
        if not script_text or not script_text.strip():
            return []

        # Normalize line endings and remove excessive blank lines
        script_text = script_text.replace('\r\n', '\n').replace('\r', '\n')
        script_text = re.sub(r'\n{2,}', '\n\n', script_text).strip()

        # Initial split by double newlines (paragraphs)
        paragraphs = [p.strip() for p in script_text.split('\n\n') if p.strip()]

        scenes = []
        current_scene_paragraphs = []

        for paragraph in paragraphs:
            is_scene_indicator = re.match(r'^(INT\.|EXT\.|SCENE\s+\d+|CUT\s+TO:|FADE\s+IN\.|FADE\s+OUT\.|[A-Z\s]+:)', paragraph, re.IGNORECASE)

            if is_scene_indicator and current_scene_paragraphs:
                scenes.append("\n\n".join(current_scene_paragraphs))
                current_scene_paragraphs = [paragraph]
            elif len(sent_tokenize(paragraph)) <= 2 and len(paragraph.split()) < 15 and current_scene_paragraphs:
                current_scene_paragraphs.append(paragraph)
            else:
                current_scene_paragraphs.append(paragraph)

        if current_scene_paragraphs:
            scenes.append("\n\n".join(current_scene_paragraphs))

        final_scenes = []
        temp_scene = ""
        for i, scene in enumerate(scenes):
            sentences = sent_tokenize(scene)
            if len(sentences) < 3 and i > 0 and len(scene.split()) < 50:
                if temp_scene:
                    temp_scene += "\n\n" + scene
                else:
                    temp_scene = scene
            else:
                if temp_scene:
                    final_scenes.append(temp_scene)
                    temp_scene = ""
                final_scenes.append(scene)

        if temp_scene:
            final_scenes.append(temp_scene)

        cleaned_scenes = []
        for scene in final_scenes:
            if len(sent_tokenize(scene)) == 1 and len(scene.split()) < 10 and not re.match(r'^(INT\.|EXT\.|SCENE\s+\d+|CUT\s+TO:|FADE\s+IN\.|FADE\s+OUT\.|[A-Z\s]+:)', scene.strip(), re.IGNORECASE):
                pass
            cleaned_scenes.append(scene)

        return cleaned_scenes

    def analyze_scene_with_gemini(self, scene_text: str) -> dict:
        """
        Uses Gemini to analyze a single scene and extract a title/summary and potential keywords.
        Returns a dictionary with 'title', 'summary', and 'keywords'.
        """
        if not self.model:
            return {"title": "AI Analysis Unavailable", "summary": "Gemini API not configured or failed to initialize.", "keywords": []}

        prompt = textwrap.dedent(f"""
        Analyze the following scene text. Provide:
        1. A concise title for the scene (max 10 words).
        2. A brief summary of the scene (1-2 sentences).
        3. 3-5 keywords or visual cues that represent the core elements or mood of the scene.

        Format your response clearly as follows:
        Title: [Your Scene Title]
        Summary: [Your Scene Summary]
        Keywords: [keyword1], [keyword2], [keyword3], ...

        Scene Text:
        ---
        {scene_text}
        ---
        """)

        try:
            response = self.model.generate_content(prompt)
            gemini_output = response.text.strip()

            title = "N/A"
            summary = "N/A"
            keywords = []

            lines = gemini_output.split('\n')
            for line in lines:
                if line.lower().startswith("title:"):
                    title = line[len("Title:"):].strip()
                elif line.lower().startswith("summary:"):
                    summary = line[len("Summary:"):].strip()
                elif line.lower().startswith("keywords:"):
                    keywords_str = line[len("Keywords:"):].strip()
                    keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]

            return {"title": title, "summary": summary, "keywords": keywords}

        except Exception as e:
            print(f"Error analyzing scene with Gemini: {e}")
            return {"title": "AI Error", "summary": f"Could not analyze scene: {e}", "keywords": []}