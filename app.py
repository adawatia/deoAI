import sys
import os
import shutil
import time # For basic timing/progress
from datetime import datetime # To create unique filenames

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QComboBox, QScrollArea, QFrame,
    QLineEdit, QFileDialog, QMessageBox, QProgressBar, QSizePolicy, QCheckBox
)
from PySide6.QtCore import Qt, QSize, QThread, Signal, Slot, QObject # Added QObject
from PySide6.QtGui import QIcon, QPixmap

# Import your custom modules (ensure these files are in the same directory)
try:
    from script_processor import ScriptProcessor
    from voiceover_generator import VoiceoverGenerator
    from visual_generator import VisualGenerator
    from video_assembler import VideoAssembler
    from PIL import Image # For placeholder image if visual generation fails
    from pydub import AudioSegment # For silent audio fallback and duration
except ImportError as e:
    QMessageBox.critical(None, "Import Error",
                         f"Missing module. Please ensure all generator files "
                         f"(script_processor.py, voiceover_generator.py, visual_generator.py, "
                         f"video_assembler.py) are in the same directory and all dependencies "
                         f"are installed.\nError: {e}")
    sys.exit(1)


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


# --- Main Application Logic (Backend) ---
class FacelessVideoAppBackend(QObject): # Inherit from QObject
    """
    This class contains the core logic for video generation,
    adapted from your CLI app to be callable by the GUI.
    It emits signals to update the GUI.
    """
    progress_update = Signal(str, int) # message, percentage
    status_update = Signal(str) # general status message
    video_generated = Signal(str) # path to final video
    error_occurred = Signal(str) # error message
    backend_ready = Signal(bool) # Indicates if all components initialized successfully

    def __init__(self):
        super().__init__() # Call QObject's constructor
        print("Initializing Faceless Video App backend components...")
        self.script_processor = None
        self.voiceover_generator = None
        self.visual_generator = None
        self.video_assembler = None
        
        try:
            self.script_processor = ScriptProcessor()
            self.voiceover_generator = VoiceoverGenerator(output_dir=GENERATED_AUDIO_DIR)
            self.visual_generator = VisualGenerator(output_dir=GENERATED_IMAGES_DIR)
            self.video_assembler = VideoAssembler(output_dir=FINAL_VIDEOS_DIR)
            print("Backend components initialized.")
            self.status_update.emit("Backend components ready.")
            self.backend_ready.emit(True)
        except Exception as e:
            error_msg = f"Failed to initialize backend components: {e}"
            self.error_occurred.emit(error_msg)
            print(f"Error initializing backend components: {e}")
            self.backend_ready.emit(False)


    def generate_video_from_script(self, raw_script: str, background_music_path: str = None):
        """
        Orchestrates the entire video generation process from a raw script.
        This method is designed to be run in a separate thread.
        """
        if not all([self.script_processor, self.voiceover_generator, self.visual_generator, self.video_assembler]):
            self.error_occurred.emit("Backend components are not fully initialized. Aborting generation.")
            return None

        self.status_update.emit("--- Starting Video Generation Process ---")
        print("\n--- Starting Video Generation Process ---")
        start_time = time.time()
        total_steps = 3 # Script processing, scene processing, video assembly

        try:
            # 1. Process the script into scenes
            self.progress_update.emit("1. Processing script into scenes...", 0)
            print("1. Processing script into scenes...")
            processed_scenes = self.script_processor.process_script(raw_script)
            if not processed_scenes:
                self.error_occurred.emit("No scenes processed from the script. Aborting video generation.")
                print("No scenes processed. Aborting video generation.")
                return None
            self.status_update.emit(f"Script processed into {len(processed_scenes)} scenes.")
            print(f"Script processed into {len(processed_scenes)} scenes.")
            self.progress_update.emit(f"Script processed into {len(processed_scenes)} scenes.", int(100/total_steps))


            scene_assets = [] # To store paths of generated audio and images for each scene

            # 2. Generate voiceovers and visuals for each scene
            self.status_update.emit("2. Generating voiceovers and visuals for each scene...")
            print("2. Generating voiceovers and visuals for each scene...")
            
            for i, scene_text in enumerate(processed_scenes):
                current_scene_progress = int((i / len(processed_scenes)) * (100/total_steps)) + int(100/total_steps)
                self.progress_update.emit(f"  -- Processing Scene {i+1}/{len(processed_scenes)} --", current_scene_progress)
                print(f"\n  -- Processing Scene {i+1}/{len(processed_scenes)} --")
                scene_start_time = time.time()

                # Generate Voiceover
                audio_path = self.voiceover_generator.generate_voiceover_for_scene(scene_text, i)
                if not audio_path:
                    print(f"  Warning: Voiceover failed for scene {i+1}. Using fallback/silent audio.")
                    # Create a silent audio here as a fallback
                    silent_audio = AudioSegment.silent(duration=2000) # Default silent duration
                    fallback_audio_path = os.path.join(TEMP_DIR, f"silent_fallback_{i}.wav")
                    silent_audio.export(fallback_audio_path, format="wav")
                    audio_path = fallback_audio_path
                self.status_update.emit(f"  Voiceover for scene {i+1} saved to: {audio_path}")
                print(f"  Voiceover for scene {i+1} saved to: {audio_path}")

                # Generate Visual
                image_path = self.visual_generator.generate_visual_for_scene(scene_text, i)
                if not image_path:
                    print(f"  Warning: Visual generation failed for scene {i+1}. Using a black placeholder image.")
                    # Create a black placeholder image if visual generation fails
                    audio_for_duration = AudioSegment.from_wav(audio_path)
                    # placeholder_duration_ms = audio_for_duration.duration_seconds * 1000 # Not needed for static image

                    placeholder_image = Image.new('RGB', (1920, 1080), color = 'black') # Standard HD resolution
                    fallback_image_path = os.path.join(TEMP_DIR, f"black_placeholder_{i}.png")
                    placeholder_image.save(fallback_image_path)
                    image_path = fallback_image_path
                self.status_update.emit(f"  Visual for scene {i+1} saved to: {image_path}")
                print(f"  Visual for scene {i+1} saved to: {image_path}")

                scene_assets.append({
                    "image_path": image_path,
                    "audio_path": audio_path
                })
                print(f"  Scene {i+1} processing finished in {time.time() - scene_start_time:.2f} seconds.")
            self.progress_update.emit("Finished generating all scene assets.", int(200/total_steps))


            # 3. Assemble the final video
            self.status_update.emit("\n3. Assembling the final video...")
            self.progress_update.emit("3. Assembling the final video...", int(200/total_steps) + 10) # Small jump
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
                self.status_update.emit(f"\n--- Video Generation Complete! ---")
                self.status_update.emit(f"Final video saved to: {os.path.abspath(final_video_path)}")
                self.video_generated.emit(os.path.abspath(final_video_path))
                print(f"\n--- Video Generation Complete! ---")
                print(f"Final video saved to: {os.path.abspath(final_video_path)}")
            else:
                self.error_occurred.emit("\n--- Video Generation Failed ---")
                print("\n--- Video Generation Failed ---")

            end_time = time.time()
            self.status_update.emit(f"Total processing time: {end_time - start_time:.2f} seconds.")
            print(f"Total processing time: {end_time - start_time:.2f} seconds.")
            self.progress_update.emit("Video generation complete!", 100) # Final 100%

            # Optional: Clean up temporary files
            # print("Cleaning up temporary assets...")
            # shutil.rmtree(TEMP_DIR)
            # print("Temporary assets removed.")

            return final_video_path
        except Exception as e:
            self.error_occurred.emit(f"An unexpected error occurred during video generation: {e}")
            print(f"An unexpected error occurred: {e}")
            self.progress_update.emit("Error during generation.", 0) # Reset progress
            return None


