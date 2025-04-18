import requests

url = 'https://youtube-v311.p.rapidapi.com/search/'

querystring = {
    'q': 'Avengers',
    'part': 'snippet',
    'maxResults': '5',
    'type': 'video'
}

headers = {
    'X-RapidAPI-Key': '2eaf2be0d1msh48f50fe2afeaa3cp167efajsn2d2c5e509894',
    'X-RapidAPI-Host': 'youtube-v311.p.rapidapi.com'
}

response = requests.get(url, headers=headers, params=querystring)

print(f'Status code: {response.status_code}')
if response.status_code == 200:
    data = response.json()
    print('Success!')
    if 'items' in data:
        print(f'Found {len(data["items"])} results')
        for item in data['items'][:2]:  # Print first 2 results
            print(f"Title: {item['snippet']['title']}")
            print(f"Video ID: {item['id'].get('videoId')}")
            print(f"Thumbnail: {item['snippet']['thumbnails']['high']['url']}")
            print('---')
    else:
        print('No results found in response')
        print(data)
else:
    print(f'Error: {response.text}')