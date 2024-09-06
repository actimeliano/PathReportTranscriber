# Pathology Transcription App

The Pathology Transcription App is a web-based application designed to streamline the process of transcribing audio files for pathology reports. It offers features such as audio file upload, transcription using customizable templates, and text file management.

## Features

- Audio file upload (.wav, .mp3, .ogg, .flac)
- Transcription using OpenAI's Whisper model
- Customizable transcription templates
- Text file management (combine, download, delete)
- Responsive web interface

## Technologies Used

- Backend: Python, Flask
- Frontend: HTML, JavaScript, Tailwind CSS
- APIs: OpenAI API for transcription

## Prerequisites

- Python 3.7+
- OpenAI API key

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/pathology-transcription-app.git
   cd pathology-transcription-app
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Set up your OpenAI API key as an environment variable:
   ```
   export OPENAI_API_KEY='your-api-key-here'
   ```

## Usage

1. Start the Flask server:
   ```
   python main.py
   ```

2. Open a web browser and navigate to `http://localhost:5000`

3. Use the interface to upload audio files, manage templates, and transcribe files.

## Configuration

- Audio file upload directory: `uploads/`
- Transcribed text file directory: `texts/`
- Allowed audio file extensions: .wav, .mp3, .ogg, .flac

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- OpenAI for providing the Whisper model API
- Flask for the web framework
- Tailwind CSS for the UI styling