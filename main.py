import streamlit as st
import os
from datetime import datetime
from dotenv import load_dotenv

# --- Import your backend modules ---
try:
    from script_processor import ScriptProcessor
    from voiceover_generator import VoiceoverGenerator
    from visual_generator import VisualGenerator
    from video_assembler import VideoAssembler
except ImportError as e:
    st.error(f"Failed to import a module. Error: {e}")
    st.stop()

# --- Configuration & Setup ---
load_dotenv()
for dir_path in ["generated_audio", "generated_images", "final_videos", "temp_assets"]:
    os.makedirs(dir_path, exist_ok=True)

# Initialize Session State
if "app_step" not in st.session_state:
    st.session_state.app_step = "create_script"
if "scenes" not in st.session_state:
    st.session_state.scenes = []
if "manual_script" not in st.session_state:
    st.session_state.manual_script = ""
if "final_video_path" not in st.session_state:
    st.session_state.final_video_path = None

# --- Cached Functions ---
@st.cache_resource
def load_models():
    script_processor = ScriptProcessor()
    voiceover_generator = VoiceoverGenerator(output_dir="generated_audio")
    visual_generator = VisualGenerator(output_dir="generated_images")
    return script_processor, voiceover_generator, visual_generator

@st.cache_data
def generate_scene_asset(scene_index, visual_prompt, voiceover_script, enable_vo, model_id, negative_prompt, dimensions):
    _, voiceover_gen, visual_gen = load_models()
    width, height = dimensions
    image_path = visual_gen.generate_visual_for_scene(visual_prompt, scene_index, model_id, negative_prompt, width, height)
    if not image_path:
        from PIL import Image
        placeholder_image = Image.new('RGB', (width, height), color='black')
        image_path = os.path.join("temp_assets", f"black_placeholder_{scene_index}.png")
        placeholder_image.save(image_path)
    if enable_vo:
        audio_path = voiceover_gen.generate_voiceover_for_scene(voiceover_script, scene_index)
    else:
        from pydub import AudioSegment
        silent_audio = AudioSegment.silent(duration=5000)
        audio_path = os.path.join("temp_assets", f"silent_{scene_index}.wav")
        silent_audio.export(audio_path, format="wav")
    return audio_path, image_path

