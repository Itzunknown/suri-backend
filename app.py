from flask import Flask, request, jsonify
import requests
import re

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

@app.route('/')
def home():
    return "suriplayer backend running! Supports Terabox, Diskwala, GDrive, Direct"

@app.route('/api')
def get_direct():
    url = request.args.get('url', '').strip()
    if not url:
        return jsonify({"error": "No url"}), 400

    try:
        # 1. DIRECT MP4/MKV/M3U8 - return as is
        if url.endswith(('.mp4', '.mkv', '.m3u8', '.avi', '.mov', '.webm')) or '.mp4' in url:
            return jsonify({"direct_link": url, "type": "direct"})

        # 2. GOOGLE DRIVE
        if 'drive.google.com' in url:
            file_id = None
            match = re.search(r'/d/([A-Za-z0-9_-]+)', url) or re.search(r'id=([A-Za-z0-9_-]+)', url)
            if match:
                file_id = match.group(1)
                direct = f"https://drive.google.com/uc?export=download&id={file_id}"
                return jsonify({"direct_link": direct, "type": "gdrive", "file_id": file_id})

        # 3. DISKWALA / FILEPRESS
        if 'diskwala' in url or 'filepress' in url:
            session = requests.Session()
            resp = session.get(url, headers=HEADERS, timeout=15).text

            # Try to find direct download button link
            # Diskwala usually has fast download link in page
            m = re.search(r'"downloadUrl"\s*:\s*"([^"]+)"', resp) or \
                re.search(r'downloadUrl\s*=\s*"([^"]+)"', resp) or \
                re.search(r'https://[^"]+\.mp4[^"]*', resp) or \
                re.search(r'href="([^"]*download[^"]*)"', resp)

            if m:
                dlink = m.group(1) if hasattr(m, 'group') else m.group(0)
                dlink = dlink.replace('\\/', '/').replace('\\u002F', '/')
                return jsonify({"direct_link": dlink, "type": "diskwala"})
            else:
                return jsonify({"error": "Diskwala extraction failed, site changed", "debug": resp[:500]}), 500

        # 4. TERABOX FAMILY (terabox.com, terafileshare.com, 1024tera, etc)
        if any(x in url for x in ['terabox', 'terafile', 'nephobox', 'mirrobox', '1024tera']):
            session = requests.Session()
            # Get surl
            surl_match = re.search(r'/s/([A-Za-z0-9-_]+)', url)
            if not surl_match:
                return jsonify({"error": "Invalid terabox link"}), 400
            surl = surl_match.group(1)

            # Get file list
            list_url = f"https://www.terabox.com/share/list?app_id=250528&shorturl={surl}&root=1"
            list_resp = session.get(list_url, headers=HEADERS, timeout=15).json()

            if 'list' in list_resp and len(list_resp['list']) > 0:
                file = list_resp['list'][0]
                if 'dlink' in file:
                    return jsonify({
                        "direct_link": file['dlink'],
                        "file_name": file.get('server_filename', 'video.mp4'),
                        "type": "terabox"
                    })

            return jsonify({"error": "Terabox extraction failed", "debug": str(list_resp)[:500]}), 500

        return jsonify({"error": f"Unsupported host: {url}"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)