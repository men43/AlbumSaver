import logging
import configparser
import urllib.request


class Out(object):
    @staticmethod
    def init_logging(settings):
        form = logging.Formatter("[%(asctime)s][%(levelname)s] %(message)s", "%d-%m-%y, %H:%M:%S")
        logger = logging.getLogger("root")
        if int(settings[("OUTPUT", "output_debug")]) == 1:
            logger.setLevel(10)
        else:
            logger.setLevel(20)
        if settings[("OUTPUT", "output_log")] != 0:
            file_handler = logging.FileHandler(settings[("FILES", "log_file")])
            file_handler.setFormatter(form)
            logger.addHandler(file_handler)
        if settings[("OUTPUT", "output_console")] != 0:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(form)
            logger.addHandler(console_handler)
        logger.log(10, "Logging initialized")
        return

    @staticmethod
    def output_message(log_level, msg):
        output = logging.getLogger("root")
        output.log(log_level, msg)
        return


class Cfg(object):
    @staticmethod
    def create_config(settings):
        config = configparser.ConfigParser()
        for sect in settings.keys():
            config.add_section(sect)
            for key in settings[sect].keys():
                config.set(sect, key, str(settings[sect][key]))
        with open(settings["FILES"]["config_file"], "w+") as conf:
            config.write(conf)
        return

    @staticmethod
    def read_config(settings):
        config = configparser.ConfigParser()
        config.read(settings["FILES"]["config_file"])
        actual = {}
        for sect in config:
            for n, key in enumerate(config[sect].keys()):
                val = list(config[sect].values())
                actual[(sect, key)] = val[n]
        return actual

    @staticmethod
    def check_config(settings):
        cfg = configparser.ConfigParser()
        cfg.read(settings["FILES"]["config_file"])
        temp = {}
        vr = 0
        for sect in cfg:
            for n, key in enumerate(cfg[sect].keys()):
                rem = list(cfg[sect].values())
                temp[(sect, key)] = rem[n]
        if settings["BASE"]["script_version"] > float(temp[("BASE", "script_version")]):
            answer = input("Detected version mismatch. Do you want to update your config with default values? (y/n): ")
            if answer is "y":
                Cfg.fix_config(settings, 0)
        for sect in settings.keys():
            for key in settings[sect].keys():
                try:
                    temp[(sect, key)]
                except KeyError:
                    vr += 1
        if vr != 0:
            answer = input("Detected "+str(vr)+" missing elements in your config. Want to update? (y/n): ")
            if answer is "y":
                Out.output_message(10, "Fixing config.")
                Cfg.fix_config(settings, 1)
        return

    @staticmethod
    def fix_config(settings, upd):
        cfg = configparser.ConfigParser()
        override = configparser.ConfigParser()
        cfg.read(settings["FILES"]["config_file"])
        temp = {}
        for sect in cfg:
            for n, key in enumerate(cfg[sect].keys()):
                rem = list(cfg[sect].values())
                temp[(sect, key)] = rem[n]
        for section in settings.keys():
            override.add_section(section)
            for key in settings[section].keys():
                if upd is 1:
                    try:
                        override.set(section, key, str(temp[(section, key)]))
                    except KeyError:
                        override.set(section, key, str(settings[section][key]))
                elif upd is 0:
                    override.set(section, key, str(settings[section][key]))
        with open(settings["FILES"]["config_file"], "w+") as configfile:
            override.write(configfile)
        return


class Web(object):
    @staticmethod
    def api_get(req, settings):
        if settings[("AUTHORIZATION", "use_token")] == 1:
            request = urllib.request.Request("https://api.vk.com/method/"+req
                                             + "&rev="+settings[("BASE", "photo_sorting")]
                                             + "&v="+settings[("BASE", "api_version")])
        else:
            request = urllib.request.Request("https://api.vk.com/method/"+req+"&rev="
                                             + settings[("BASE", "photo_sorting")]
                                             + "&v="+settings[("BASE", "api_version")]
                                             + "&access_token="+settings[("AUTHORIZATION", "access_token")])
        return urllib.request.urlopen(request).read().decode("utf8")

    @staticmethod
    def download_file(link, filename):
        request = urllib.request.Request(link)
        try:
            file = urllib.request.urlopen(request)
            writeable = open(filename, "wb")
            writeable.write(file.read())
            writeable.close()
        except urllib.error.HTTPError as e:
            Out.output_message(40, "HTTP Error: " + str(e.code))
        return

    @staticmethod
    def check_token(opt):
        result = [0, 1]
        if opt[("AUTHORIZATION", "use_token")] == "1" and opt[("AUTHORIZATION", "access_token")].strip() == "":
            Out.output_message(30, "Can't find your access token, you can input it manually.")
            token = input("Token (press ENTER for non-token mode): ")
            if token.strip() == "":
                Out.output_message(20, "Non-token mode enabled.")
                result[0] = 0
                result[1] = ""
            else:
                result[0] = 1
                result[1] = token
        return result


class Saver(object):
    @staticmethod
    def check_version(version):
        try:
            request = urllib.request.Request("https://raw.githubusercontent.com/men43/AlbumSaver/master/version")
            latest = urllib.request.urlopen(request).read().decode("utf8")
        except ConnectionError:
            latest = 0
        if float(latest) != version:
            Out.output_message(30, "Your script is out of date. "
                                   "Get a new version here: https://github.com/men43/AlbumSaver")
        elif latest is 0:
            Out.output_message(30, "Can't check script version. You might have network issues.")
        else:
            Out.output_message(10, "Completed version check. Everything is up to date.")
        return

    @staticmethod
    def build_request(link):
        owner = "owner_id="+str(link[0])
        album = "album_id="+str(link[1])
        request = [0, 1]
        if link[1].strip() == "0":
            album = "&album_id=profile"
        elif link[1].strip() == "00":
            album = "&album_id=wall"
        elif link[1].strip() == "000":
            album = "&album_id=saved"
        request[0] = "photos.get?" + owner + "&" + album.strip()
        request[1] = "photos.getAlbums?" + owner + "&album_ids=" + str(link[1].strip())
        return request