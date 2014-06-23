import time,os,sys,configparser,urllib.request,json,logging,platform

class utils(object):
	def getScriptFolder():
		return os.path.dirname(os.path.realpath(sys.argv[0])) + "\\"
	def initLogging():
		format = logging.Formatter("[%(asctime)s][%(levelname)s] %(message)s", "%d-%m-%y, %H:%M:%S")
		logger = logging.getLogger("root")
		logger.setLevel(20)
		if options.OUTPUT_LOG != 0:
			fileHandler = logging.FileHandler(options.LOG_FILE)
			fileHandler.setFormatter(format)
			logger.addHandler(fileHandler)
		if options.OUTPUT_CONSOLE != 0:
			consoleHandler = logging.StreamHandler()
			consoleHandler.setFormatter(format)
			logger.addHandler(consoleHandler)
		return
	def outputMessage(logLevel, message):
		output = logging.getLogger("root")
		output.log(logLevel, message)
		return
	def createConfig(filename):
		config = configparser.ConfigParser()
		config["setup"] = {"script_location": options.SCRIPT_LOCATION, "data_location": options.DATA_LOCATION,
		"links_file": options.LINKS_FILE, "config_file": options.CONFIG_FILE, "log_file": options.LOG_FILE}
		config["output"] = {"output_console": options.OUTPUT_CONSOLE, "output_log": options.OUTPUT_LOG}
		config["token"] = {"access_token": options.ACCESS_TOKEN, "use_token": options.USE_TOKEN}
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
			options.LOG_FILE = setup["log_file"]
		if "output" in config:
			output = config["output"]
			options.OUTPUT_CONSOLE = output["output_console"]
			options.OUTPUT_LOG = output["output_log"]
		if "token" in config:
			token = config["token"]
			options.ACCESS_TOKEN = token["access_token"]
			options.USE_TOKEN = token["use_token"]
		return
	def checkAccessToken(accessToken):
		return False #TODO
	def authorize(username, password):
		return False #TODO
	def apiGet(method, params):
		request = urllib.request.Request("https://api.vk.com/method/"+method+"?"+params+"&access_token="+options.ACCESS_TOKEN)
		return urllib.request.urlopen(request).read().decode(options.SYSTEM_ENCODING)
	def downloadImage(url, filename):
		request = urllib.request.Request(url)
		image = urllib.request.urlopen(request)
		writeable = open(filename, "wb")
		writeable.write(image.read())
		writeable.close()
		return
	def systemEncoding():
		return "cp1251" if sys.platform != "win32" or platform.release() != "8" else "utf8"	#extremely bad but working solution

class options(object):
	SCRIPT_LOCATION = utils.getScriptFolder()
	DATA_LOCATION = "res"
	LINKS_FILE = "links.txt"
	CONFIG_FILE = "config.ini"
	LOG_FILE = "dump.log"
	OUTPUT_CONSOLE = 1
	OUTPUT_LOG = 1
	ACCESS_TOKEN = ""
	USE_TOKEN = 1
	SYSTEM_ENCODING = utils.systemEncoding()
	
	
def startup():
	utils.initLogging()
	if os.path.exists(options.CONFIG_FILE):
		utils.outputMessage(20, "Config file is presented, reading.")
		utils.readConfig(options.CONFIG_FILE)
	else:
		utils.outputMessage(20, "No config file detected, creating one.")
		utils.createConfig(options.CONFIG_FILE)
	if options.ACCESS_TOKEN.strip() == "":
		utils.outputMessage(30, "Can't find your access token, you can input it manually.")
		accessToken = input("Token (press ENTER for non-token mode): ")
		if accessToken.strip() == "":
			utils.outputMessage(20, "Non-token mode enabled.")
			options.ACCESS_TOKEN = ""
			options.USE_TOKEN = 0
		else: 
			options.ACCESS_TOKEN = accessToken
	if os.path.exists(options.SCRIPT_LOCATION+options.DATA_LOCATION) != True:
		utils.outputMessage(20, "Can't find data folder, creating.")
		os.mkdir(options.SCRIPT_LOCATION+options.DATA_LOCATION)
	if os.path.exists(options.LINKS_FILE):
		utils.outputMessage(20, "Links file is present, reading.")
	else:
		utils.outputMessage(50, "Can't find links file. Terminating.")
		sys.exit()
	return

def run():
	startup()
	lines = open(options.LINKS_FILE, 'r').readlines()
	for i in range(0, len(lines)):
		raw = lines[i].split("album")
		full = raw[1].split("_")
		try:
			rawAlbumData = utils.apiGet("photos.get", "owner_id="+full[0]+"?&album_id="+full[1].rstrip("\n"))
			rawAlbumName = utils.apiGet("photos.getAlbums", "owner_id="+full[0]+"?&album_ids="+full[1].rstrip("\n"))
		except:
			utils.outputMessage(50, "Can't connect to VK API. Check your internet connection. Terminating.")
			sys.exit()
		decodedJsonData = json.loads(rawAlbumData)
		decodedJsonName = json.loads(rawAlbumName)
		if options.USE_TOKEN != 0: albumFolder = decodedJsonName["response"][0]["title"].encode(options.SYSTEM_ENCODING).decode('utf-8') #last two methods are redundant in some cases 
		if options.USE_TOKEN == 0: 
			albumFolder = i+1
		if "error" not in decodedJsonData:
			os.mkdir(options.DATA_LOCATION+"/"+str(albumFolder))
			for w in range(0,len(decodedJsonData["response"])):
				if "src_xxbig" in decodedJsonData["response"][w]:
					imageUrl = decodedJsonData["response"][w]["src_xxbig"]
				elif "src_xbig" in decodedJsonData["response"][w]:
					imageUrl = decodedJsonData["response"][w]["src_xbig"]
				else:
					imageUrl = decodedJsonData["response"][w]["src_big"]
				utils.downloadImage(imageUrl, options.DATA_LOCATION+"/"+str(albumFolder)+"/"+str(w+1)+".jpg")
			utils.outputMessage(20, "Finished "+str(albumFolder)+" album, downloaded "+str(len(decodedJsonData["response"]))+" photos.")
		else:
			utils.outputMessage(50, "API error: "+decodedJsonData["error"]["error_msg"]+". Terminating.")
			sys.exit()
	utils.outputMessage(20, "Finished all albums, terminating.")
	return
run()
