import os
import sys
import utils
import json
import threading
from queue import Queue
import random
import re


class Options(object):
    preset = {
        "BASE": {
            "script_version": "1.0.0",
            "api_version": "5.30",
            "threads": 4,
            "check_updates": True,
            "check_config": True,
            "check_config_version": True,
        }, "FILES": {
            "script_location": os.path.dirname(os.path.realpath(sys.argv[0])) + "\\",
            "data_location": "res",
            "links_file": "links.txt",
            "config_file": "config.ini",
            "log_file": "dump.log",
            "reverse_photo": False,
            "reverse_audio": False,
            "album_names": True,
        }, "OUTPUT": {
            "output_console": True,
            "output_log": False,
            "output_debug": False,
            "output_download_info": True,
        }, "AUTHORIZATION": {
            "use_token": False,
            "access_token": "",
        }
    }
    set = {}


def script_init():
    updated = 0
    if os.path.exists(Options.preset["FILES"]["config_file"]) is not True:
        utils.Cfg.create_config(Options.preset)
    Options.set = utils.Cfg.read_config(Options.preset)
    if Options.set[("BASE", "check_config")] == "True":
        updated = utils.Cfg.check_config(Options.preset)
    if updated != 0:
        Options.set = utils.Cfg.read_config(Options.preset)
    utils.Out.init_logging(Options.set)
    utils.Out.output_message(10, "Executing startup checks.")
    token = utils.Web.check_token(Options.set)
    Options.set[("AUTHORIZATION", "use_token")] = token[0]
    Options.set[("AUTHORIZATION", "access_token")] = token[1]
    if Options.set[("BASE", "check_updates")] == "True":
        utils.Saver.update_check(Options.set[("BASE", "script_version")])
    if os.path.exists(Options.set[("FILES", "data_location")]) is not True:
        utils.Out.output_message(30, "Can't locate data folder. Creating.")
        try:
            os.mkdir(Options.set[("FILES", "data_location")])
        except OSError:
            utils.Out.output_message(50, "Can't create data folder. Terminating.")
            sys.exit()
    if os.path.exists(Options.set[("FILES", "links_file")]):
        utils.Out.output_message(10, "Located links file, reading.")
    else:
        links_file = open(Options.set[("FILES", "links_file")], "w")
        links_file.close()
        utils.Out.output_message(50, "Created links file. Terminating.")
        sys.exit()
    return


def get_audios(request, full_path):
    offset = 0
    iteration = 1
    temp = []
    while True:
        if iteration != 1 and offset >= decoded_data["response"]["count"]:
            break
        request += "&offset=" + str(offset)
        offset += 6000
        try:
            json_audio_data = utils.Web.api_get(request, Options.set)
        except ConnectionError:
            utils.Out.output_message(50, "Can't connect to VK Api. Terminating.")
            sys.exit()
        decoded_data = json.loads(json_audio_data)
        if "error" not in decoded_data:
            if Options.set[("FILES", "reverse_audio")] == "True":
                decoded_data["response"]["items"] = list(reversed(decoded_data["response"]["items"]))
            for w in range(0, len(decoded_data["response"]["items"])):
                temp.append([full_path, str(re.sub('[/:*?<>|]', '', decoded_data["response"]["items"][w]["artist"]) + " - " +
                                            re.sub('[/:*?<>|]', '', decoded_data["response"]["items"][w]["title"]) + ".mp3"),
                                            decoded_data["response"]["items"][w]["url"]])
        else:
            utils.Out.output_message(50, str(decoded_data["error"]["error_msg"]))
            sys.exit()
        iteration += 1
    for obj in temp:
        q.put(obj)
    utils.Out.output_message(10, "Queue populated. Downloading audio.")
    return


