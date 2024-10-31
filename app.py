import streamlit as st
import moviepy.editor as mp
from google.cloud import speech_v1
from google.cloud import texttospeech_v1
from google.oauth2 import service_account
import os
import tempfile
import json
import wave
import time
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

def load_credentials():
    """Load Google Cloud credentials from uploaded file."""
    credentials = None
    if 'google_credentials' not in st.session_state:
        credentials_file = st.file_uploader(
            "Upload Google Cloud credentials (JSON)", 
            type=['json'],
            help="Upload your Google Cloud service account credentials file"
        )
        if credentials_file is not None:
            credentials_json = json.loads(credentials_file.getvalue())
            credentials = service_account.Credentials.from_service_account_info(credentials_json)
            st.session_state['google_credentials'] = credentials
    else:
        credentials = st.session_state['google_credentials']
    return credentials

def get_audio_duration(audio_path):
    """Get duration of audio file in seconds."""
    with wave.open(audio_path, 'rb') as wav_file:
        frames = wav_file.getnframes()
        rate = wav_file.getframerate()
        duration = frames / float(rate)
        return duration

def extract_audio_from_video(video_path):
    """Extract audio from video file and save as WAV."""
    try:
        # Create a progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("Loading video file...")
        video = mp.VideoFileClip(video_path)
        audio = video.audio
        
        # Create temporary audio file
        temp_audio_path = tempfile.mktemp(suffix='.wav')
        
        status_text.text("Extracting audio... This may take a few minutes.")
        audio.write_audiofile(temp_audio_path, 
                            codec='pcm_s16le',  # Use PCM format
                            ffmpeg_params=["-ac", "1"],  # Convert to mono
                            logger=None)  # Disable moviepy logging
        
        progress_bar.progress(100)
        status_text.text("Audio extraction completed!")
        
        video.close()
        audio.close()
        
        return temp_audio_path
    except Exception as e:
        st.error(f"Error extracting audio: {str(e)}")
        return None

def transcribe_audio(audio_path, credentials):
    """Transcribe audio using Google Speech-to-Text."""
    try:
        # Create client with explicit credentials
        client = speech_v1.SpeechClient(credentials=credentials)
        
        # Read the audio file
        with open(audio_path, 'rb') as audio_file:
            content = audio_file.read()
        
        # Get audio file details
        with wave.open(audio_path, 'rb') as wav_file:
            sample_rate = wav_file.getframerate()
        
        # Get audio duration
        duration = get_audio_duration(audio_path)
        st.info(f"Audio duration: {duration:.2f} seconds")
        
        # Create progress elements
        progress_bar = st.progress(0)
        status_text = st.empty()
        time_text = st.empty()
        
        start_time = time.time()
        status_text.text("Starting transcription...")
        
        audio = speech_v1.RecognitionAudio(content=content)
        config = speech_v1.RecognitionConfig(
            encoding=speech_v1.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate,
            language_code="en-US",
            enable_automatic_punctuation=True,
            model='video',  # Using video model for better accuracy
            use_enhanced=True  # Using enhanced model for better quality
        )
        
        # Create a placeholder for live transcription updates
        transcript_display = st.empty()
        
        response = client.recognize(config=config, audio=audio)
        
        # Combine all transcriptions
        full_transcript = ""
        for i, result in enumerate(response.results):
            transcript = result.alternatives[0].transcript
            full_transcript += transcript + " "
            
            # Update progress
            progress = min(100, int((i + 1) / max(1, len(response.results)) * 100))
            progress_bar.progress(progress)
            
            # Update status
            elapsed_time = time.time() - start_time
            time_text.text(f"Time elapsed: {elapsed_time:.1f} seconds")
            status_text.text(f"Transcribing... ({progress}% complete)")
            
            # Show live transcript updates
            transcript_display.text_area("Current Transcript:", full_transcript, height=150)
        
        # Final status update
        progress_bar.progress(100)
        status_text.text("✅ Transcription completed!")
        time_text.text(f"Total time: {time.time() - start_time:.1f} seconds")
        
        return full_transcript.strip()
    except Exception as e:
        st.error(f"Error in transcription: {str(e)}")
        return None

def text_to_speech(text, credentials, output_path):
    """Convert text to speech using Google Cloud TTS with Journey voice."""
    try:
        client = texttospeech_v1.TextToSpeechClient(credentials=credentials)
        
        # Set up voice and audio configuration
        voice = texttospeech_v1.VoiceSelectionParams(
            name='en-US-Journey-F',  # Journey voice
            language_code='en-US'
        )
        
        audio_config = texttospeech_v1.AudioConfig(
            audio_encoding=texttospeech_v1.AudioEncoding.LINEAR16,
            speaking_rate=1.0,
            pitch=0.0
        )
        
        # Create progress elements
        status_text = st.empty()
        status_text.text("Converting text to speech...")
        
        # Create synthesis input
        synthesis_input = texttospeech_v1.SynthesisInput(text=text)
        
        # Perform text-to-speech
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        # Save the audio file
        with open(output_path, 'wb') as out:
            out.write(response.audio_content)
            
        status_text.text("✅ Text-to-speech conversion completed!")
        return True
        
    except Exception as e:
        st.error(f"Error in text-to-speech conversion: {str(e)}")
        return False

