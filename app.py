from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
import requests
from fake_useragent import UserAgent

app = Flask(__name__)

BASE_URL = 'https://www.gequbao.com'

def generate_random_user_agent():
    ua = UserAgent()
    return ua.random

# 从搜索的数据中提取歌曲的真实的歌曲链接
def get_song_url_from_api(mp3_id):
    api_url = f'{BASE_URL}/api/play_url'
    params = {'id': mp3_id, 'json': 1}

    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()

        data = response.json()
        if data['code'] == 1:
            return data['data']['url']
        else:
            # print(f"API Error: {data['msg']}")
            return None

    except requests.exceptions.RequestException as request_exception:
        # print(f"Request Exception: {request_exception}")
        return None

# 从关键词中获取搜索数据            
def search_and_extract(keyword):
    try:
        # Base URL for the API
        api_url = f"{BASE_URL}/api/s"

        # Data to be sent in the POST request
        data = {"keyword": keyword}

        # Generating a random User-Agent
        headers_post = {
            "User-Agent": generate_random_user_agent(),
            "Referer": f"{BASE_URL}/",
        }

        # Sending a POST request to the API
        response = requests.post(api_url, data=data, headers=headers_post)
        response.raise_for_status()

        # If the request is successful, redirect to the search results page
        if response.status_code == 200:
            # Construct search_results_url
            search_results_url = f"{BASE_URL}/s/{keyword}"

            # Generating another random User-Agent for the GET request
            headers_get = {
                "User-Agent": generate_random_user_agent(),
                "Referer": search_results_url,
                "Accept-Charset": "UTF-8"
            }
            headers_get["Referer"] = headers_get["Referer"].encode("utf-8")
            # Sending a GET request to the search results URL
            search_response = requests.get(search_results_url, headers=headers_get)
            search_response.raise_for_status()

            # If the request for search results is successful, parse the HTML
            if search_response.status_code == 200:
                # Parse HTML using BeautifulSoup
                soup = BeautifulSoup(search_response.text, 'html.parser')

                # Extract song information
                songs = []
                for row in soup.select('.card.mb-1 .row'):
                    try:
                        # Extract song information
                        song_name = row.select_one('.col-5 a').text.strip()
                        artist_name = row.select_one('.text-success').text.strip()
                        # Extract and clean up download link
                        download_link = row.select_one('.col-3 a')['href'].replace('/music/', '')
                        link = get_song_url_from_api(download_link)
                        if (link != 'kuwo.cn') and (link is not None):
                            songs.append({'name': song_name, 'artist': artist_name, 'id': download_link,'link':link})                      
                    except AttributeError:
                        # Skip rows without .col-5 a element
                        continue

                return songs

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

# CORS头部设置
# def add_cors_headers(response):
#     response.headers['Access-Control-Allow-Origin'] = '*'
#     response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
#     response.headers['Access-Control-Allow-Methods'] = 'GET, POST'
#     return response

@app.route('/api', methods=['GET'])
def search():
    # 获取查询关键词
    search_keyword = request.args.get('keyword')

    if not search_keyword:
        return jsonify({"error": "Missing 'keyword' parameter"}), 400

    # 执行搜索，只获取 search_results 部分
    search_results = search_and_extract(search_keyword)

    if search_results:
        return jsonify({"data": search_results})
    else:
        return jsonify({"error": "Search failed"}), 500

# @app.route('/link', methods=['GET'])
# def get_song_url():
#     # 获取歌曲 mp3_id
#     mp3_id = request.args.get('id')

#     if not mp3_id:
#         return add_cors_headers(jsonify({"error": "Missing 'mp3_id' parameter"})), 400

#     # 获取歌曲链接
#     song_url = get_song_url_from_api(mp3_id)

#     if song_url:
#         return add_cors_headers(jsonify({"song_url": song_url}))
#     else:
#         return add_cors_headers(jsonify({"error": "Failed to get song URL"})), 500

if __name__ == "__main__":
    # 运行 Flask 应用
    app.run(debug=False)
