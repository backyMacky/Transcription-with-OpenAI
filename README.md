
# Transcription and AI Assistant Tool

## Overview

This project is a **Transcription and AI Assistant** built using Python and PyQt5. It allows users to record audio, transcribe it using OpenAI's Whisper API, and rewrite the transcribed text in various tones using OpenAI's GPT model. The application includes options for custom prompts, transcription settings, and continuous transcription features.

## Key Features

- **Audio Transcription:** Record and transcribe audio using OpenAI’s Whisper API.
- **Text Rewriting:** Use GPT models to rewrite transcribed text in a selected tone (Formal, Casual, Professional).
- **Custom Prompts:** Upload custom prompts to tailor the rewriting process.
- **Continuous Transcription Mode:** Automatically start new transcription after one finishes.
- **Always on Top:** Option to keep the application on top of all windows.
- **Customizable UI:** Frictionless, minimalistic interface with a draggable, frameless window.

## Installation

### Prerequisites

1. **Python 3.6+** installed.
2. Install the required libraries by running:

```bash
pip install -r requirements.txt
```

The `requirements.txt` should include:

```plaintext
PyQt5
openai
pyaudio
wave
pyperclip
pynput
python-dotenv
```

### Environment Setup

1. Create a `.env` file in the root directory.
2. Add your OpenAI API key to the `.env` file:

```plaintext
OPENAI_API_KEY=your_openai_api_key_here
```

### Run the Application

1. Navigate to the project directory.
2. Run the application:

```bash
python main.py
```

## Usage

1. **Transcription:**
   - Click **"Start Transcription"** to begin recording audio.
   - Set the **Max Recording Time** from the dropdown menu.
   - Check the **"Continuous Transcription"** checkbox to automatically begin a new transcription when the current one finishes.
   
2. **Custom Prompts:**
   - You can upload custom prompts by clicking **"Upload Prompt"** and selecting a `.txt` file containing the desired prompt.

3. **Rewrite Transcribed Text:**
   - Select the tone of the rewriting (Formal, Casual, Professional).
   - Click **"Rewrite using AI"** to rewrite the text based on the selected tone.

4. **Window Controls:**
   - The window is draggable, frameless, and can be minimized or set to **Always on Top** mode.

## Customization

### Changing the Default Prompt

You can modify the default assistant prompt inside the code. Change the `DEFAULT_PROMPT` variable:

```python
DEFAULT_PROMPT = "You are a skilled assistant for rewriting text."
```

### Adding Additional Tones

To add more tone options, edit the `setup_tone_dropdown` method:

```python
self.tone_dropdown.addItems(["Formal", "Casual", "Professional", "New Tone"])
```

## Key Classes and Functions

### `OverlayWindow`
- **Purpose:** Main GUI class that defines the user interface, actions, and event handling for the application.

### `TranscriptionWorker`
- **Purpose:** Handles audio recording in a separate thread to ensure smooth UI performance. Signals the main window when transcription is complete.

### `transcribe_audio`
- **Purpose:** Records audio, saves it as a `.wav` file, and transcribes the audio using the OpenAI Whisper API.

### `rewrite_text`
- **Purpose:** Rewrites transcribed text using the OpenAI GPT API based on the selected tone.

### `upload_prompt`
- **Purpose:** Allows users to upload a custom prompt from a `.txt` file.

### `paste_text`
- **Purpose:** Copies rewritten text to the clipboard and simulates a paste operation using `pyperclip` and `pynput`.

## Error Handling

- **Error when rewriting text:** If there's an issue during the text rewriting, the app will display an error message on the summary label.
- **File handling errors:** Safe file handling is ensured during the recording and transcription process, with proper error logging.

## Contribution

Feel free to fork the repository and contribute to the project. Create a pull request or raise issues if you encounter any problems or have suggestions for improvements.

---

This documentation outlines the main functionalities of the Transcription and AI Assistant. For more details or support, please refer to the source code or reach out through GitHub issues.
