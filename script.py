import time,os,sys,configparser,urllib.request,json,logging,platform

class utils(object):
	def getScriptFolder():
		return os.path.dirname(os.path.realpath(sys.argv[0])) + "\\"
	def initLogging():
		format = logging.Formatter("[%(asctime)s][%(levelname)s] %(message)s", "%d-%m-%y, %H:%M:%S")
		logger = logging.getLogger("root")
		logger.setLevel(20)
		if options.preset["OUTPUT"]["OUTPUT_LOG"] != 0:
			fileHandler = logging.FileHandler(options.preset["SETUP"]["LOG_FILE"])
			fileHandler.setFormatter(format)
			logger.addHandler(fileHandler)
		if options.preset["OUTPUT"]["OUTPUT_CONSOLE"] != 0:
			consoleHandler = logging.StreamHandler()
			consoleHandler.setFormatter(format)
			logger.addHandler(consoleHandler)
		return
	def outputMessage(logLevel, message):
		output = logging.getLogger("root")
		output.log(logLevel, message)
		return
	def createConfig():
		config = configparser.ConfigParser()
		for section in options.preset.keys():
			config.add_section(section)
			for key in options.preset[section].keys():
				config.set(section, key, str(options.preset[section][key]))
		with open(options.preset["SETUP"]["CONFIG_FILE"], 'w+') as configfile:
			config.write(configfile)
		return
	def readConfig():
		config = configparser.ConfigParser()
		config.read(options.preset["SETUP"]["CONFIG_FILE"])
		rs = {}
		for opt in config:
			for n, key in enumerate(config[opt].keys()):
				rem = list(config[opt].values())
				rs[(opt, key)] = rem[n]
		for section in rs.keys():
			options.preset[section[0]][section[1]] = rs[(section[0],section[1])]
		return
	def checkAccessToken(accessToken):
		return False #TODO
	def authorize(username, password):
		return False #TODO
	def apiGet(method, params):
		request = urllib.request.Request("https://api.vk.com/method/"+method+"?"+params+"&access_token="+options.preset["AUTHORIZATION"]["ACCESS_TOKEN"])
		return urllib.request.urlopen(request).read().decode(options.preset["SETUP"]["SYSTEM_ENCODING"])
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
	preset = {
	"SETUP": {
		"SCRIPT_LOCATION":os.path.dirname(os.path.realpath(sys.argv[0])) + "\\",
		"SYSTEM_ENCODING":utils.systemEncoding(),
		"DATA_LOCATION":"res",
		"LINKS_FILE":"links.txt",
		"CONFIG_FILE":"config.ini", #NOT(!) IN CONFIG 
		"LOG_FILE":"dump.log",
	},"OUTPUT": {
		"OUTPUT_CONSOLE":1,
		"OUTPUT_LOG":1,
	},"AUTHORIZATION": {
		"ACCESS_TOKEN":"0",
		"USE_TOKEN":0
	}}

def startup():
	if os.path.exists(options.preset["SETUP"]["CONFIG_FILE"]):
		cfg = utils.readConfig()
	else:
		utils.createConfig()
	utils.initLogging()
	if options.preset["AUTHORIZATION"]["ACCESS_TOKEN"].strip() == "":
		utils.outputMessage(30, "Can't find your access token, you can input it manually.")
		accessToken = input("Token (press ENTER for non-token mode): ")
		if accessToken.strip() == "":
			utils.outputMessage(20, "Non-token mode enabled.")
			options.preset["AUTHORIZATION"]["ACCESS_TOKEN"] = ""
			options.preset["AUTHORIZATION"]["USE_TOKEN"] = 0
		else: 
			options.preset["AUTHORIZATION"]["ACCESS_TOKEN"] = accessToken
	if os.path.exists(options.preset["SETUP"]["SCRIPT_LOCATION"]+options.preset["SETUP"]["DATA_LOCATION"]) != True:
		utils.outputMessage(20, "Can't find data folder, creating.")
		os.mkdir(options.preset["SETUP"]["SCRIPT_LOCATION"]+options.preset["SETUP"]["DATA_LOCATION"])
	if os.path.exists(options.preset["SETUP"]["LINKS_FILE"]):
		utils.outputMessage(20, "Links file is present, reading.")
	else:
		utils.outputMessage(50, "Can't find links file. Terminating.")
		sys.exit()
	return

def run():
	startup()
	lines = open(options.preset["SETUP"]["LINKS_FILE"], 'r').readlines()
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
		if options.preset["AUTHORIZATION"]["USE_TOKEN"] != 0: albumFolder = decodedJsonName["response"][0]["title"].encode(options.preset["SETUP"]["SYSTEM_ENCODING"]).decode('utf-8') #last two methods are redundant in some cases 
		if options.preset["AUTHORIZATION"]["USE_TOKEN"] == 0: 
			albumFolder = i+1
		if "error" not in decodedJsonData:
			os.mkdir(options.preset["SETUP"]["DATA_LOCATION"]+"/"+str(albumFolder))
			for w in range(0,len(decodedJsonData["response"])):
				if "src_xxbig" in decodedJsonData["response"][w]:
					imageUrl = decodedJsonData["response"][w]["src_xxbig"]
				elif "src_xbig" in decodedJsonData["response"][w]:
					imageUrl = decodedJsonData["response"][w]["src_xbig"]
				else:
					imageUrl = decodedJsonData["response"][w]["src_big"]
				utils.downloadImage(imageUrl, options.preset["SETUP"]["DATA_LOCATION"]+"/"+str(albumFolder)+"/"+str(w+1)+".jpg")
			utils.outputMessage(20, "Finished "+str(albumFolder)+" album, downloaded "+str(len(decodedJsonData["response"]))+" photos.")
		else:
			utils.outputMessage(50, "API error: "+decodedJsonData["error"]["error_msg"]+". Terminating.")
			sys.exit()
	utils.outputMessage(20, "Finished all albums, terminating.")
	return
run()