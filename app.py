import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
from yt_dlp import YoutubeDL

app = Flask(__name__)
CORS(app)

# Credentials (Environment variables se bhi le sakte hain, par abhi hardcode theek hai)
CLIENT_ID = "903475bacc0d49b7b66e81b34831250f"
CLIENT_SECRET = "c6e70a414b3747278db58879d8481023"

sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET
))

# Cloud par /tmp folder safe hota hai temporary files ke liye
DOWNLOAD_FOLDER = "/tmp"

def get_spotify_track(link):
    try:
        track = sp.track(link)
        name = track['name']
        artists = ", ".join([a['name'] for a in track['artists']])
        search_query = f"{artists} - {name} official audio"
        
        # Output template for /tmp
        out_path = os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s')

        opts = {
            'format': 'bestaudio/best',
            'outtmpl': out_path,
            'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '320'}],
            'quiet': True,
            'noplaylist': True
        }

        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{search_query}", download=True)
            filename = ydl.prepare_filename(info['entries'][0])
            final_filename = filename.replace(".webm", ".mp3").replace(".m4a", ".mp3")
            return {"status": "success", "file_path": final_filename}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    url = data.get('url')
    if not url: return jsonify({"error": "No URL"}), 400

    result = get_spotify_track(url)

    if result['status'] == 'success':
        try:
            return send_file(result['file_path'], as_attachment=True, download_name=os.path.basename(result['file_path']))
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": result['message']}), 500

if __name__ == '__main__':
    # Cloud variable PORT use karega, nahi to 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
