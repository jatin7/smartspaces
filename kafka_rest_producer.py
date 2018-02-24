#!/usr/bin/python
###############################################################################
# USAGE:
# cd ~/jetson-inference/build/aarch64/bin
# ./kafka_rest_producer.py -i /mapr/nuc.cluster.com/images/ -o /mapr/nuc.cluster.com/images/
#
# MapR NFS share must be mounted under /mnt/
#
# Directories are in MapR-FS.
# For example this command saves images to /mapr/nuc.cluster.com/images/:
#   ./kafka_rest_producer.py -i /mapr/nuc.cluster.com/images/ -o /mapr/nuc.cluster.com/images/
###############################################################################

import sys, getopt

import subprocess
import re
import json
import requests, base64
import os
from datetime import datetime

def main(argv):
    rawdir = ''
    boxdir = ''
    topic=''
    try:
        opts, args = getopt.getopt(argv, "i:o:h", ["rawdir=", "boxdir=", "help"])
    except getopt.GetoptError:
        print
        'test.py -i <MFS raw image directory> -o <MFS boxed image directory>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == ('-h', "--help"):
            print
            'test.py -t <stream:topic> -i <raw image dir> -o <boxed image dir>'
            sys.exit()
        elif opt in ("-i", "--rawdir"):
            rawdir = arg
        elif opt in ("-o", "--boxdir"):
            boxdir = arg
    if (rawdir == '' or boxdir == ''):
        print("Must specify rawdir (-i) and boxdir (-o)")
        sys.exit()
    if (os.access('/mnt/'+rawdir, os.W_OK) != True):
        print('Cannot write to ' + rawdir)
        sys.exit(2)
    if (os.access('/mnt/'+boxdir, os.W_OK) != True):
        print('Cannot write to ' + boxdir)
        sys.exit(2)
    print('Saving raw images to /mnt/' + rawdir)
    print('Saving boxed images to /mnt/' + boxdir)

    # lookup geolocation for lat / long feature columns
    #send_url = 'http://freegeoip.net/json'
    #r = requests.get(send_url)
    #j = json.loads(r.text)
    #lat = j['latitude']
    #lon = j['longitude']
    lat = '0'
    lon = '0'

    try:
        while True:
            timestamp=datetime.now().strftime('%Y%m%d%H%M%S')
            outfile = 'boxed-'+timestamp+'.jpg'
            #infile = 'strata2018_og_events.jpg'
            infile = 'webcam-'+timestamp+'.jpg'
            subprocess.Popen('fswebcam -d /dev/video1 -r 1280x1024 --no-banner --jpeg 85 -D 0 ' + infile + ' 2> /dev/null', shell=True, stdout=subprocess.PIPE)
            cmd = subprocess.Popen('./detectnet-console ' + infile + ' ' + outfile + ' facenet', shell=True, stdout=subprocess.PIPE)
            x = {}
            rows = []
            numboxes=0

            for line in cmd.stdout:
                if "bounding boxes detected" in line:
                    numboxes = int(re.findall('\d+', line)[0])
                if "bounding box " in line:
                    boxinfo = re.findall('\d+\.*\d*', line)
                    row = {}
                    row["boxnum"] = int(boxinfo[0])
                    row["x0"] = float(boxinfo[1])
                    row["x1"] = float(boxinfo[2])
                    row["y0"] = float(boxinfo[3])
                    row["y1"] = float(boxinfo[4])
                    row["width"] = float(boxinfo[5])
                    row["height"] = float(boxinfo[6])
                    row["size"] = row["width"] * row["height"]
                    rows.append(row)

            average_box_size = 0
            for row in rows:
                average_box_size += row["size"]
            if len(rows) > 0:
                x["average_box_size"] = average_box_size / len(rows)

            print('copying ' + infile + ' /mnt/' + rawdir)
            print('copying ' + outfile + ' /mnt/' + boxdir)
            subprocess.Popen('cp ' + infile + ' /mnt/' + rawdir + '; rm -f ' + infile, shell=True)
            subprocess.Popen('cp ' + outfile + ' /mnt/' + boxdir + '; rm -f ' + outfile, shell=True)
            x['boxes'] = rows
            x['numboxes'] = numboxes
            x['original_image'] = rawdir+infile
            x['boxed_image'] = boxdir+outfile
            x['timestamp'] = timestamp
            x['lat'] = lat
            x['lon'] = lon

            # Publish object detection result to Kafka REST service.
            url = 'http://nodea:8082/topics/%2Fapps%2Fface_detection_stream%3Acamera1'
            payload = '{"records":[{"value":"' + base64.b64encode(json.dumps(x)) + '"}]}'
            headers = {'content-type': 'application/vnd.kafka.v1+json'}
            r = requests.post(url, data=payload, headers=headers)
            print(json.dumps(x))
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main(sys.argv[1:])