# --- Main Generation Logic ---
def run_video_generation(scenes, sidebar_options):
    st.session_state.app_step = "generate_video"
    video_assembler = VideoAssembler(output_dir="final_videos")
    final_scenes = scenes
    if sidebar_options['voiceover_style'] != "Default" and sidebar_options['enable_voiceover']:
        st.toast(f"Applying '{sidebar_options['voiceover_style']}' voiceover style...")
        final_scenes = script_processor.modify_voiceover_style(final_scenes, sidebar_options['voiceover_style'])
    scene_assets = []
    progress_text = "Generating scene assets... (This can take several minutes)"
    progress_bar = st.progress(0, text=progress_text)
    for i, scene in enumerate(final_scenes):
        st.write(f"⚙️ Processing Scene {i+1}/{len(final_scenes)}...")
        audio_path, image_path = generate_scene_asset(
            i, scene['visual_prompt'], scene['voiceover_script'], sidebar_options['enable_voiceover'],
            sidebar_options['model_id'], sidebar_options['negative_prompt'], sidebar_options['dimensions']
        )
        scene_assets.append({"image_path": image_path, "audio_path": audio_path})
        progress_bar.progress(int(((i + 1) / len(final_scenes)) * 100))
    st.write("🎬 Assembling the final video...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"faceless_video_{timestamp}.mp4"
    final_video_path = video_assembler.assemble_video(scene_assets, sidebar_options['music_path'], output_filename, sidebar_options['dimensions'])
    st.session_state.final_video_path = final_video_path

# --- Custom CSS ---
st.markdown("""
<style>
    /* Main app styling */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
    }
    
    /* Card-like containers */
    .stContainer {
        background: white;
        border-radius: 15px;
        padding: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    /* Headers */
    h1 {
        color: white;
        text-align: center;
        font-size: 3rem !important;
        font-weight: 800 !important;
        margin-bottom: 0.5rem !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    
    h2 {
        color: #667eea;
        font-weight: 700 !important;
        margin-top: 1.5rem !important;
        margin-bottom: 1rem !important;
    }
    
    h3 {
        color: #764ba2;
        font-weight: 600 !important;
    }
    
    /* Buttons */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s ease;
        border: none;
        padding: 0.75rem 2rem;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    
    /* Primary button */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    [data-testid="stSidebar"] .stTitle {
        color: #667eea;
        font-weight: 700;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #f8f9fa;
        border-radius: 8px;
        font-weight: 600;
    }
    
    /* Text inputs and text areas */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 8px;
        border: 2px solid #e9ecef;
        transition: border-color 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Radio buttons */
    .stRadio > div {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
    }
    
    /* Progress bar */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Divider */
    hr {
        margin: 2rem 0;
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #667eea, transparent);
    }
    
    /* Info boxes */
    .stAlert {
        border-radius: 10px;
    }
    
    /* Step indicator */
    .step-indicator {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 2rem 0;
        gap: 1rem;
    }
    
    .step {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        background: #e9ecef;
        color: #6c757d;
    }
    
    .step.active {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .step.completed {
        background: #28a745;
        color: white;
    }
    
    /* Scene cards */
    .scene-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #667eea;
    }
</style>
""", unsafe_allow_html=True)

# --- UI Layout ---
st.set_page_config(layout="wide", page_title="DeoAI Video Creator", page_icon="🎬")

# Sidebar
with st.sidebar:
    st.markdown("# 🎭 DeoAI Settings")
    st.markdown("---")
    
    with st.expander("🔑 API Configuration", expanded=True):
        api_key_input = st.text_input("OpenRouter API Key", type="password", placeholder="sk-or-v1-...", help="Enter your OpenRouter API key")
    
    st.markdown("### 🎙️ Audio Settings")
    with st.container():
        enable_voiceover = st.toggle("Enable Voiceover", value=True, help="Add AI-generated voiceover to your video")
        voiceover_style = st.selectbox(
            "Voiceover Style", 
            ["Default", "Energetic", "Happy", "Sad", "Professional"], 
            disabled=(not enable_voiceover),
            help="Choose the tone for your voiceover"
        )
        st.markdown("---")
        enable_music = st.toggle("Enable Background Music", value=True, help="Add background music to your video")
        uploaded_music = st.file_uploader(
            "Upload Music Track", 
            type=['mp3', 'wav'], 
            disabled=(not enable_music),
            help="Upload your own music (MP3 or WAV)"
        )
    
    st.markdown("### 🎨 Visual Settings")
    with st.container():
        ASPECT_RATIOS = {
            "Fast Demo (1:1)": (512, 512), 
            "Landscape (16:9)": (1920, 1080), 
            "Portrait (9:16)": (1080, 1920), 
            "Square (1:1)": (1080, 1080)
        }
        selected_ratio_name = st.selectbox(
            "Aspect Ratio", 
            options=list(ASPECT_RATIOS.keys()),
            help="Choose the video dimensions"
        )
        dimensions = ASPECT_RATIOS[selected_ratio_name]
        
        VISUAL_MODELS = {
            "Realistic": "runwayml/stable-diffusion-v1-5", 
            "Anime": "andite/anything-v4.0", 
            "Fantasy Art": "dreamlike-art/dreamlike-photoreal-2.0"
        }
        selected_model_name = st.selectbox(
            "Visual Style", 
            options=list(VISUAL_MODELS.keys()),
            help="Select the art style for your visuals"
        )
        negative_prompt = st.text_area(
            "Negative Prompt", 
            placeholder="blurry, text, watermark, low quality",
            help="Describe what you DON'T want in the images",
            height=100
        )

music_path = None
if enable_music and uploaded_music:
    music_path = os.path.join("temp_assets", uploaded_music.name)
    with open(music_path, "wb") as f: 
        f.write(uploaded_music.getbuffer())

sidebar_options = {
    "enable_voiceover": enable_voiceover, 
    "voiceover_style": voiceover_style, 
    "enable_music": enable_music,
    "music_path": music_path, 
    "dimensions": dimensions, 
    "model_id": VISUAL_MODELS[selected_model_name],
    "negative_prompt": negative_prompt
}

# Main Page Header
st.markdown("# 🎬 DeoAI Faceless Video Creator")
st.markdown("<p style='text-align: center; color: white; font-size: 1.2rem; margin-top: -1rem;'>Create stunning AI-powered videos in minutes</p>", unsafe_allow_html=True)

# Step Indicator
current_step = {"create_script": 1, "review_script": 2, "generate_video": 3}.get(st.session_state.app_step, 1)
st.markdown(f"""
<div class='step-indicator'>
    <div class='step {"active" if current_step == 1 else "completed" if current_step > 1 else ""}'>1</div>
    <div style='width: 60px; height: 2px; background: {"#667eea" if current_step >= 2 else "#e9ecef"};'></div>
    <div class='step {"active" if current_step == 2 else "completed" if current_step > 2 else ""}'>2</div>
    <div style='width: 60px; height: 2px; background: {"#667eea" if current_step >= 3 else "#e9ecef"};'></div>
    <div class='step {"active" if current_step == 3 else ""}'>3</div>
</div>
<p style='text-align: center; color: white; margin-top: 0.5rem;'>
    <strong>{"Create Script" if current_step == 1 else "Review & Edit" if current_step == 2 else "Generate Video"}</strong>
</p>
""", unsafe_allow_html=True)

openrouter_api_key = api_key_input or os.getenv("OPENROUTER_API_KEY")
if not openrouter_api_key:
    st.warning("⚠️ Please enter your OpenRouter API key in the sidebar to begin.")
    st.info("Don't have an API key? Get one at [OpenRouter.ai](https://openrouter.ai)")
    st.stop()

os.environ["OPENROUTER_API_KEY"] = openrouter_api_key

with st.spinner("🔄 Loading AI models..."):
    script_processor, _, __ = load_models()

# --- Step 1: Create Script ---
if st.session_state.app_step == "create_script":
    st.markdown("## ✍️ Step 1: Create Your Script")
    
    with st.container():
        method = st.radio(
            "How would you like to create your script?", 
            ["🤖 Generate with AI", "✏️ Write Manually"], 
            horizontal=True,
            label_visibility="collapsed"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if method == "✏️ Write Manually":
            st.markdown("### 📝 Write Your Script")
            st.session_state.manual_script = st.text_area(
                "Enter your script:", 
                height=300, 
                value=st.session_state.manual_script,
                placeholder="Write your video script here... Each paragraph will become a scene.",
                label_visibility="collapsed"
            )
        else:
            st.markdown("### 🤖 AI Script Generator")
            col1, col2 = st.columns([4, 1])
            with col1: 
                ai_topic = st.text_input(
                    "Topic:", 
                    placeholder="e.g., The benefits of meditation, History of the Internet, How to bake a cake...",
                    label_visibility="collapsed"
                )
            with col2: 
                num_scenes = st.number_input("Scenes", min_value=2, max_value=10, value=4, help="Number of scenes to generate")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Next: Review Script", type="primary", use_container_width=True):
            if method == "✏️ Write Manually":
                if st.session_state.manual_script.strip():
                    with st.spinner("Processing your script..."):
                        scenes = [{"visual_prompt": text, "voiceover_script": text} for text in script_processor.process_script(st.session_state.manual_script)]
                        st.session_state.scenes = scenes
                        st.session_state.app_step = "review_script"
                        st.rerun()
                else: 
                    st.error("❌ Please enter a script before continuing.")
            else:
                if ai_topic:
                    with st.spinner("🤖 AI is writing your script... This may take a moment."):
                        generated_scenes = script_processor.generate_full_script(ai_topic, num_scenes)
                        if generated_scenes:
                            st.session_state.scenes = generated_scenes
                            st.session_state.app_step = "review_script"
                            st.success("✅ Script generated successfully!")
                            st.rerun()
                        else: 
                            st.error("❌ AI script generation failed. Please check your API key and try again.")
                else: 
                    st.error("❌ Please enter a topic for the AI to write about.")

# --- Step 2: Review and Edit Script ---
elif st.session_state.app_step == "review_script":
    st.markdown("## ✏️ Step 2: Review & Edit Your Script")
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("### 📋 Script Scenes")
        for i, scene in enumerate(st.session_state.scenes):
            with st.expander(f"🎬 Scene {i+1}", expanded=(i==0)):
                scene['visual_prompt'] = st.text_area(
                    "Visual Description", 
                    value=scene.get('visual_prompt', ''), 
                    key=f"vp_{i}",
                    height=100,
                    help="Describe what should appear in this scene"
                )
                scene['voiceover_script'] = st.text_area(
                    "Voiceover Narration", 
                    value=scene.get('voiceover_script', ''), 
                    key=f"vo_{i}",
                    height=100,
                    help="The text that will be spoken in this scene"
                )
    
    with col2:
        st.markdown("### ⚙️ Generation Settings")
        with st.container():
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); padding: 1.5rem; border-radius: 12px;'>
                <p style='margin: 0.5rem 0;'><strong>📐 Aspect Ratio:</strong> {selected_ratio_name}</p>
                <p style='margin: 0.5rem 0;'><strong>🎨 Visual Style:</strong> {selected_model_name}</p>
                <p style='margin: 0.5rem 0;'><strong>🎙️ Voiceover:</strong> {'✅ Enabled' if enable_voiceover else '❌ Disabled'}</p>
            """, unsafe_allow_html=True)
            
            if enable_voiceover: 
                st.markdown(f"<p style='margin: 0.5rem 0;'><strong>🎭 Style:</strong> {voiceover_style}</p>", unsafe_allow_html=True)
            
            st.markdown(f"<p style='margin: 0.5rem 0;'><strong>🎵 Music:</strong> {'✅ Enabled' if enable_music and uploaded_music else '❌ Disabled'}</p></div>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.info(f"💡 **Total Scenes:** {len(st.session_state.scenes)}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()
    
    bcol1, bcol2, bcol3 = st.columns([1, 2, 1])
    with bcol1:
        if st.button("⬅️ Back", use_container_width=True):
            st.session_state.app_step = "create_script"
            st.rerun()
    with bcol3:
        if st.button("🎬 Generate Video", type="primary", use_container_width=True):
            run_video_generation(st.session_state.scenes, sidebar_options)
            st.rerun()

# --- Step 3: Generate Video & Display ---
elif st.session_state.app_step == "generate_video":
    if st.session_state.final_video_path and os.path.exists(st.session_state.final_video_path):
        st.balloons()
        st.markdown("## 🎉 Your Video is Ready!")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            st.video(st.session_state.final_video_path)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            with open(st.session_state.final_video_path, "rb") as f:
                st.download_button(
                    "📥 Download Video", 
                    f, 
                    os.path.basename(st.session_state.final_video_path), 
                    "video/mp4",
                    use_container_width=True,
                    type="primary"
                )
    else:
        st.error("❌ Something went wrong during video generation. Please try again.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔄 Create a New Video", use_container_width=True, type="primary"):
            st.session_state.app_step = "create_script"
            st.session_state.scenes = []
            st.session_state.manual_script = ""
            st.session_state.final_video_path = None
            st.rerun()