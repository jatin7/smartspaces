# Run like this:
#   cd /Users/idownard/development/smartspaces/bokeh
#   virtualenv -p python3 ../python3_env
#   source ../python3_env/bin/activate
#   pip3 install numpy pandas requests bokeh
#   bokeh serve . --allow-websocket-origin '*'

from os.path import dirname, join

import pandas as pd

from bokeh.layouts import row, widgetbox
from bokeh.models import Div
from bokeh.models.widgets import RangeSlider, Button, DataTable, TableColumn, NumberFormatter
from bokeh.io import curdoc

import base64
import json
import urllib
import pandas as pd
# import yaml
import requests
import subprocess

# make sure consumer group exists
# I can't figure out how to do this http POST in python, so I'm just doing it in bash
subprocess.Popen('curl --silent -X POST -H "Content-Type: application/vnd.kafka.v1+json" --data \'{"name":"my_consumer_instance","format": "binary", "auto.offset.reset": "earliest", "auto.commit.enable": "true"}\' "http://192.168.0.22:8082/consumers/my_consumer"', shell=True, stdout=subprocess.PIPE)
# verify consumer with this command:
# curl -X POST http://192.168.0.22:8082/consumers/my_consumer/instances/my_consumer_instance/offsets

request=urllib.request.Request('http://192.168.0.22:8082/consumers/my_consumer/instances/my_consumer_instance/topics/%2Fapps%2Fmystream1%3Amytopic')
response = urllib.request.urlopen(request)
x= response.read()
#x.bytes.decode(encoding="utf-8", errors="strict")
x2=json.loads(x)
if (len(x2) > 0):
    df = pd.DataFrame.from_dict(x2)
    df2 = base64.b64decode(df.value[len(df)-1])
    current = json.loads(df2)
    numboxes = current['numboxes']
    outfile = current['boxed_image']
else:
    numboxes = 0
    outfile="bokeh/static/images/output_1.jpg"

# url = 'http://192.168.0.22:8082/topics/%2Fapps%2Fmystream1%3Amytopic/partitions/0/messages?count=30'
# headers = {'content-type': 'application/vnd.kafka.v1+json'}
# r = requests.get(url, headers=headers)
# response = yaml.safe_load(r.text)
# if len(response) > 0:
# json_object = json.loads(base64.b64decode(response[0]["value"]))
#
# print(df)

intro = Div(text='<h1><strong>Num Boxes:</strong></h1>')
image = Div(text='<img src="bokeh/static/images/output_1.jpg"  width="450">')

# @count() annotation increments t every time cont_update is called
t=0
def update():
    global outfile, numboxes, current, t

    # make sure consumer group exists
    # I can't figure out how to do this http POST in python, so I'm just doing it in bash
    subprocess.Popen('curl --silent -X POST -H "Content-Type: application/vnd.kafka.v1+json" --data \'{"name":"my_consumer_instance","format": "binary", "auto.offset.reset": "earliest", "auto.commit.enable": "true"}\' "http://192.168.0.22:8082/consumers/my_consumer"', shell=True, stdout=subprocess.PIPE)

    t=t+1
    print ("checking for new messages")
    request=urllib.request.Request('http://192.168.0.22:8082/consumers/my_consumer/instances/my_consumer_instance/topics/%2Fapps%2Fmystream1%3Amytopic')
    response = urllib.request.urlopen(request)
    x= response.read()
    x2=json.loads(x)
    if (len(x2) > 0):
        df = pd.DataFrame.from_dict(x2)
        df2 = base64.b64decode(df.value[len(df)-1])
        current = json.loads(df2)
        numboxes = current['numboxes']
        outfile = current['boxed_image']
        intro.text = '<h1><strong>Num Boxes:</strong> ' + str(numboxes) + '<br>t='+str(t)+'<br>'+outfile+'</h1>'
        image.text = '<img src="bokeh/static/images/'+outfile+'" width="450">'
        print(numboxes)
        print(outfile)

row1 = widgetbox(intro, image)

curdoc().add_root(row(row1))
curdoc().title = "Smartspaces"
from bokeh.plotting import curdoc
curdoc().add_periodic_callback(update, 5000) #period in ms

update()
