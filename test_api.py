import http.client
import json
from urllib.parse import urlencode

# API Configuration
API_KEY = "2eaf2be0d1msh48f50fe2afeaa3cp167efajsn2d2c5e509894"
API_HOST = "streaming-availability.p.rapidapi.com"

# Create connection
conn = http.client.HTTPSConnection(API_HOST)

# Set up headers
headers = {
    'x-rapidapi-key': API_KEY,
    'x-rapidapi-host': API_HOST
}

# Set up query parameters
querystring = {
    'title': 'Avengers',
    'country': 'us',
    'show_type': 'all',
    'output_language': 'en',
    'limit': '5'
}

# Create the URL with query parameters
url = f"/search/title?{urlencode(querystring)}"

# Make the request
conn.request("GET", url, headers=headers)

# Get the response
response = conn.getresponse()
data = response.read()

# Decode and parse the response
try:
    decoded_data = json.loads(data.decode('utf-8'))
    print(f'Status code: {response.status}')
    
    if response.status == 200:
        print('Success!')
        if 'result' in decoded_data:
            print(f'Found {len(decoded_data["result"])} results')
            for item in decoded_data['result'][:2]:  # Print first 2 results
                print(f"Title: {item.get('title')}")
                print(f"ID: {item.get('imdbId') or item.get('tmdbId')}")
                if item.get('posterURLs'):
                    print(f"Poster: {next(iter(item['posterURLs'].values()), '')}")
                print('---')
        else:
            print('No results found in response')
            print(decoded_data)
    else:
        print(f'Error: {data.decode("utf-8")}')

except json.JSONDecodeError as e:
    print(f'Error decoding JSON response: {e}')
except Exception as e:
    print(f'An error occurred: {e}')

# Close the connection
conn.close()