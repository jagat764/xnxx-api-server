from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route('/')
def home():
    return 'XNXX scraper API is running!'

@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('q')
    if not query:
        return jsonify({'error': 'Missing search query'}), 400

    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        url = f"https://www.xnxx.com/search/{query.replace(' ', '+')}"
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')

        videos = []
        for video in soup.select(".mozaique .thumb-block"):
            a_tag = video.find("a", href=True)
            img_tag = video.find("img")
            title = a_tag.get("title") if a_tag else "No title"
            link = f"https://www.xnxx.com{a_tag['href']}" if a_tag else None
            thumb = img_tag.get("data-src") or img_tag.get("src") if img_tag else None

            if link:
                videos.append({
                    "title": title,
                    "url": link,
                    "thumbnail": thumb
                })

        return jsonify(videos[:30])  # Limit to 30 results
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
