from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import re

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "suriplayer backend running! Supports Terabox, Diskwala, GDrive, Direct"

@app.route('/api')
def get_direct():
    terabox_url = request.args.get('url')
    if not terabox_url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        # Extract surl
        match = re.search(r'/s/([A-Za-z0-9-_]+)', terabox_url)
        if not match:
            return jsonify({"error": "Invalid Terabox URL"}), 400

        surl = match.group(1)

        # Terabox API - New working method
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.terabox.com/'
        }

        # Get file info
        api_url = f"https://www.terabox.com/api/shorturlinfo?app_id=250528&shorturl={surl}&root=1"
        resp = requests.get(api_url, headers=headers, timeout=15)
        data = resp.json()

        if data.get('errno')!= 0:
            # Try alternative method
            api_url2 = f"https://terabox.hnn.workers.dev/api?url={terabox_url}"
            try:
                resp2 = requests.get(api_url2, timeout=15)
                return jsonify(resp2.json())
            except:
                return jsonify({"error": "Terabox blocked, try again", "details": data}), 500

        # Extract direct link
        file_list = data.get('list', [])
        if file_list and len(file_list) > 0:
            file_info = file_list[0]
            dlink = file_info.get('dlink', '')

            if dlink:
                return jsonify({
                    "direct_link": dlink,
                    "url": dlink,
                    "filename": file_info.get('server_filename', 'video.mp4'),
                    "size": file_info.get('size', 0)
                })

        return jsonify({"error": "No file found", "data": data}), 404

    except Exception as e:
        return jsonify({"error": str(e), "url": terabox_url}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
