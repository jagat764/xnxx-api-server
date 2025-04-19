from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

@app.route('/')
def home():
    return 'XNXX scraper API is running!'

@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('q')
    page = request.args.get('page', '1')
    if not query:
        return jsonify({'error': 'Missing search query'}), 400

    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        url = f"https://www.xnxx.com/search/{query.replace(' ', '+')}/{page}"
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')

        videos = []
        for video in soup.select(".mozaique .thumb-block"):
            a_tag = video.find("a", href=True)
            img_tag = video.find("img")
            title_tag = video.select_one("p.metadata")
            raw = title_tag.get_text(strip=True) if title_tag else ""

            match = re.match(r"([\d\.]+[MK]?)\s*(\d+%)\s*([\w\s]+?)-(\d+p)", raw)
            views, rating, duration, quality = match.groups() if match else (None, None, None, None)

            link = f"https://www.xnxx.com{a_tag['href']}" if a_tag else None
            thumb = img_tag.get("data-src") or img_tag.get("src") if img_tag else None

            if link:
                videos.append({
                    "title": raw,
                    "url": link,
                    "thumbnail": thumb,
                    "views": views,
                    "rating": rating,
                    "duration": duration,
                    "quality": quality
                })

        return jsonify(videos)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/video', methods=['GET'])
def get_video_url():
    video_page_url = request.args.get('url')
    if not video_page_url:
        return jsonify({'error': 'Missing URL'}), 400

    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        response = requests.get(video_page_url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Look for the script containing the video URL
        script_tags = soup.find_all("script")
        video_url = None

        for script in script_tags:
            if script.string and "html5player.setVideoUrlHigh" in script.string:
                match = re.search(r"html5player\.setVideoUrlHigh\('(.*?)'\)", script.string)
                if match:
                    video_url = match.group(1)
                    break

        if video_url:
            return jsonify({'url': video_url})
        else:
            return jsonify({'error': 'Video URL not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
