import os
import requests
from flask import current_app

# YouTube API Configuration
RAPIDAPI_KEY = "2eaf2be0d1msh48f50fe2afeaa3cp167efajsn2d2c5e509894"
RAPIDAPI_HOST = "youtube-v31.p.rapidapi.com"

def get_youtube_data(endpoint, query_params):
    try:
        url = f"https://youtube-v31.p.rapidapi.com/{endpoint}"
        
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": RAPIDAPI_HOST
        }
        
        response = requests.get(url, headers=headers, params=query_params)
        
        if response.status_code == 200:
            return {
                'success': True,
                'data': response.json()
            }
        else:
            current_app.logger.error(f"YouTube API error: {response.status_code} - {response.text}")
            return {
                'success': False,
                'error': f"API error: {response.status_code}"
            }
            
    except Exception as e:
        current_app.logger.error(f"Error accessing YouTube API: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def search_videos(query, max_results=10):
    try:
        url = "https://youtube-v31.p.rapidapi.com/search"
        
        querystring = {
            "q": query,
            "part": "snippet",
            "regionCode": "US",
            "maxResults": str(max_results),
            "order": "relevance"
        }
        
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": RAPIDAPI_HOST
        }
        
        response = requests.get(url, headers=headers, params=querystring)
        
        if response.status_code == 200:
            data = response.json()
            
            processed_videos = []
            for item in data.get('items', []):
                video_id = item['id'].get('videoId')
                if video_id:
                    processed_videos.append({
                        'id': video_id,
                        'title': item['snippet']['title'],
                        'description': item['snippet']['description'],
                        'thumbnail': item['snippet']['thumbnails']['high']['url'],
                        'channel': item['snippet']['channelTitle'],
                        'published_at': item['snippet']['publishedAt']
                    })
            
            return {
                'success': True,
                'videos': processed_videos
            }
        else:
            current_app.logger.error(f"YouTube API error: {response.status_code} - {response.text}")
            return {
                'success': False,
                'error': f"API error: {response.status_code}"
            }
            
    except Exception as e:
        current_app.logger.error(f"Error searching YouTube videos: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def get_video_details(video_id):
    try:
        url = "https://youtube-v31.p.rapidapi.com/videos"
        
        querystring = {
            "part": "contentDetails,snippet,statistics",
            "id": video_id
        }
        
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": RAPIDAPI_HOST
        }
        
        response = requests.get(url, headers=headers, params=querystring)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('items') and len(data['items']) > 0:
                item = data['items'][0]
                return {
                    'success': True,
                    'video': {
                        'id': item['id'],
                        'title': item['snippet']['title'],
                        'description': item['snippet']['description'],
                        'thumbnail': item['snippet']['thumbnails']['high']['url'],
                        'channel': item['snippet']['channelTitle'],
                        'published_at': item['snippet']['publishedAt'],
                        'views': item['statistics'].get('viewCount', 0),
                        'likes': item['statistics'].get('likeCount', 0),
                        'duration': item['contentDetails']['duration']
                    }
                }
            else:
                return {
                    'success': False,
                    'error': 'Video not found'
                }
        else:
            current_app.logger.error(f"YouTube API error: {response.status_code} - {response.text}")
            return {
                'success': False,
                'error': f"API error: {response.status_code}"
            }
            
    except Exception as e:
        current_app.logger.error(f"Error getting video details: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }