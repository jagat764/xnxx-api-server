from flask import Flask, request, jsonify
from xnxx_api import Client
import logging

app = Flask(__name__)
client = Client()

logging.basicConfig(level=logging.DEBUG)

@app.route('/')
def home():
    return 'XNXX API is running!'

@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('q')
    if not query:
        return jsonify({'error': 'Missing search query'}), 400

    try:
        search_obj = client.search(query)

        # Debug: list all available attributes
        info = {}
        for attr in dir(search_obj):
            if not attr.startswith('_'):
                try:
                    value = getattr(search_obj, attr)
                    info[attr] = str(value)
                except Exception as e:
                    info[attr] = f"Error accessing attribute: {e}"

        app.logger.debug(f"Search object info: {info}")
        return jsonify(info)

    except Exception as e:
        app.logger.error(f"Search error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/video', methods=['GET'])
def get_video():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'Missing video URL'}), 400

    try:
        video = client.get_video(url)
        return jsonify({
            'title': video.title,
            'author': video.author,
            'duration': video.length,
            'views': video.views,
            'likes': video.likes,
            'thumbnail': video.thumbnail_url,
            'tags': video.tags,
            'video_url': video.content_url
        })
    except Exception as e:
        app.logger.error(f"Video error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
