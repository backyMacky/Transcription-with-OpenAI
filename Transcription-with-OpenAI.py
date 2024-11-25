import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QHBoxLayout,
    QComboBox, QCheckBox, QFileDialog
)
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal
import openai
import pyaudio
import wave
import os
import audioop
import pyperclip
from pynput.keyboard import Controller, Key
from dotenv import load_dotenv
import random
import string

# Load environment variables
load_dotenv()

# Initialize OpenAI API with your API key
openai.api_key = "API KEY HERE"
DEFAULT_PROMPT = "You are a skilled assistant for rewriting text."

def generate_random_string(length=16):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def paste_text(text):
    keyboard = Controller()
    pyperclip.copy(text)
    with keyboard.pressed(Key.ctrl):
        keyboard.press('v')
        keyboard.release('v')

def transcribe_audio(silence_threshold=500, silence_duration=2, max_record_time=None):
    chunk, sample_format, channels, rate = 1024, pyaudio.paInt16, 1, 44100
    filename = f"output_{generate_random_string()}.wav"
    p = pyaudio.PyAudio()
    stream = p.open(
        format=sample_format, channels=channels, rate=rate,
        frames_per_buffer=chunk, input=True
    )

    frames, silent_chunks = [], 0
    silence_limit = int(rate / chunk * silence_duration)
    max_chunks = int(rate / chunk * max_record_time) if max_record_time else None
    silence_limit_reached = False  # Initialize the flag

    while True:
        data = stream.read(chunk)
        frames.append(data)
        if audioop.rms(data, 2) < silence_threshold:
            silent_chunks += 1
        else:
            silent_chunks = 0
        if silent_chunks > silence_limit:
            silence_limit_reached = True
            break
        if max_chunks and len(frames) >= max_chunks:
            break

    stream.stop_stream()
    stream.close()
    p.terminate()

    try:
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(p.get_sample_size(sample_format))
            wf.setframerate(rate)
            wf.writeframes(b''.join(frames))

        with open(filename, "rb") as audio_file:
            transcription = openai.audio.transcriptions.create("whisper-1", file=audio_file)

        return transcription.text, silence_limit_reached

    except Exception as e:
        print(f"Error: {e}")
        return None, silence_limit_reached

    finally:
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception as e:
                print(f"Error removing file: {e}")

class TranscriptionWorker(QThread):
    transcription_done = pyqtSignal(str)
    silence_limit_reached_signal = pyqtSignal(int)  # Signal to notify when silence limit is reached

    def __init__(self, max_record_time, silence_duration):
        super().__init__()
        self.max_record_time = max_record_time
        self.silence_duration = silence_duration

    def run(self):
        transcribed_text, silence_limit_reached = transcribe_audio(
            max_record_time=self.max_record_time,
            silence_duration=self.silence_duration
        )
        self.transcription_done.emit(transcribed_text)
        if silence_limit_reached:
            self.silence_limit_reached_signal.emit(self.silence_duration)

class OverlayWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.custom_prompt = DEFAULT_PROMPT
        self.continuous_recording_stopped = False  # Initialize the flag
        self.init_ui()

    def init_ui(self):
        self.setup_window_properties()
        self.setup_layout()
        self.setup_styles()

    def setup_window_properties(self):
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setGeometry(100, 100, 600, 650)
        self.setWindowTitle("Transcription and AI Assistant")
        self.setMinimumSize(QSize(600, 650))
        self.old_pos = None

    def setup_layout(self):
        main_layout = QVBoxLayout()

        self.setup_dashboard_label(main_layout)
        self.setup_action_buttons(main_layout)
        self.setup_recording_options(main_layout)
        self.setup_prompt_upload(main_layout)
        self.setup_summary_section(main_layout)
        self.setup_control_buttons(main_layout)

        self.setLayout(main_layout)

    def setup_dashboard_label(self, layout):
        self.dashboard_label = QLabel("Transcription and AI Assistant", self)
        self.dashboard_label.setAlignment(Qt.AlignCenter)
        self.dashboard_label.setStyleSheet("font-size: 22px; font-weight: bold; margin: 20px;")
        layout.addWidget(self.dashboard_label)

    def setup_action_buttons(self, layout):
        action_button_layout = QHBoxLayout()
        self.transcribe_button = QPushButton("Start Transcription", self)
        self.transcribe_button.setFixedSize(180, 50)
        self.transcribe_button.clicked.connect(self.start_transcribing)
        action_button_layout.addWidget(self.transcribe_button)
        layout.addLayout(action_button_layout)

    def setup_recording_options(self, layout):
        options_layout = QHBoxLayout()

        # Max recording time dropdown
        self.max_time_dropdown = QComboBox(self)
        self.max_time_dropdown.addItems([
            "5 seconds", "10 seconds", "30 seconds",
            "1 minute", "2 minutes", "5 minutes", "Unlimited"
        ])
        self.max_time_dropdown.setFixedSize(180, 30)
        options_layout.addWidget(QLabel("Max Recording Time:"))
        options_layout.addWidget(self.max_time_dropdown)

        # Continuous transcription toggle
        self.continuous_toggle = QCheckBox("Continuous Transcription", self)
        self.continuous_toggle.setFixedSize(180, 30)
        options_layout.addWidget(self.continuous_toggle)

        # Continuous conversation toggle
        self.continuous_conversation = QCheckBox("Conversation", self)
        self.continuous_conversation.setFixedSize(180, 30)
        options_layout.addWidget(self.continuous_conversation)

        layout.addLayout(options_layout)

    def setup_prompt_upload(self, layout):
        prompt_layout = QHBoxLayout()

        self.prompt_label = QLabel("Current Prompt: Default", self)
        prompt_layout.addWidget(self.prompt_label)

        self.upload_prompt_button = QPushButton("Upload Prompt", self)
        self.upload_prompt_button.clicked.connect(self.upload_prompt)
        prompt_layout.addWidget(self.upload_prompt_button)

        layout.addLayout(prompt_layout)

    def setup_summary_section(self, layout):
        self.summary_label = QLabel("No transcription started.", self)
        self.summary_label.setAlignment(Qt.AlignLeft)
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet("""
            font-size: 14px; 
            margin: 20px; 
            padding: 10px; 
            background-color: #ffffff; 
            border: 1px solid #ccc; 
            border-radius: 10px;
            color: black;
        """)
        layout.addWidget(self.summary_label)

        summary_control_layout = QHBoxLayout()
        self.setup_tone_dropdown(summary_control_layout)
        self.setup_rewrite_button(summary_control_layout)
        layout.addLayout(summary_control_layout)

    def setup_tone_dropdown(self, layout):
        self.tone_dropdown = QComboBox(self)
        self.tone_dropdown.addItems(["Formal", "Casual", "Professional"])
        self.tone_dropdown.setFixedSize(180, 50)
        layout.addWidget(self.tone_dropdown)

    def setup_rewrite_button(self, layout):
        self.rewrite_button = QPushButton("Rewrite using AI", self)
        self.rewrite_button.setFixedSize(180, 50)
        self.rewrite_button.clicked.connect(self.rewrite_text)
        layout.addWidget(self.rewrite_button)

    def setup_control_buttons(self, layout):
        control_button_layout = QHBoxLayout()

        self.minimize_button = self.create_control_button("Minimize", self.minimize_window)
        self.close_button = self.create_control_button("Close", self.close_window)
        self.always_on_top_button = self.create_control_button("Always On Top", self.toggle_always_on_top)

        control_button_layout.addWidget(self.minimize_button)
        control_button_layout.addWidget(self.close_button)
        control_button_layout.addWidget(self.always_on_top_button)

        layout.addLayout(control_button_layout)

    def create_control_button(self, text, callback):
        button = QPushButton(text, self)
        button.setFixedSize(130, 40)
        button.clicked.connect(callback)
        return button

    def setup_styles(self):
        self.setStyleSheet("""
            QWidget { background-color: #242424; color: #fff; }
            QLabel { background-color: transparent; color: #fff; }
            QPushButton { background-color: #4891b4; color: #fff; border-radius: 4px; padding: 5px; }
            QPushButton:hover { background-color: #54aad3; border: 1px solid #46a2da; }
            QPushButton:pressed { background-color: #2385b4; border: 1px solid #46a2da; }
            QPushButton#close_button { background-color: #bd5355; }
            QComboBox, QCheckBox { background-color: #333; color: #fff; border: 1px solid #555; }
            QComboBox::drop-down { border: 0px; }
            QComboBox::down-arrow { image: url(down_arrow.png); width: 14px; height: 14px; }
        """)

    def start_transcribing(self):
        self.continuous_recording_stopped = False  # Reset the flag at the start
        self.summary_label.setText("Transcribing your query...")
        max_time = self.get_max_record_time()

        # Adjust silence_duration based on the continuous transcription toggle
        if self.continuous_toggle.isChecked():
            silence_duration = 20
        else:
            silence_duration = 2

        self.transcription_worker = TranscriptionWorker(max_time, silence_duration)
        self.transcription_worker.transcription_done.connect(self.on_transcription_done)
        self.transcription_worker.silence_limit_reached_signal.connect(self.on_silence_limit_reached)
        self.transcription_worker.start()

    def get_max_record_time(self):
        selected_time = self.max_time_dropdown.currentText()
        if selected_time == "Unlimited":
            return None
        elif "minute" in selected_time:
            return int(selected_time.split()[0]) * 60
        else:
            return int(selected_time.split()[0])

    def on_transcription_done(self, transcribed_text):
        self.transcribed_text = transcribed_text
        current_text = self.summary_label.text()
        new_text = f"Transcribed Text: {transcribed_text}\n"

        self.summary_label.setText(f"{current_text}\n{new_text}")

        if self.continuous_toggle.isChecked() and not self.continuous_recording_stopped:
            self.start_transcribing()
        else:
            self.continuous_recording_stopped = False  # Reset the flag for next time

    def on_silence_limit_reached(self, silence_duration):
        self.continuous_recording_stopped = True  # Stop continuous recording
        self.summary_label.setText(
            f"Silence limit of {silence_duration} seconds reached. Continuous recording stopped."
        )

    def upload_prompt(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Prompt File", "", "Text Files (*.txt)"
        )
        if file_path:
            try:
                with open(file_path, 'r') as file:
                    self.custom_prompt = file.read().strip()
                self.prompt_label.setText(
                    f"Current Prompt: Custom ({os.path.basename(file_path)})"
                )
            except Exception as e:
                self.prompt_label.setText(f"Error loading prompt: {str(e)}")
        else:
            self.custom_prompt = DEFAULT_PROMPT
            self.prompt_label.setText("Current Prompt: Default")

    def rewrite_text(self):
        if not hasattr(self, 'transcribed_text') or not self.transcribed_text:
            self.summary_label.setText("No transcribed text available to rewrite.")
            return

        tone = self.tone_dropdown.currentText()
        prompt = (
            f"{self.custom_prompt}\n\n"
            f"Rewrite the following text in a {tone} tone:\n\n{self.transcribed_text}"
        )

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.custom_prompt},
                    {
                        "role": "user",
                        "content": (
                            f"Rewrite the following text in a {tone} tone:\n\n"
                            f"{self.transcribed_text}"
                        )
                    }
                ]
            )
            self.rewritten_text = response['choices'][0]['message']['content']
            paste_text(self.rewritten_text)
            self.summary_label.setText(
                f"Rewritten Text ({tone}): {self.rewritten_text}"
            )
        except Exception as e:
            self.summary_label.setText(f"Error rewriting text: {str(e)}")

    def minimize_window(self):
        self.showMinimized()

    def close_window(self):
        self.close()

    def toggle_always_on_top(self):
        flags = self.windowFlags()
        if flags & Qt.WindowStaysOnTopHint:
            flags &= ~Qt.WindowStaysOnTopHint
            self.always_on_top_button.setText("Always On Top (Off)")
        else:
            flags |= Qt.WindowStaysOnTopHint
            self.always_on_top_button.setText("Always On Top (On)")
        self.setWindowFlags(flags)
        self.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = event.globalPos() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OverlayWindow()
    window.show()
    sys.exit(app.exec_())
