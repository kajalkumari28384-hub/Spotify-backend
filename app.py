import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
from yt_dlp import YoutubeDL

app = Flask(__name__)
CORS(app)

CLIENT_ID = "903475bacc0d49b7b66e81b34831250f"
CLIENT_SECRET = "c6e70a414b3747278db58879d8481023"

sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET
))

DOWNLOAD_FOLDER = "/tmp"

def get_spotify_track(link):
    try:
        track = sp.track(link)
        name = track['name']
        artists = ", ".join([a['name'] for a in track['artists']])
        search_query = f"{artists} - {name} official audio"
        
        # Humne extension hardcode kar diya hai M4A (best quality)
        out_path = os.path.join(DOWNLOAD_FOLDER, f"{name}.m4a")

        # === UPDATED SETTINGS (NO FFMPEG NEEDED) ===
        opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best', # Force M4A
            'outtmpl': out_path,
            # Post-processor hata diya (yehi crash kar raha tha)
            'quiet': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': True,
            'no_warnings': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'source_address': '0.0.0.0',
        }
        # =============================================

        with YoutubeDL(opts) as ydl:
            ydl.download([f"ytsearch1:{search_query}"])
            
            # File check karte hain
            if os.path.exists(out_path):
                return {"status": "success", "file_path": out_path}
            else:
                return {"status": "error", "message": "Download failed internally."}
            
    except Exception as e:
        print(f"Server Error: {e}") 
        return {"status": "error", "message": str(e)}

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    url = data.get('url')
    if not url: return jsonify({"error": "No URL"}), 400

    result = get_spotify_track(url)

    if result['status'] == 'success':
        try:
            # File bhejne ke baad delete bhi kar dete hain taaki server full na ho
            path = result['file_path']
            return send_file(path, as_attachment=True, download_name=os.path.basename(path))
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": result['message']}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
