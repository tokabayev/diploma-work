from fastapi import FastAPI, File, UploadFile, WebSocket
import os
import mimetypes
import openai
import re
import pandas as pd
from fpdf import FPDF
from pydub import AudioSegment
from moviepy.video.io.VideoFileClip import VideoFileClip
from rapidfuzz import fuzz
import json
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow requests from frontend
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

openai.api_key = "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"

app = FastAPI()

UPLOAD_DIR = "uploads"
REPORT_DIR = "reports"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)


@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        return {"message": "File uploaded successfully", "file_path": file_path}
    except Exception as e:
        return {"error": str(e)}


@app.post("/analyze/")
async def analyze_file(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        file_type, _ = mimetypes.guess_type(file_path)

        if file_type and file_type.startswith("video"):
            audio_path = extract_audio(file_path)
        elif file_type and file_type.startswith("audio"):
            audio_path = file_path
        else:
            return {"error": "Unsupported file type. Please upload a video or audio file."}

        transcript, timestamps = transcribe_audio_with_timestamps(audio_path)
        detected_words = detect_unwanted_words(transcript, timestamps)

        pdf_path = generate_pdf_report(detected_words)

        return {
            "transcript": transcript,
            "detected_words": detected_words,
            "pdf_report": pdf_path
        }

    except Exception as e:
        return {"error": str(e)}


def extract_audio(video_path):
    """Extracts audio from video."""
    audio_path = video_path.rsplit(".", 1)[0] + ".wav"
    try:
        video = VideoFileClip(video_path)
        video.audio.write_audiofile(audio_path, codec="pcm_s16le")
        return audio_path
    except Exception as e:
        raise RuntimeError(f"Failed to extract audio: {e}")


def transcribe_audio_with_timestamps(audio_path):
    """Transcribes audio with word-level timestamps using OpenAI's Whisper API."""
    import openai

    with open(audio_path, "rb") as audio_file:
        response = openai.Audio.transcribe(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json"
        )

    print(json.dumps(response, indent=4))  

    transcript = response.get("text", "").strip() 

    timestamps = []
    if "segments" in response:
        for segment in response["segments"]:
            start_time = segment.get("start", None)
            text = segment.get("text", "").lower()

            if start_time is not None and text:
                words = text.split()
                time_step = (segment["end"] - start_time) / max(len(words), 1) 

                for i, word in enumerate(words):
                    word_time = round(start_time + (i * time_step), 2)
                    timestamps.append((word, word_time))

    if not timestamps:
        print("🚨 Warning: No timestamps found! Trying segment-based timestamps instead.")
        for segment in response["segments"]:
            if "text" in segment and "start" in segment:
                words = segment["text"].lower().split()  # Basic word splitting
                start_time = segment["start"]
                for word in words:
                    timestamps.append((word, start_time))

    print(f"✅ Extracted Timestamps: {timestamps}")  # ✅ Debugging: Verify timestamps

    return transcript, timestamps  # ✅ Now timestamps won't be empty



def detect_unwanted_words(transcript, timestamps):
    """
    Detects unwanted words by breaking the transcript into smaller parts and matching them correctly.
    """
    csv_path = os.path.join(os.path.dirname(__file__), "unwanted_words.csv")

    if not os.path.exists(csv_path):
        print("Error: unwanted_words.csv file is missing!")
        return []

    # Load unwanted words and clean them
    unwanted_words = set(pd.read_csv(csv_path)["unwanted_words"].str.lower().str.strip())

    detected_words = []
    segment_size = 10  # Adjust for better detection

    print("===== DEBUG START =====")
    print(f"Unwanted words: {unwanted_words}")

    # Normalize transcript: remove punctuation & lowercase
    cleaned_transcript = re.sub(r"[^\w\s]", "", transcript.lower())

    # Normalize words with timestamps: remove punctuation
    words_with_timestamps = [(re.sub(r"[^\w\s]", "", word.lower()), time) for word, time in timestamps]

    print(f"Cleaned Transcript: {cleaned_transcript}")
    print(f"Timestamps Extracted: {words_with_timestamps}")

    num_words = len(words_with_timestamps)

    if num_words == 0:  # ✅ Fix: Ensure words exist before looping
        print("🚨 No words with timestamps found! Exiting detection.")
        return []

    for i in range(0, num_words, segment_size):
        segment = words_with_timestamps[i : i + segment_size]  # ✅ Ensure segment always exists
        print(f"🔍 Checking segment: {segment}")

        for unwanted in unwanted_words:
            for word, timecode in segment:
                # First try direct match
                if word == unwanted:
                    detected_words.append((word, timecode))
                    print(f"✅ Exact match: '{word}' at {timecode:.2f} sec")
                # Then try fuzzy match for variations
                

    print(f"Final Detected Words: {detected_words}")
    print("===== DEBUG END =====")

    return detected_words



def format_time(seconds):
    """Converts time in seconds to HH:MM:SS format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02}:{minutes:02}:{secs:02}"


def generate_pdf_report(detected_words):
    """
    Generates a PDF report with detected unwanted words and timestamps in HH:MM:SS format.
    """
    pdf_path = os.path.join(REPORT_DIR, f"report_{pd.Timestamp.now().strftime('%Y%m%d-%H%M%S')}.pdf")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Unwanted Words Report", ln=True, align='C')
    pdf.ln(10)

    if not detected_words:
        pdf.cell(200, 10, txt="No unwanted words detected.", ln=True)
    else:
        for word, timecode in detected_words:
            time_formatted = format_time(timecode)  # Convert seconds to HH:MM:SS
            pdf.cell(200, 10, txt=f"Detected: '{word}' at {time_formatted}", ln=True)

    pdf.output(pdf_path)
    return pdf_path


@app.get("/status/")
def check_status():
    return {"status": "Server is running"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text("Hello from WebSocket!")
    await websocket.close()