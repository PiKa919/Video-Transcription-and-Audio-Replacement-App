# Video Transcription and Audio Replacement App

This Streamlit application allows you to upload a video file, extract its audio, transcribe the audio using Google Cloud Speech-to-Text, convert the transcription to speech using Google Cloud Text-to-Speech, and replace the original audio in the video with the synthesized speech.

## Features

- Upload a video file in various formats (e.g., MP4, AVI, MOV).
- Extract audio from the uploaded video.
- Transcribe the extracted audio using Google Cloud Speech-to-Text.
- Convert the transcription to speech using Google Cloud Text-to-Speech.
- Replace the original audio in the video with the synthesized speech.
- Download the final video, transcript, and synthesized audio.

## Prerequisites

- Python 3.7 or higher
- Google Cloud credentials with access to Speech-to-Text and Text-to-Speech APIs
- Required Python packages (listed in `requirements.txt`)

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/yourusername/video-transcription-app.git
    cd video-transcription-app
    ```

2. Create and activate a virtual environment:

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3. Install the required packages:

    ```bash
    pip install -r requirements.txt
    ```

4. Create a `.env` file in the root directory and add your Google Cloud credentials:

    ```env
    GOOGLE_APPLICATION_CREDENTIALS=path/to/your/google-credentials.json
    ```

## Usage

1. Run the Streamlit application:

    ```bash
    streamlit run app.py
    ```

2. Open your web browser and go to `http://localhost:8501`.

3. Follow the steps in the application:

    - Upload your Google Cloud credentials (JSON file).
    - Upload a video file.
    - Click the "Start Processing" button to begin the process.
    - Wait for the process to complete. The application will display the final video, transcript, and synthesized audio.
    - Download the final video, transcript, and synthesized audio using the provided download buttons.

## Troubleshooting

- Ensure that your Google Cloud credentials have the necessary permissions for Speech-to-Text and Text-to-Speech APIs.
- Make sure the `.env` file is correctly configured with the path to your Google Cloud credentials.
- If you encounter any issues, check the Streamlit application logs for error messages.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [Streamlit](https://streamlit.io/)
- [MoviePy](https://zulko.github.io/moviepy/)
- [Google Cloud Speech-to-Text](https://cloud.google.com/speech-to-text)
- [Google Cloud Text-to-Speech](https://cloud.google.com/text-to-speech)