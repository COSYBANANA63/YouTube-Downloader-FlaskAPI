from flask import Flask, jsonify, request
from flask_cors import CORS
from pytube import YouTube
from pytube.exceptions import AgeRestrictedError
import os
import re
import logging

# Create the Flask application and enable CORS
app = Flask(__name__)
CORS(app, origins=["*"])

# Logging configuration for debugging purposes
logging.basicConfig(level=logging.INFO)

# Directory to store downloaded files
download_folder = os.path.join("downloads", "youtube")
if not os.path.exists(download_folder):
    os.makedirs(download_folder)

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Welcome to the YouTube downloader API!"})

@app.route("/download", methods=["POST"])
def download_video():
    response = {"message": "", "error": False}
    video_url = request.form.get("video_url")
    resolution_or_format = request.form.get("resolution")

    # Validate YouTube URL
    if not video_url:
        response["message"] = "Please enter a YouTube video URL."
        response["error"] = True
        return jsonify(response)

    youtube_regex = (
        r"(https?://)?(www\.)?"
        r"(youtube|youtu|youtube-nocookie)\.(com|be)/"
        r"(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})"
    )
    if not re.match(youtube_regex, video_url):
        response["message"] = "Invalid YouTube URL."
        response["error"] = True
        return jsonify(response)

    # Attempt to download the YouTube video
    try:
        yt = YouTube(video_url)
        if resolution_or_format in ["highest", "1080p", "720p", "360p"]:
            streams = yt.streams.filter(progressive=True, file_extension="mp4")
            video = streams.get_highest_resolution() if resolution_or_format == "highest" else streams.filter(res=resolution_or_format).first()
            if video:
                video.download(download_folder)
                response["message"] = "Video downloaded successfully!"
            else:
                response["message"] = "Selected resolution not available."
                response["error"] = True

        elif resolution_or_format in ["mp3", "wav"]:
            audio_stream = yt.streams.get_audio_only()
            temp_file_path = audio_stream.download(download_folder)
            base, _ = os.path.splitext(temp_file_path)
            new_file_path = f"{base}.{resolution_or_format}"
            clip = AudioFileClip(temp_file_path)
            clip.write_audiofile(new_file_path)
            clip.close()
            os.remove(temp_file_path)
            response["message"] = f"Audio ({resolution_or_format.upper()}) downloaded successfully!"

        else:
            response["message"] = "Invalid resolution or format selected."
            response["error"] = True

    except AgeRestrictedError:
        response["message"] = "This video is age-restricted and cannot be downloaded."
        response["error"] = True
    except Exception as e:
        response["message"] = f"An error occurred: {e}"
        response["error"] = True

    return jsonify(response)

if __name__ == "__main__":
    app.run(host="0.0.0.0",port="5000", debug=True)