# --- Worker Thread for Backend Operations ---
class VideoGenerationWorker(QThread):
    """
    A QThread subclass to run the long-running video generation process
    without freezing the main GUI thread.
    """
    # Define signals that the worker will emit
    progress_update = Signal(str, int)
    status_update = Signal(str)
    video_generated = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, raw_script: str, background_music_path: str = None, parent=None):
        super().__init__(parent)
        self.raw_script = raw_script
        self.background_music_path = background_music_path
        # Create backend instance in run() method for better thread affinity
        # or ensure it's created *before* the thread starts and moved to the thread.
        # For simplicity, we'll create it here and rely on QThread's run mechanism.
        self._backend = FacelessVideoAppBackend()

        # Connect backend signals to worker signals
        self._backend.progress_update.connect(self.progress_update)
        self._backend.status_update.connect(self.status_update)
        self._backend.video_generated.connect(self.video_generated)
        self._backend.error_occurred.connect(self.error_occurred)
        # Note: backend_ready signal from backend is for GUI init, not needed by worker itself.

    def run(self):
        """
        The main entry point for the thread. This is where the long-running
        operation (video generation) is called.
        """
        self._backend.generate_video_from_script(self.raw_script, self.background_music_path)


# --- GUI Application ---
class FacelessVideoGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Faceless Video Creator")
        self.setGeometry(100, 100, 1200, 800) # Initial window size

        self.worker_thread = None # To hold the reference to the worker thread
        self.backend_initialized = False # Track if backend components are ready

        self.init_ui()
        self.init_backend() # Initialize the backend components


    def init_ui(self):
        # Central Widget and Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # --- Left Panel (Script Input and Controls) ---
        left_panel = QFrame()
        left_panel.setFrameShape(QFrame.StyledPanel)
        left_panel.setContentsMargins(10, 10, 10, 10)
        left_panel_layout = QVBoxLayout(left_panel)
        left_panel_layout.setAlignment(Qt.AlignTop) # Align content to the top

        # Script Input
        script_label = QLabel("Enter your script:")
        left_panel_layout.addWidget(script_label)
        self.script_input = QTextEdit()
        self.script_input.setPlaceholderText("Paste or type your script here...")
        left_panel_layout.addWidget(self.script_input)

        # Action Buttons (only "Generate Full Video" for now, others will be integrated into this)
        button_layout = QHBoxLayout()
        
        self.generate_video_btn = QPushButton("Generate Full Video")
        self.generate_video_btn.clicked.connect(self.start_video_generation)
        self.generate_video_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.generate_video_btn.setEnabled(False) # Disabled until backend is ready
        button_layout.addWidget(self.generate_video_btn)
        left_panel_layout.addLayout(button_layout)

        # Background Music Selection
        music_label = QLabel("Background Music (Optional):")
        left_panel_layout.addWidget(music_label)
        self.music_path_input = QLineEdit()
        self.music_path_input.setPlaceholderText("Path to background music file (e.g., .mp3)")
        self.music_path_btn = QPushButton("Browse...")
        self.music_path_btn.clicked.connect(self.browse_music)
        music_layout = QHBoxLayout()
        music_layout.addWidget(self.music_path_input)
        music_layout.addWidget(self.music_path_btn)
        left_panel_layout.addLayout(music_layout)


        # Voiceover Options (placeholders for now - Chatterbox specific)
        voice_options_label = QLabel("Voiceover Options:")
        left_panel_layout.addWidget(voice_options_label)
        self.voice_style_combo = QComboBox()
        self.voice_style_combo.addItem("Default Voice (Chatterbox)")
        # More voices would be added here if Chatterbox-TTS supports different styles/speakers
        left_panel_layout.addWidget(self.voice_style_combo)

        self.language_combo = QComboBox()
        self.language_combo.addItem("English")
        # Add more languages if Chatterbox-TTS supports them
        left_panel_layout.addWidget(self.language_combo)

        # Branding Options (placeholder for now)
        branding_label = QLabel("Branding:")
        left_panel_layout.addWidget(branding_label)
        self.logo_path_input = QLineEdit()
        self.logo_path_input.setPlaceholderText("Path to brand logo (optional)")
        self.logo_path_btn = QPushButton("Browse...")
        self.logo_path_btn.clicked.connect(self.browse_logo)
        logo_layout = QHBoxLayout()
        logo_layout.addWidget(self.logo_path_input)
        logo_layout.addWidget(self.logo_path_btn)
        left_panel_layout.addLayout(logo_layout)

        # Gemini Checkbox (adjusted based on error)
        self.use_gemini_checkbox = QCheckBox("Use AI for Script Enhancement (e.g., Gemini)")
        self.use_gemini_checkbox.setChecked(False) # Default to false
        self.use_gemini_checkbox.setEnabled(False) # Disabled until we can properly link to backend capability
        left_panel_layout.addWidget(self.use_gemini_checkbox)


        # Progress Bar and Status
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Initializing...")
        left_panel_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Initializing backend components...")
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignLeft)
        left_panel_layout.addWidget(self.status_label)


        # Add a stretch to push content to the top
        left_panel_layout.addStretch(1)
        main_layout.addWidget(left_panel, 2) # Left panel takes 2 parts of width

        # --- Right Panel (Scene Previews and Video Preview) ---
        right_panel = QFrame()
        right_panel.setFrameShape(QFrame.StyledPanel)
        right_panel_layout = QVBoxLayout(right_panel)

        # Scene Preview Area (Will be populated by processed scenes)
        scene_preview_label = QLabel("Generated Scenes (Visuals & Audio):")
        right_panel_layout.addWidget(scene_preview_label)
        self.scene_scroll_area = QScrollArea()
        self.scene_scroll_area.setWidgetResizable(True)
        self.scene_container = QWidget()
        self.scene_layout = QVBoxLayout(self.scene_container)
        self.scene_container.setLayout(self.scene_layout)
        self.scene_scroll_area.setWidget(self.scene_container)
        right_panel_layout.addWidget(self.scene_scroll_area, 3) # Takes 3 parts of height

        # Video Preview Area
        video_preview_label = QLabel("Final Video Output Path:")
        right_panel_layout.addWidget(video_preview_label)
        self.video_output_label = QLabel("No video generated yet.")
        self.video_output_label.setWordWrap(True)
        self.video_output_label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse)
        right_panel_layout.addWidget(self.video_output_label)

        # A placeholder for future video player or thumbnail
        self.video_placeholder = QLabel()
        self.video_placeholder.setText("Final video preview will appear here, or you can open the file.")
        self.video_placeholder.setAlignment(Qt.AlignCenter)
        self.video_placeholder.setMinimumSize(480, 270) # Standard 16:9 aspect ratio
        self.video_placeholder.setStyleSheet("background-color: #333; color: lightgray; border: 1px solid #555;")
        self.video_placeholder.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_panel_layout.addWidget(self.video_placeholder, 2) # Takes 2 parts of height

        main_layout.addWidget(right_panel, 3) # Right panel takes 3 parts of width

    def init_backend(self):
        """
        Initializes the backend components in a separate thread if they are long-running
        or directly if quick, and sets up error handling and readiness signals.
        """
        # We can directly instantiate the backend here as it needs to exist
        # on the main thread to connect its signals to the GUI's slots.
        # Its internal components might load heavy models, but the QObject itself is light.
        self._backend = FacelessVideoAppBackend()
        self._backend.status_update.connect(self.update_status)
        self._backend.error_occurred.connect(self.handle_error_on_init)
        self._backend.backend_ready.connect(self.set_backend_ready)

        # Initial check (can be expanded if backend initialization itself is very slow)
        # For now, rely on backend_ready signal for status update
        self.progress_bar.setFormat("Initializing backend...")
        self.progress_bar.setValue(0) # Reset or set to initial value

    @Slot(bool)
    def set_backend_ready(self, ready: bool):
        self.backend_initialized = ready
        self.generate_video_btn.setEnabled(ready)
        if ready:
            self.status_label.setText("Ready to generate video.")
            self.progress_bar.setFormat("Ready")
            self.progress_bar.setValue(0)
            # Potentially enable/disable other UI elements based on backend capabilities
            # For the Gemini checkbox, you'd need a method on ScriptProcessor to check its status
            # if hasattr(self._backend.script_processor, 'is_gemini_enabled'):
            #     self.use_gemini_checkbox.setChecked(self._backend.script_processor.is_gemini_enabled())
            # self.use_gemini_checkbox.setEnabled(self._backend.script_processor.can_use_gemini()) # Example
        else:
            self.status_label.setText("ERROR: Backend components failed to load. See console.")
            self.progress_bar.setFormat("Error")
            self.progress_bar.setValue(0)
            QMessageBox.critical(self, "Backend Error", "Backend components could not be initialized. Check console for details.")


    @Slot(str)
    def handle_error_on_init(self, message):
        """Handle errors during backend initialization."""
        self.status_label.setText(f"ERROR: {message}")
        self.generate_video_btn.setEnabled(False) # Disable button if backend is not ready
        self.progress_bar.setFormat("Error")
        self.progress_bar.setValue(0)


    def start_video_generation(self):
        if not self.backend_initialized:
            QMessageBox.warning(self, "Initialization Error", "Backend is not ready. Please wait or check for errors.")
            return

        raw_script = self.script_input.toPlainText().strip()
        if not raw_script:
            QMessageBox.warning(self, "Input Error", "Please enter a script to generate the video.")
            return

        background_music_path = self.music_path_input.text().strip()
        if background_music_path and not os.path.exists(background_music_path):
            QMessageBox.warning(self, "File Not Found",
                                f"Background music file not found: {background_music_path}\n"
                                "Please check the path or leave it empty if not using background music.")
            return
        elif not background_music_path:
            background_music_path = None # Ensure it's None if empty string

        # Disable buttons and indicate busy state
        self.generate_video_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Starting...")
        self.status_label.setText("Video generation started. Please wait...")
        self.video_output_label.setText("Generating video...")
        self.video_placeholder.setText("Generating video...")


        # Clear previous scene previews
        for i in reversed(range(self.scene_layout.count())):
            widget = self.scene_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # Create and start the worker thread
        self.worker_thread = VideoGenerationWorker(raw_script, background_music_path, parent=self)
        self.worker_thread.progress_update.connect(self.update_progress)
        self.worker_thread.status_update.connect(self.update_status)
        self.worker_thread.video_generated.connect(self.handle_video_generated)
        self.worker_thread.error_occurred.connect(self.handle_error)
        self.worker_thread.finished.connect(self.on_worker_finished) # Clean up when thread finishes

        self.worker_thread.start()

    @Slot(str, int)
    def update_progress(self, message, percentage):
        self.progress_bar.setValue(percentage)
        self.progress_bar.setFormat(f"{message} ({percentage}%)")
        # self.status_label.setText(message) # Status label already updated by status_update signal

    @Slot(str)
    def update_status(self, message):
        self.status_label.setText(message)

    @Slot(str)
    def handle_video_generated(self, video_path):
        self.video_output_label.setText(f"Final video: <a href='file:///{video_path}'>{os.path.basename(video_path)}</a>")
        self.video_output_label.setOpenExternalLinks(True)
        self.video_placeholder.setText("Video generated successfully!")
        self.status_label.setText(f"Video generation complete! Saved to: {video_path}")
        QMessageBox.information(self, "Success", f"Video generated successfully!\nPath: {video_path}")

    @Slot(str)
    def handle_error(self, message):
        self.status_label.setText(f"ERROR: {message}")
        self.video_output_label.setText("Video generation failed.")
        self.video_placeholder.setText("Video generation failed.")
        QMessageBox.critical(self, "Error", message)

    @Slot()
    def on_worker_finished(self):
        """Called when the worker thread finishes, whether successfully or with an error."""
        self.generate_video_btn.setEnabled(self.backend_initialized) # Re-enable if backend is still ready
        self.progress_bar.setFormat("Complete" if self.progress_bar.value() == 100 else "Failed")
        self.worker_thread = None # Release the reference

    def browse_music(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Select Background Music", "", "Audio Files (*.mp3 *.wav *.ogg)")
        if file_path:
            self.music_path_input.setText(file_path)

    def browse_logo(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Select Brand Logo", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)")
        if file_path:
            self.logo_path_input.setText(file_path)

    # Placeholder methods from your original GUI, now largely handled by the full generation
    def split_scenes(self):
        QMessageBox.information(self, "Info", "Scene splitting is part of the 'Generate Full Video' process.")

    def generate_voiceover(self):
        QMessageBox.information(self, "Info", "Voiceover generation is part of the 'Generate Full Video' process.")

    def generate_visuals(self):
        QMessageBox.information(self, "Info", "Visuals generation is part of the 'Generate Full Video' process.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FacelessVideoGUI()
    window.show()
    sys.exit(app.exec())