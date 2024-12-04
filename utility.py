import openai
import whisper
from openai import OpenAI
# from gtts import gTTS
import os
from dotenv import load_dotenv
load_dotenv()
# Initialize OpenAI API
# init_openai_api(".env")
openai.api_key = os.getenv('API_KEY')
client = OpenAI()
# import whisper
from werkzeug.utils import secure_filename
import os

# Load the Whisper model globally to improve efficiency
model = whisper.load_model("base")


def transcribe_audio(audio_file):
    try:
        # Resolve the absolute path to the `temp` folder
        base_dir = os.path.dirname(os.path.abspath(__file__))  # Get directory of `utility.py`
        temp_dir = os.path.join(base_dir, "temp")  # Resolve the temp directory path

        # Ensure the temp directory exists
        os.makedirs(temp_dir, exist_ok=True)

        # Save the audio file to the `temp` directory
        filename = secure_filename(audio_file.filename)
        temp_path = os.path.join(temp_dir, filename)
        audio_file.save(temp_path)
        transcription = model.transcribe(temp_path,fp16=False)
        return transcription['text']

    except Exception as e:
        return f"Error during transcription: {str(e)}"



# def get_reply(prompt):
#     response=client.chat.completions.create(
#     model="gpt-3.5-turbo",
#     messages=[
#         {"role": "user", "content": f"Q: {prompt}\nA:"}
#     ] )
#     return response.choices[0].message.content

import uuid  # For generating unique filenames
# from gtts import gTTS
import os
previous_audio_file = None
def generate_tts(text, output_dir="static/audio"):
    global previous_audio_file
    os.makedirs(output_dir, exist_ok=True)
    unique_filename = f"response_{uuid.uuid4().hex}.mp3"
    # unique_filename = f"response.mp3"
    filepath = os.path.join(output_dir, unique_filename)
    if previous_audio_file and os.path.exists(previous_audio_file):
        try:
            os.remove(previous_audio_file)
        except Exception as e:
            print(f"Error deleting file {previous_audio_file}: {e}")
    
    # Update the previous file tracker
    previous_audio_file = filepath

    with client.audio.speech.with_streaming_response.create(
        model="tts-1",
        voice="onyx",
        input=text,
    ) as response:
        response.stream_to_file(filepath)
    
    return filepath  # Return the full path of the audio file
    

    