def get_photos(request, full_path):
    iteration = 1
    offset = 0
    temp = []
    utils.Out.output_message(10, "Populating queue.")
    while True:
        if iteration != 1 and int(decoded_data["response"]["count"] - offset) <= 0:
            break
        request += "&offset="+str(offset)
        try:
            json_album_data = utils.Web.api_get(request, Options.set)
        except ConnectionError:
            utils.Out.output_message(50, "Can't connect to VK Api. Terminating.")
            sys.exit()
        decoded_data = json.loads(json_album_data)
        if "error" not in decoded_data:
            if Options.set[("FILES", "reverse_photo")] == "True":
                decoded_data["response"]["items"] = list(reversed(decoded_data["response"]["items"]))
            for w in range(0, len(decoded_data["response"]["items"])):
                image_data = [0, 0, 0]
                image_data[0] = full_path
                image_data[1] = str(offset+1) + ".jpg"
                try:
                    image_data[2] = decoded_data["response"]["items"][w]["photo_604"]
                except KeyError:
                    pass
                try:
                    image_data[2] = decoded_data["response"]["items"][w]["photo_807"]
                except KeyError:
                    pass
                try:
                    image_data[2] = decoded_data["response"]["items"][w]["photo_1280"]
                except KeyError:
                    pass
                try:
                    image_data[2] = decoded_data["response"]["items"][w]["photo_2560"]
                except KeyError:
                    pass
                offset += 1
                temp.append(image_data)
            iteration += 1
        else:
            utils.Out.output_message(50, str(decoded_data["error"]["error_msg"]))
            sys.exit()
    for obj in temp:
        q.put(obj)
    utils.Out.output_message(10, "Queue populated. Downloading album.")
    return


def preprocess(link):
    user_id, album_id = 0, 0
    link_type = [False, False]
    if "audios" in link:
        preprocessed = link.split("audios")
        user_id = preprocessed[1].strip()
        link_type[0] = True
    if "album" in link:
        temp = link.split("album")
        preprocessed = temp[1].split("_")
        user_id = preprocessed[0].strip()
        album_id = preprocessed[1].strip()
        link_type[1] = True
    if link_type[0]:
        full_path = Options.set[("FILES", "data_location")]
        full_path += "/" + "audios" + str(user_id)
        try:
            os.mkdir(full_path)
        except OSError:
            full_path += "_" + str(int(random.random() * 99999))
            os.mkdir(full_path)
        api_request = "audio.get?owner_id="+str(user_id)+"&need_user=0"
        get_audios(api_request, full_path)
    if link_type[1]:
        full_path = Options.set[("FILES", "data_location")]
        name_needed = False
        user_alias = user_id
        photos_request = "photos.get?owner_id="+str(user_id)
        if album_id == "0":
            photos_request += "&album_id=profile"
            full_path += "/" + str(user_alias) + "_profile"
        elif album_id == "00":
            photos_request += "&album_id=wall"
            full_path += "/" + str(user_alias) + "_wall"
        elif album_id == "000":
            photos_request += "&album_id=saved"
            full_path += "/" + str(user_alias) + "_saved"
        else:
            photos_request += "&album_id="+album_id
            name_needed = True
        if name_needed:
            if Options.set[("FILES", "album_names")] == "True":
                name_request = "photos.getAlbums?"+"owner_id="+str(user_id)+"albums_id="+str(album_id) + \
                               "&offset=0&count=1&need_system=0&need_covers=0&photo_sizes=0"
                try:
                    json_album_data = utils.Web.api_get(name_request, Options.set)
                except ConnectionError:
                    utils.Out.output_message(40, "Can't connect to VK Api. This may be caused by network issues."
                                             " Check your internet connection and try again.")
                json_parsed_data = json.loads(json_album_data)
                if "error" not in json_parsed_data:
                    full_path += "/" + re.sub('[/:*?<>|]', '', json_parsed_data["response"]["items"][0]["title"])
                else:
                    utils.Out.output_message(40, "Failed to get album album name for "+str(album_id) +
                                             ". API Error: " + json_parsed_data["error"]["error_msg"])
                    full_path += "/" + "album" + album_id
            else:
                full_path += "/" + "album" + album_id
        try:
            os.mkdir(full_path)
        except OSError:
            full_path += "_" + str(int(random.random() * 99999))
            os.mkdir(full_path)
        get_photos(photos_request, full_path)
    return

lock = threading.Lock()
q = Queue()


def task_download(file_data):
    with lock:
        log_level = 10
        utils.Web.download_file(file_data[2], file_data[0] + "/" + file_data[1])
        log_message = "Downloaded " + file_data[1]
        if Options.set[("OUTPUT", "output_download_info")] == "True":
            log_level = 20
        if Options.set[("OUTPUT", "output_debug")] == "True":
            log_message += " Thread: " + threading.current_thread().name
        utils.Out.output_message(log_level, log_message)
    return


def worker():
    while True:
        itm = q.get()
        task_download(itm)
        q.task_done()

script_init()
raw_links = open(Options.set[("FILES", "links_file")], "r").readlines()

for i in range(int(Options.set[("BASE", "threads")])):
    thread = threading.Thread(target=worker)
    thread.daemon = True
    thread.start()

for item in raw_links:
    preprocess(item)
    q.join()
    utils.Out.output_message(20, "Task completed.")