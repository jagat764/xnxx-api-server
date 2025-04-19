from flask import Flask, request, jsonify, render_template_string
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import quote_plus

app = Flask(__name__)

@app.route('/')
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
      <title>XNXX Search</title>
      <style>
        body {
          font-family: sans-serif;
          margin: 0;
          padding: 0;
          background: var(--bg);
          color: var(--text);
          transition: all 0.3s;
        }
        :root {
          --bg: #111;
          --text: #fff;
        }
        .light {
          --bg: #fff;
          --text: #000;
        }
        .container { padding: 1rem; }
        input, button {
          width: 100%;
          padding: 12px;
          font-size: 16px;
          border: none;
          border-radius: 6px;
          margin-bottom: 1rem;
        }
        .grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
          gap: 1rem;
        }
        .video {
          background: #222;
          border-radius: 8px;
          overflow: hidden;
          text-align: center;
        }
        .light .video { background: #eee; }
        .video img { width: 100%; }
        .video-info {
          font-size: 14px;
          padding: 0.5rem;
        }
        .video-info small {
          display: block;
          color: #aaa;
        }
        .pagination {
          display: flex;
          justify-content: space-between;
          gap: 1rem;
        }
        .pagination button {
          flex: 1;
          background: #333;
          color: white;
        }
        .light .pagination button {
          background: #ddd;
          color: black;
        }
        a {
          color: inherit;
          text-decoration: none;
        }
        .theme-toggle {
          position: fixed;
          top: 10px;
          right: 10px;
          width: 44px;
          height: 44px;
          background: #444;
          color: white;
          font-size: 20px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 50%;
          cursor: pointer;
          z-index: 999;
        }
        .light .theme-toggle {
          background: #ddd;
          color: black;
        }
      </style>
    </head>
    <body>
      <div class="theme-toggle" onclick="toggleTheme()">☀️</div>
      <div class="container">
        <input id="search" placeholder="Search videos..." />
        <div class="pagination">
          <button id="prev">Previous</button>
          <button id="next">Next</button>
        </div>
        <div id="results" class="grid"></div>
      </div>

      <script>
        let page = 1;
        let query = '';

        const input = document.getElementById('search');
        const results = document.getElementById('results');
        const prevBtn = document.getElementById('prev');
        const nextBtn = document.getElementById('next');

        async function loadResults() {
          if (!query) return;
          results.innerHTML = 'Loading...';
          const res = await fetch(`/api/search?q=${encodeURIComponent(query)}&page=${page}`);
          const data = await res.json();
          results.innerHTML = '';
          data.forEach(video => {
            const el = document.createElement('div');
            el.className = 'video';
            el.innerHTML = `
              <a href="/player?url=${encodeURIComponent(video.url)}">
                <img src="${video.thumbnail}" alt="">
                <div class="video-info">
                  <strong>${video.duration || 'Unknown'}</strong>
                  <small>${video.quality || ''} ${video.views || ''}</small>
                </div>
              </a>
            `;
            results.appendChild(el);
          });
        }

        input.addEventListener('keyup', e => {
          if (e.key === 'Enter') {
            query = input.value.trim();
            page = 1;
            loadResults();
          }
        });

        nextBtn.onclick = () => { page++; loadResults(); };
        prevBtn.onclick = () => { if (page > 1) { page--; loadResults(); } };

        function toggleTheme() {
          const isLight = document.body.classList.toggle('light');
          localStorage.setItem('theme', isLight ? 'light' : 'dark');
          document.querySelector('.theme-toggle').innerText = isLight ? '🌙' : '☀️';
        }

        window.onload = () => {
          const theme = localStorage.getItem('theme');
          if (theme === 'light') {
            document.body.classList.add('light');
            document.querySelector('.theme-toggle').innerText = '🌙';
          }
        };
      </script>
    </body>
    </html>
    """)

@app.route('/api/search')
def search():
    query = request.args.get('q')
    page = request.args.get('page', '1')
    if not query:
        return jsonify({'error': 'Missing query'}), 400

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        url = f"https://www.xnxx.com/search/{query.replace(' ', '+')}/{page}"
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.content, 'html.parser')

        videos = []
        for vid in soup.select(".mozaique .thumb-block"):
            a = vid.find("a", href=True)
            img = vid.find("img")
            meta = vid.select_one("p.metadata")
            raw = meta.get_text(strip=True) if meta else ""

            views = rating = duration = quality = None
            parts = re.findall(r'([\d\.]+[MK]?)|(\d+%)|(\d+min(?:\s\d+sec)?)|(\d{3,4}p)', raw)
            for p in parts:
                for i in p:
                    if i.endswith('%'): rating = i
                    elif 'min' in i: duration = i
                    elif 'p' in i: quality = i
                    else: views = i

            link = f"https://www.xnxx.com{a['href']}" if a else None
            thumb = img.get("data-src") or img.get("src") if img else None

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

@app.route('/api/video')
def api_video():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'Missing URL'}), 400

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.content, 'html.parser')

        title_tag = soup.select_one("meta[property='og:title']")
        video_tag = soup.select_one("video > source")

        title = title_tag["content"] if title_tag else "Video"
        stream = video_tag["src"] if video_tag else None

        if not stream:
            return jsonify({'error': 'Video URL not found'}), 500

        return jsonify({"title": title, "video_url": stream})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/player')
def player():
    url = request.args.get('url')
    if not url:
        return "Missing video URL", 400

    try:
        encoded_url = quote_plus(url)
        internal_api = f"{request.host_url.rstrip('/')}/api/video?url={encoded_url}"
        res = requests.get(internal_api, headers={"User-Agent": "Mozilla/5.0"})
        data = res.json()

        if "video_url" not in data or "title" not in data:
            return f"Error loading video: Invalid response format", 500

        return render_template_string("""
        <html>
        <head>
            <title>{{ title }}</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { margin: 0; background: #000; color: white; font-family: sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; }
                video { width: 100%; max-width: 800px; border: 4px solid #555; border-radius: 10px; }
            </style>
        </head>
        <body>
            <video controls autoplay>
                <source src="{{ video_url }}" type="video/mp4">
                Your browser does not support the video tag.
            </video>
        </body>
        </html>
        """, title=data["title"], video_url=data["video_url"])
    except Exception as e:
        return f"Error loading video: {e}", 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
