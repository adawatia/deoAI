# 🎭 DeoAI: Faceless Video Generation

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Built with PyTorch](https://img.shields.io/badge/Built%20with-PyTorch-EE4C2C.svg?logo=pytorch)](https://pytorch.org/)
[![Hugging Face](https://img.shields.io/badge/Hugging%20Face-Models-FFD21C.svg?logo=huggingface)](https://huggingface.co/ResembleAI/chatterbox)
[![Code Style: Black](https://img.shields.io/badge/Code%20Style-Black-000000.svg)](https://github.com/psf/black)

## ✨ Overview

DeoAI is an innovative open-source project designed to automate the creation of "faceless" videos. These videos typically feature dynamic visuals with voiceover narration, perfect for explainer videos, educational content, social media snippets, and more, without needing on-camera talent.

Leveraging cutting-edge AI models for Text-to-Speech (TTS) and Text-to-Image generation, DeoAI transforms a simple script into a complete video, synchronized with engaging visuals and optional background music.

## 🚀 Features

* **Script Processing:** Parses raw text scripts into manageable scenes.
* **AI Voiceovers:** Generates natural-sounding voiceovers for each scene using **ChatterboxTTS** (powered by `ResembleAI/chatterbox` on Hugging Face).
* **AI Visual Generation:** Creates descriptive images for each scene from text prompts using **Stable Diffusion** via Hugging Face `diffusers`.
* **Video Assembly:** Stitches together generated audio and images into a cohesive video file with synchronized durations using **MoviePy**.
* **Background Music:** Option to add looping background music to the final video.
* **Extensible:** Designed with modular components, allowing easy integration of different TTS models, image generation models, or video editing techniques.

## ⚙️ Technologies Used

* **Python 3.10+**
* **`chatterbox-tts`**: For high-quality Text-to-Speech.
* **`diffusers` (Hugging Face)**: For state-of-the-art Text-to-Image generation (e.g., Stable Diffusion).
* **`moviepy`**: For video assembly and editing.
* **`pydub` & `torchaudio`**: For audio manipulation and saving.
* **`torch`**: Underlying deep learning framework.
* **FFmpeg**: Essential multimedia framework (required by `moviepy` and `pydub`).

## 📥 Installation

### Prerequisites

Before you begin, ensure you have:

* **Python 3.10 or newer** installed.
* **`uv`**: A fast Python package installer and package manager. If you don't have it, install it:
    ```bash
    curl -LsSf [https://astral.sh/uv/install.sh](https://astral.sh/uv/install.sh) | sh
    ```
    Then ensure `~/.cargo/bin` is in your PATH.
* **FFmpeg**: DeoAI relies on FFmpeg for video and audio processing. Install it according to your operating system:
    * **Ubuntu/Debian:**
        ```bash
        sudo apt update
        sudo apt install ffmpeg
        ```
    * **macOS (with Homebrew):**
        ```bash
        brew install ffmpeg
        ```
    * **Windows:** Download a static build from [ffmpeg.org](https://ffmpeg.org/download.html) and add its `bin` directory to your system's PATH environment variable.

### Setup

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/DeoAI.git](https://github.com/your-username/DeoAI.git) # Replace with your actual repo URL
    cd DeoAI
    ```

2.  **Create and activate a virtual environment with `uv`:**
    ```bash
    uv venv
    uv shell
    ```

3.  **Install dependencies:**
    ```bash
    uv pip install -r requirements.txt
    ```
    * **For GPU support (NVIDIA CUDA):** If you have an NVIDIA GPU and CUDA installed, ensure your `torch` and `torchaudio` packages are installed with CUDA support. You might need to reinstall them:
        ```bash
        uv pip install torch torchvision torchaudio --index-url [https://download.pytorch.org/whl/cu121](https://download.pytorch.org/whl/cu121) # Adjust cu121 to your CUDA version (e.g., cu118)
        uv pip install -r requirements.txt --reinstall --no-deps # Reinstall others without re-downloading torch/torchaudio deps
        ```

## 🚀 Usage

1.  **Prepare your script:** Open `app.py` and modify the `sample_script` variable with your desired video content. Each major paragraph or distinct thought will be treated as a separate scene.

    ```python
    sample_script = """
    Scene 1: Your introductory text here.
    This can be a longer paragraph describing the first visual and audio segment.

    Scene 2: Another captivating scene description.
    Focus on what you want the AI to visualize and narrate for this segment.
    """
    ```

2.  **(Optional) Add background music:** Place an MP3 file in your project directory (e.g., `background_music.mp3`) and update the `background_music_file` variable in `app.py` with its path.

    ```python
    background_music_file = "path/to/your/background_music.mp3"
    ```

3.  **Run the application:**
    ```bash
    uv run app.py
    ```

4.  **Monitor output:** The script will print progress to the console. It will download models (once), generate audio and images, and then assemble the video.

5.  **Find your video:**
    * Generated audio files will be in the `generated_audio/` directory.
    * Generated images will be in the `generated_images/` directory.
    * The final MP4 video will be saved in the `final_videos/` directory with a timestamped filename (e.g., `faceless_video_20240630_203000.mp4`).

## 🛠️ Customization and Development

### Model Configuration

* **`voiceover_generator.py`**:
    * The `ChatterboxTTS.from_pretrained()` call automatically uses `ResembleAI/chatterbox`. You can specify a different Hugging Face model if `chatterbox-tts` supports it.
    * Device selection (`"cuda"` vs `"cpu"`) is handled automatically based on GPU availability.
* **`visual_generator.py`**:
    * Change the `model_id` variable (e.g., `"runwayml/stable-diffusion-v1-5"`) to use different Stable Diffusion models from Hugging Face.
    * Experiment with `prompt`, `num_inference_steps`, `guidance_scale`, and `negative_prompt` in `generate_visual_for_scene` for better image quality and relevance.

### Video Assembly

* **`video_assembler.py`**:
    * Adjust `fps` (frames per second) and `codec` in `write_videofile` for different video quality and file size.
    * Modify `bg_music.volumex(0.2)` to change background music volume.
    * Explore `moviepy`'s capabilities to add transitions (`crossfade`, `fadein`, `fadeout`), text overlays (`TextClip`), or more complex video effects.

## 🤝 Contributing

We welcome contributions to DeoAI! If you have ideas for improvements, new features, or bug fixes, please feel free to:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/your-feature`).
3.  Make your changes.
4.  Commit your changes (`git commit -m 'feat: Add new awesome feature'`).
5.  Push to the branch (`git push origin feature/your-feature`).
6.  Open a Pull Request.

Please ensure your code adheres to a consistent style (e.g., using `black` formatter) and includes relevant documentation.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgements

* **Chatterbox-TTS** team for their excellent Text-to-Speech library.
* **Hugging Face** for providing an incredible platform for AI models (`transformers`, `diffusers`).
* **MoviePy** and **pydub** for making video and audio manipulation in Python accessible.
* **FFmpeg** for being the backbone of multimedia processing.

---