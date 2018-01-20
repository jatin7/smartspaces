import base64
import requests
import yaml
url = 'http://192.168.0.22:8082/topics/%2Fapps%2Fmystream1%3Amytopic/partitions/0/messages?count=30'
headers = {'content-type': 'application/vnd.kafka.v1+json'}
r = requests.get(url, headers=headers)
x = base64.b64decode( (yaml.safe_load(r.text)[0])["value"])
print(x)
