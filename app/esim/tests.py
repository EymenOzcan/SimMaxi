import requests

URL = "https://api.esim-go.com/v2.4/esims"
HEADERS = {
    "X-API-Key": "NuzAFxpBhLUHQ7HNaN4sF63NlfYSs7IRxc-CszQp",
    "Accept": "application/json",
}
params = {
    "page": 1,
    "per_page": 50,
    # "country": "TR",
}

response = requests.get(URL, headers=HEADERS, params=params)
print(response.status_code)
print(response.json())
