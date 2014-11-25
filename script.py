import os
import sys
import karasykUtils
import json
import time
import threading
from queue import Queue
import random
import re


class Options(object):
    preset = {
        "BASE": {
            "script_version": 0.8,
            "api_version": 5.27,
            "photo_sorting": 0,
            "threads": 4,
        }, "FILES": {
            "script_location": os.path.dirname(os.path.realpath(sys.argv[0])) + "\\",
            "data_location": "res",
            "links_file": "links.txt",
            "config_file": "config.ini",
            "log_file": "dump.log",
        }, "OUTPUT": {
            "output_console": 1,
            "output_log": 1,
            "output_debug": 0,
        }, "AUTHORIZATION": {
            "use_token": 0,
            "access_token": "",
        }
    }
    set = {}

lock = threading.Lock()
q = Queue()


def script_init():
    if os.path.exists(Options.preset["FILES"]["config_file"]):
        karasykUtils.Cfg.check_config(Options.preset)
    else:
        karasykUtils.Cfg.create_config(Options.preset)
    Options.set = karasykUtils.Cfg.read_config(Options.preset)
    karasykUtils.Out.init_logging(Options.set)
    karasykUtils.Out.output_message(10, "Executing startup checks.")
    token = karasykUtils.Web.check_token(Options.set)
    Options.set[("AUTHORIZATION", "use_token")] = token[0]
    Options.set[("AUTHORIZATION", "access_token")] = token[1]
    karasykUtils.Saver.check_version(Options.preset["BASE"]["script_version"])
    if os.path.exists(Options.set[("FILES", "data_location")]) is not True:
        karasykUtils.Out.output_message(30, "Can't locate data folder. Trying to create one.")
        try:
            os.mkdir(Options.set[("FILES", "data_location")])
        except OSError:
            karasykUtils.Out.output_message(50, "Can't create data folder. Terminating.")
            sys.exit()
    if os.path.exists(Options.set[("FILES", "links_file")]):
        karasykUtils.Out.output_message(10, "Located links file, reading.")
    else:
        karasykUtils.Out.output_message(50, "Can't locate links file. Terminating.")
        sys.exit()
    return


def parse_album(data):
    clean = data.split("_")
    api_request = karasykUtils.Saver.build_request(clean)
    current = 1
    offset = 0
    temp = []
    karasykUtils.Out.output_message(10, "Populating queue.")
    album_folder = str(int(random.random() * 99999))
    while True:
        api_request[0] += "&offset="+str(offset)
        try:
            json_album_data = karasykUtils.Web.api_get(api_request[0], Options.set)
            json_album_name = karasykUtils.Web.api_get(api_request[1], Options.set)
        except ConnectionError:
            karasykUtils.Out.output_message(50, "Can't connect to VK Api. Terminating.")
            sys.exit()
        decoded_data = [json.loads(json_album_data), json.loads(json_album_name)]
        if current is 1:
            if "error" not in decoded_data[1]:
                try:
                    album_folder = re.sub('[/:*?<>|]', '', decoded_data[1]["response"]["items"][0]["title"])
                except IndexError:
                    album_folder = str(int(time.time())) + "_" + str(int(random.random() * 9999))
            else:
                album_folder = str(int(time.time())) + "_" + str(int(random.random() * 9999))
            try:
                os.mkdir(Options.set[("FILES", "data_location")]+"/"+str(album_folder))
            except OSError:
                album_folder += "_" + str(int(random.random() * 9999))
                os.mkdir(Options.set[("FILES", "data_location")]+"/"+album_folder)
        if "error" not in decoded_data[0]:
            if int(decoded_data[0]["response"]["count"] - offset) <= 0:
                break
            for w in range(0, len(decoded_data[0]["response"]["items"])):
                image_url = [0, 1, 2]
                image_url[1] = album_folder
                image_url[2] = str(offset+1)
                try:
                    image_url[0] = decoded_data[0]["response"]["items"][w]["photo_604"]
                except KeyError:
                    pass
                try:
                    image_url[0] = decoded_data[0]["response"]["items"][w]["photo_807"]
                except KeyError:
                    pass
                try:
                    image_url[0] = decoded_data[0]["response"]["items"][w]["photo_1280"]
                except KeyError:
                    pass
                try:
                    image_url[0] = decoded_data[0]["response"]["items"][w]["photo_2560"]
                except KeyError:
                    pass
                offset += 1
                temp.append(image_url)
            if int(decoded_data[0]["response"]["count"] - offset) > 1000:
                current += 1
        else:
            karasykUtils.Out.output_message(50, str(decoded_data[0]["error"]["error_msg"]))
    for obj in temp:
        q.put(obj)
    karasykUtils.Out.output_message(10, "Queue populated. Downloading album " + str(album_folder))
    return


def download_photo(link):
    with lock:
        karasykUtils.Web.download_file(link[0], "res"+"/" + link[1] + "/" + link[2] + ".jpg")
        karasykUtils.Out.output_message(10, "Downloaded "+link[2] + ".jpg, " + "Thread: "
                                        + threading.current_thread().name)
    return


def worker():
    while True:
        itm = q.get()
        download_photo(itm)
        q.task_done()

script_init()
raw_links = open(Options.set[("FILES", "links_file")], "r").readlines()

for i in range(int(Options.set[("BASE", "threads")])):
    thread = threading.Thread(target=worker)
    thread.daemon = True
    thread.start()

for item in raw_links:
    raw = item.split("album")
    parse_album(raw[1])
    q.join()
    karasykUtils.Out.output_message(20, "Downloaded album.")