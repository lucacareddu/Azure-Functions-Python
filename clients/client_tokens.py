import requests

string = "Quanti tokens in 3930.30"
url = "http://localhost:7071/api/get_tokens_number/"

r = requests.get(url+string)

print(r.text)
