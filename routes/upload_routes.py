import os

from flask import Blueprint
from flask import request
from flask import jsonify

from video_processing.process_video import process_video


upload_bp = Blueprint("upload", __name__)


UPLOAD_FOLDER = "uploads/videos"


@upload_bp.route("/upload", methods=["POST"])
def upload_video():

    if "video" not in request.files:

        return jsonify({
            "error": "No video uploaded"
        })

    file = request.files["video"]

    if file.filename == "":

        return jsonify({
            "error": "Empty filename"
        })

    if not os.path.exists(UPLOAD_FOLDER):

        os.makedirs(UPLOAD_FOLDER)

    save_path = os.path.join(
        UPLOAD_FOLDER,
        file.filename
    )

    file.save(save_path)

    # -----------------------------
    # PROCESS VIDEO
    # -----------------------------
    leaderboard = process_video(save_path)

    return jsonify({
        "message": "Video processed successfully",
        "leaderboard": leaderboard
    })