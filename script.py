import time,os,sys,configparser,urllib.request,json,logging,platform

class utils(object):
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
	def apiGet(method, params):
		request = urllib.request.Request("https://api.vk.com/method/"+method+"?"+params+"&rev="+options.preset["SETUP"]["PHOTO_SORTING"]+"&v="+options.preset["SETUP"]["API_VERSION"])
		return urllib.request.urlopen(request).read().decode("utf8")
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
		"SCRIPT_VERSION":"0. beta",
		"API_VERSION":"5.23",
		"PHOTO_SORTING":"0",
	},"OUTPUT": {
		"OUTPUT_CONSOLE":1,
		"OUTPUT_LOG":1,
	},"AUTHORIZATION": {
		"ACCESS_TOKEN":"c98ff7264da760befbe1a958fb47a30449cdf062725974528f53ba1450fe7e342f66f7d93b3362387dc36",
		"USE_TOKEN":1
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
	return open(options.preset["SETUP"]["LINKS_FILE"], 'r').readlines()

def downloadAlbum(link,i):
	raw = link.split("album")
	full = raw[1].split("_")
	apiRequest = "owner_id="+str(full[0])
	specical = 0
	if full[1] == "0":
		apiRequest += "&album_id=profile"
		specical = "profile"
	elif full[1] == "00":
		apiRequest += "&album_id=wall"
		specical = "wall"
	elif full[1] == "000":
		apiRequest += "&album_id=saved"
		specical = "saved"
	else:
		apiRequest += "&album_id="+str(full[1])
	try:
		rawAlbumData = utils.apiGet("photos.get", apiRequest)
		rawAlbumName = utils.apiGet("photos.getAlbums", "owner_id="+str(full[0])+"&album_ids="+str(full[1]))
	except:
		utils.outputMessage(50, "Can't connect to VK API. Check your internet connection. Terminating.")
		sys.exit()
	decodedData = [json.loads(rawAlbumData), json.loads(rawAlbumName)]
	if options.preset["AUTHORIZATION"]["USE_TOKEN"] != 0 and specical == 0: albumFolder = decodedData[1]["response"]["items"][0]["title"]
	elif options.preset["AUTHORIZATION"]["USE_TOKEN"] == 0 and specical == 0: albumFolder = i
	elif specical != 0: albumFolder = str(full[0])+"_"+specical
	if "error" not in decodedData[0]:
		os.mkdir(options.preset["SETUP"]["DATA_LOCATION"]+"/"+str(albumFolder))
		for w in range(0,decodedData[0]["response"]["count"]):
			if "photo_2560" in decodedData[0]["response"]["items"][w]:
				imageUrl = decodedData[0]["response"]["items"][w]["photo_2560"]
			elif "photo_1280" in decodedData[0]["response"]["items"][w]:
				imageUrl = decodedData[0]["response"]["items"][w]["photo_1280"]
			elif "photo_807" in decodedData[0]["response"]["items"][w]:
				imageUrl = decodedData[0]["response"]["items"][w]["photo_807"]
			else:
				imageUrl = decodedData[0]["response"]["items"][w]["photo_604"]
			utils.downloadImage(imageUrl, options.preset["SETUP"]["DATA_LOCATION"]+"/"+str(albumFolder)+"/"+str(w+1)+".jpg")
		utils.outputMessage(20, "Finished "+str(albumFolder)+" album, downloaded "+str(decodedData[0]["response"]["count"])+" photos.")
	else:
		utils.outputMessage(50, "API error: "+decodedData[0]["error"]["error_msg"]+". Terminating.")
		sys.exit()
	return

def run():
	links = startup()
	if len(links) == 0:
		utils.outputMessage(50, "Links file is empty, terminating.")
		sys.exit()
	for n,i in enumerate(links):
		downloadAlbum(i.rstrip("\n"),n)
	return

run()