import requests

url = 'http://localhost:5555/upload'
file = {'file': open('sample.pdf', 'rb')}
response = requests.post(url, files=file)
print(response.json())