def replace_audio_in_video(video_path, new_audio_path, output_path):
    """Replace the audio in the video with new audio."""
    try:
        # Create progress elements
        status_text = st.empty()
        status_text.text("Loading video and audio files...")
        
        # Load the video
        video = mp.VideoFileClip(video_path)
        
        # Load the new audio
        new_audio = mp.AudioFileClip(new_audio_path)
        
        # Get durations
        video_duration = video.duration
        audio_duration = new_audio.duration
        
        # Adjust audio duration to match video if necessary
        if audio_duration != video_duration:
            st.warning(f"Audio duration ({audio_duration:.2f}s) differs from video duration ({video_duration:.2f}s). Adjusting audio...")
            if audio_duration > video_duration:
                # If audio is longer, trim it
                new_audio = new_audio.subclip(0, video_duration)
            else:
                # If audio is shorter, pad it with silence
                silence_duration = video_duration - audio_duration
                silence = mp.AudioClip(
                    make_frame=lambda t: 0,
                    duration=silence_duration
                )
                new_audio = mp.CompositeAudioClip([new_audio, silence.set_start(audio_duration)])
        
        status_text.text("Replacing audio...")
        
        # Set the new audio
        final_video = video.set_audio(new_audio)
        
        # Write the output file
        status_text.text("Writing final video file...")
        final_video.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile=tempfile.mktemp(suffix='.m4a'),
            remove_temp=True,
            logger=None
        )
        
        # Close the clips
        video.close()
        new_audio.close()
        final_video.close()
        
        status_text.text("✅ Video processing completed!")
        return True
        
    except Exception as e:
        st.error(f"Error replacing audio: {str(e)}")
        return False

def save_transcript(transcript, output_path):
    """Save transcript to a JSON file."""
    try:
        with open(output_path, 'w') as f:
            json.dump({
                'transcript': transcript,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }, f, indent=4)
        return True
    except Exception as e:
        st.error(f"Error saving transcript: {str(e)}")
        return False

def main():
    """
    Main function to run the Video Transcription and Audio Replacement App.
    The app performs the following steps:
    1. Displays the app title and initializes the process status indicator.
    2. Loads Google Cloud credentials.
    3. Allows the user to upload a video file.
    4. Extracts audio from the uploaded video.
    5. Transcribes the extracted audio using Google Cloud Speech-to-Text.
    6. Converts the transcription to speech using Google Cloud Text-to-Speech.
    7. Replaces the original audio in the video with the synthesized speech.
    8. Displays the final video and provides download options for the transcript, audio, and video.
    The function handles errors and updates the status indicator accordingly.
    Raises:
        Exception: If any error occurs during the processing steps.
    """
    st.title("Video Transcription and Audio Replacement App")
    
    # Add a status indicator in the sidebar
    with st.sidebar:
        st.write("📊 Process Status")
        status_indicator = st.empty()
        status_indicator.info("Waiting for credentials...")
    
    # Load credentials
    google_credentials = load_credentials()
    
    if google_credentials:
        status_indicator.success("✅ Credentials loaded")
        
        # File uploader for video
        video_file = st.file_uploader("Upload Video", type=['mp4', 'avi', 'mov'])
        
        if video_file:
            status_indicator.info("🎥 Video uploaded - Ready to process")
            
            # Save uploaded file temporarily
            temp_video_path = tempfile.mktemp(suffix='.mp4')
            with open(temp_video_path, 'wb') as f:
                f.write(video_file.read())
            
            if st.button("Start Processing"):
                try:
                    status_indicator.warning("⏳ Processing...")
                    
                    # Step 1: Extract audio
                    st.subheader("Step 1: Audio Extraction")
                    audio_path = extract_audio_from_video(temp_video_path)
                    
                    if audio_path:
                        # Step 2: Transcribe
                        st.subheader("Step 2: Transcription")
                        transcript = transcribe_audio(audio_path, google_credentials)
                        
                        if transcript:
                            # Step 3: Text-to-Speech
                            st.subheader("Step 3: Text-to-Speech Conversion")
                            tts_output_path = tempfile.mktemp(suffix='.wav')
                            if text_to_speech(transcript, google_credentials, tts_output_path):
                                st.audio(tts_output_path, format='audio/wav')
                                
                                # Step 4: Replace Audio in Video
                                st.subheader("Step 4: Replacing Audio in Video")
                                final_video_path = tempfile.mktemp(suffix='.mp4')
                                if replace_audio_in_video(temp_video_path, tts_output_path, final_video_path):
                                    st.video(final_video_path)
                                    
                                    st.subheader("Step 5: Final Results")
                                    st.success("🎉 Process completed successfully!")
                                    status_indicator.success("✅ All steps completed")
                                    
                                    # Save and offer download
                                    output_data = {
                                        'transcript': transcript,
                                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                    }
                                    
                                    # Offer downloads
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.download_button(
                                            label="📥 Download Transcript",
                                            data=json.dumps(output_data, indent=4),
                                            file_name="transcript.json",
                                            mime="application/json"
                                        )
                                    with col2:
                                        with open(tts_output_path, 'rb') as audio_file:
                                            st.download_button(
                                                label="📥 Download Audio",
                                                data=audio_file,
                                                file_name="synthesized_speech.wav",
                                                mime="audio/wav"
                                            )
                                    with col3:
                                        with open(final_video_path, 'rb') as video_file:
                                            st.download_button(
                                                label="📥 Download Video",
                                                data=video_file,
                                                file_name="final_video.mp4",
                                                mime="video/mp4"
                                            )
                                    
                                    # Clean up
                                    os.remove(temp_video_path)
                                    os.remove(audio_path)
                                    os.remove(tts_output_path)
                                    os.remove(final_video_path)
                
                except Exception as e:
                    status_indicator.error("❌ Error occurred")
                    st.error(f"An error occurred: {str(e)}")
    else:
        status_indicator.warning("⚠️ Waiting for Google Cloud credentials...")

if __name__ == "__main__":
    main()