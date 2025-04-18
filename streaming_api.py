import os
import http.client
import json
from flask import current_app

# Streaming API Configuration
RAPIDAPI_KEY = "2eaf2be0d1msh48f50fe2afeaa3cp167efajsn2d2c5e509894"
RAPIDAPI_HOST = "streaming-availability.p.rapidapi.com"

def get_show_details(show_type, show_id):
    try:
        conn = http.client.HTTPSConnection(RAPIDAPI_HOST)
        
        headers = {
            'x-rapidapi-key': RAPIDAPI_KEY,
            'x-rapidapi-host': RAPIDAPI_HOST
        }
        
        # Format the endpoint URL
        endpoint = f"/shows/{show_type}/{show_id}"
        
        # Make the request
        conn.request("GET", endpoint, headers=headers)
        
        # Get the response
        response = conn.getresponse()
        data = response.read()
        
        # Parse the JSON response
        show_data = json.loads(data.decode("utf-8"))
        
        return {
            'success': True,
            'show': show_data
        }
        
    except Exception as e:
        current_app.logger.error(f"Error fetching show details: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        if 'conn' in locals():
            conn.close()

def search_shows(query):
    try:
        conn = http.client.HTTPSConnection(RAPIDAPI_HOST)
        
        headers = {
            'x-rapidapi-key': RAPIDAPI_KEY,
            'x-rapidapi-host': RAPIDAPI_HOST
        }
        
        # URL encode the query parameter
        import urllib.parse
        encoded_query = urllib.parse.quote(query)
        
        # Format the endpoint URL with query parameters
        endpoint = f"/search/basic?country=us&services=netflix,prime,disney,hbo&output_language=en&keyword={encoded_query}&type=all"
        
        # Make the request
        conn.request("GET", endpoint, headers=headers)
        
        # Get the response
        response = conn.getresponse()
        data = response.read()
        
        # Check response status
        if response.status != 200:
            current_app.logger.error(f"Streaming API error: {response.status} - {data.decode('utf-8')}")
            return {
                'success': False,
                'error': f"API error: {response.status}"
            }
        
        # Parse the JSON response
        search_data = json.loads(data.decode("utf-8"))
        
        # Extract and process the results
        if 'result' in search_data and isinstance(search_data['result'], list):
            processed_results = []
            for show in search_data['result']:
                if show.get('type') in ['movie', 'series']:
                    processed_results.append({
                        'imdbId': show.get('imdbId', ''),
                        'title': show.get('title', ''),
                        'overview': show.get('overview', ''),
                        'posterURLs': show.get('posterURLs', {}),
                        'streamingInfo': show.get('streamingInfo', {}),
                        'firstAirYear': show.get('year', '')
                    })
            return {
                'success': True,
                'results': processed_results
            }
        else:
            return {
                'success': True,
                'results': []
            }
        
    except Exception as e:
        current_app.logger.error(f"Error searching shows: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        if 'conn' in locals():
            conn.close()