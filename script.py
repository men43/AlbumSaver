import time,os,sys,configparser,urllib.request,json

class utils(object):
	def getScriptFolder():
		return os.path.dirname(os.path.realpath(sys.argv[0])) + "\\"
	def outputMessage(messageType, message):
		cur = time.localtime()
		print("[" + str(cur.tm_hour) + ":" + str(cur.tm_min) + ":" + str(cur.tm_sec) + "]" + messageType + " " + message)
		return
	def readLinks():
		links = open(options.LINKS_FILE, 'r')
		result = links.readlines()
		return result
	def createConfig(filename):
		config = configparser.ConfigParser()
		config["setup"] = {"script_location": options.SCRIPT_LOCATION, "data_location": options.DATA_LOCATION,
		"links_file": options.LINKS_FILE, "config_file": options.CONFIG_FILE}
		config["output"] = {"output_console": options.OUTPUT_CONSOLE}
		config["token"] = {"access_token": options.ACCESS_TOKEN}
		with open(filename, 'w+') as configfile:
			config.write(configfile)
		return
	def readConfig(filename):
		config = configparser.ConfigParser()
		config.read(filename)
		if "setup" in config:
			setup = config["setup"]
			options.SCRIPT_LOCATION = setup["script_location"]
			options.DATA_LOCATION = setup["data_location"]
			options.LINKS_FILE = setup["links_file"]
			options.CONFIG_FILE = setup["config_file"]
		if "output" in config:
			output = config["output"]
			options.OUTPUT_CONSOLE = output["output_console"]
		if "token" in config:
			token = config["token"]
			options.ACCESS_TOKEN = token["access_token"]
		return
	def apiGet(method, params):
		request = urllib.request.Request("https://api.vk.com/method/"+method+"?"+params+"&access_token="+options.ACCESS_TOKEN)
		page = urllib.request.urlopen(request)
		return page.read().decode('cp1251')
	def downloadImage(url, filename):
		request = urllib.request.Request(url)
		image = urllib.request.urlopen(request)
		writeable = open(filename, "wb")
		writeable.write(image.read())
		writeable.close()
		return

class messageType(object):
	TYPE_INFO = "[INFO]"
	TYPE_NOTICE = "[NOTICE]"
	TYPE_WARNING = "[WARNING]"
	TYPE_ERROR = "[ERROR]"
	TYPE_FATAL = "[RUNTIME_ERROR]"

class options(object):
	SCRIPT_LOCATION = utils.getScriptFolder()
	DATA_LOCATION = "res"
	LINKS_FILE = "links.txt"
	CONFIG_FILE = "config.ini"
	OUTPUT_CONSOLE = 1
	ACCESS_TOKEN = ""
	
def startup():
	if os.path.exists(options.CONFIG_FILE):
		utils.outputMessage(messageType.TYPE_INFO, "Config file is present, reading.")
		utils.readConfig(options.CONFIG_FILE)
	else:
		utils.outputMessage(messageType.TYPE_WARNING, "No config file detected, creating one.")
		utils.createConfig(options.CONFIG_FILE)
	if os.path.exists(options.SCRIPT_LOCATION+options.DATA_LOCATION) != True:
		utils.outputMessage(messageType.TYPE_NOTICE, "Can't find data folder, creating.")
		os.mkdir(options.SCRIPT_LOCATION+options.DATA_LOCATION)
	if os.path.exists(options.LINKS_FILE):
		utils.outputMessage(messageType.TYPE_INFO, "Links file is present, reading.")
	else:
		utils.outputMessage(messageType.TYPE_FATAL, "Can't find links file. Terminating.")
		sys.exit()
	return

def run():
	startup()
	lines = utils.readLinks()
	for i in range(0, len(lines)):
		raw = lines[i].split("album")
		full = raw[1].split("_")
		rawAlbumData = utils.apiGet("photos.get", "owner_id="+full[0]+"?&album_id="+full[1].rstrip("\n"))
		rawAlbumName = utils.apiGet("photos.getAlbums", "owner_id="+full[0]+"?&album_id="+full[1].rstrip("\n")+"&rev=1")
		decodedJsonData = json.loads(rawAlbumData)
		decodedJsonName = json.loads(rawAlbumName)
		os.mkdir(options.DATA_LOCATION+"/"+decodedJsonName["response"][0]["title"])
		for w in range(0,len(decodedJsonData["response"])):
			utils.downloadImage(decodedJsonData["response"][w]["src_big"], "res/"+decodedJsonName["response"][0]["title"]+"/"+str(w+1)+".jpg")
	return
run()