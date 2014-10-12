import time,os,sys,configparser,urllib.request,json,logging,platform

class utils(object):
	def initLogging():
		format = logging.Formatter("[%(asctime)s][%(levelname)s] %(message)s", "%d-%m-%y, %H:%M:%S")
		logger = logging.getLogger("root")
		logger.setLevel(20)
		if options.preset["OUTPUT"]["output_log"] != 0:
			fileHandler = logging.FileHandler(options.preset["SETUP"]["log_file"])
			fileHandler.setFormatter(format)
			logger.addHandler(fileHandler)
		if options.preset["OUTPUT"]["output_console"] != 0:
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
		with open(options.preset["SETUP"]["config_file"], 'w+') as configfile:
			config.write(configfile)
		return
	def readConfig():
		config = configparser.ConfigParser()
		config.read(options.preset["SETUP"]["config_file"])
		rs = {}
		for opt in config:
			for n, key in enumerate(config[opt].keys()):
				rem = list(config[opt].values())
				rs[(opt, key)] = rem[n]
		for section in rs.keys():
			options.preset[section[0]][section[1]] = rs[(section[0],section[1])]
		return
	def checkConfig():
		config = configparser.ConfigParser()
		config.read(options.preset["SETUP"]["config_file"])
		mismatch = 0
		temp = {}
		vr = {}
		for opt in config:
			for n, key in enumerate(config[opt].keys()):
				rem = list(config[opt].values())
				temp[(opt, key)] = rem[n]
		if((options.preset["SETUP"]["script_version"].replace(".",",")) > temp[("SETUP","script_version")].replace(".",",")):
			mismatch = 1
		if(options.preset["SETUP"]["script_version"].replace(".",",") < temp[("SETUP","script_version")].replace(".",",")):
			mismatch = 2
		for opt in options.preset.keys():
			for key in options.preset[opt].keys():
				try:
					temp[(opt,key)]
				except KeyError:
					print("KeyError on "+key)
					vr[(key)] = mismatch
		vr[0] = mismatch
		return vr
	def configResolve(task,update):
		config = configparser.ConfigParser()
		override = configparser.ConfigParser()
		config.read(options.preset["SETUP"]["config_file"])
		temp = {}
		for opt in config:
			for n, key in enumerate(config[opt].keys()):
				rem = list(config[opt].values())
				temp[(opt, key)] = rem[n]
		for section in options.preset.keys():
			override.add_section(section)
			for key in options.preset[section].keys():
				if(update == 0):
					try:
						override.set(section, key, str(temp[(section,key)]))
					except KeyError:
						override.set(section, key, str(options.preset[section][key]))
				elif(update == 1):
					override.set(section, key, str(options.preset[section][key]))
		with open(options.preset["SETUP"]["config_file"], 'w+') as configfile:
			override.write(configfile)
		return
	def apiGet(method, params):
		if options.preset["AUTHORIZATION"]["use_token"] is 1: #WHY
			request = urllib.request.Request("https://api.vk.com/method/"+method+"?"+params+"&rev="+options.preset["SETUP"]["photo_sorting"]+"&v="+options.preset["SETUP"]["api_version"])
		else:
			request = urllib.request.Request("https://api.vk.com/method/"+method+"?"+params+"&rev="+options.preset["SETUP"]["photo_sorting"]+"&v="+options.preset["SETUP"]["api_version"]+"&access_token="+options.preset["AUTHORIZATION"]["access_token"])
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
	def checkVersion():
		try:
			request = urllib.request.Request("https://raw.githubusercontent.com/men43/AlbumSaver/master/version")
			latest = urllib.request.urlopen(request).read().decode("utf8")
		except:
			latest = 0
		if str(latest) > options.preset["SETUP"]["script_version"]:
			utils.outputMessage(30, "Your script is out of date. Get a new version here: https://github.com/men43/AlbumSaver")
		elif latest == 0:
			utils.outputMessage(40, "Can't check current version.")
		return

class options(object):
	preset = {
	"SETUP": {
		"script_location":os.path.dirname(os.path.realpath(sys.argv[0])) + "\\",
		"data_location":"res",
		"links_file":"links.txt",
		"config_file":"config.ini",
		"log_file":"dump.log",
		"script_version":"0.6.5",
		"api_version":"5.23",
		"photo_sorting":"0",
	},"OUTPUT": {
		"output_log":1,
		"output_console":1,
	},"AUTHORIZATION": {
		"access_token":"",
		"use_token":0
	}}

def startup():
	if os.path.exists(options.preset["SETUP"]["config_file"]):
		upd = 0
		ch = utils.checkConfig()
		if ch[0] == 0 and len(ch) < 2:
			print("Starting VK PhotoSaver. Your config file is up to date. Version v "+options.preset["SETUP"]["script_version"])
		else:
			answer = input("Detected "+str(len(ch))+" missing elements in your config. Want to update? (y/n): ")
			if(answer == "y"):
				if(ch[0] == 1):
					answer = input("Detected version mismatch. Do you want to update your config with default values? (y/n): ")
					if(answer == "y"): upd = 1
				utils.configResolve(ch,upd)
	else:
		utils.createConfig()
	utils.readConfig()
	utils.initLogging()
	utils.checkVersion()
	#ins = input("Entering IDLE mode.")
	if options.preset["AUTHORIZATION"]["access_token"].strip() == "" and options.preset["AUTHORIZATION"]["use_token"] is 1:
		utils.outputMessage(30, "Can't find your access token, you can input it manually.")
		accessToken = input("Token (press ENTER for non-token mode): ")
		if accessToken.strip() == "":
			utils.outputMessage(20, "Non-token mode enabled.")
			options.preset["AUTHORIZATION"]["access_token"] = ""
			options.preset["AUTHORIZATION"]["use_token"] = 0
		else: 
			options.preset["AUTHORIZATION"]["access_token"] = accessToken
	if os.path.exists(options.preset["SETUP"]["script_location"]+options.preset["SETUP"]["data_location"]) != True:
		utils.outputMessage(20, "Can't find data folder, creating.")
		os.mkdir(options.preset["SETUP"]["script_location"]+options.preset["SETUP"]["data_location"])
	if os.path.exists(options.preset["SETUP"]["links_file"]):
		utils.outputMessage(20, "Links file is present, reading.")
	else:
		utils.outputMessage(50, "Can't find links file. Terminating.")
		sys.exit()
	return open(options.preset["SETUP"]["links_file"], 'r').readlines()

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
	pid = 1
	numbers = 0
	while True:
		if pid >= 1000: apiRequest += "&offset="+str(pid-1)
		try:
			rawAlbumData = utils.apiGet("photos.get", apiRequest)
			rawAlbumName = utils.apiGet("photos.getAlbums", "owner_id="+str(full[0])+"&album_ids="+str(full[1]))
		except:
			utils.outputMessage(50, "Can't connect to VK API. Check your internet connection. Terminating.")
			sys.exit()
		decodedData = [json.loads(rawAlbumData), json.loads(rawAlbumName)]
		if specical == 0 and "error" not in decodedData[1]: albumFolder = decodedData[1]["response"]["items"][0]["title"]
		if specical != 0: albumFolder = str(full[0])+"_"+specical
		if pid == 1 and "error" not in decodedData[1]: os.mkdir(options.preset["SETUP"]["data_location"]+"/"+str(albumFolder))
		if "error" not in decodedData[0]:
			numbers = decodedData[0]["response"]["count"]
			curNums = 1000
			if pid >= 1000:
				numbers -= pid - 1
			if pid >= len(decodedData[0]["response"]["items"]):
				curNums = numbers
			if len(decodedData[0]["response"]["items"]) < 1000:
				curNums = numbers
			for w in range(0,curNums):
				numbers -= 1
				if "photo_2560" in decodedData[0]["response"]["items"][w]:
					imageUrl = decodedData[0]["response"]["items"][w]["photo_2560"]
				elif "photo_1280" in decodedData[0]["response"]["items"][w]:
					imageUrl = decodedData[0]["response"]["items"][w]["photo_1280"]
				elif "photo_807" in decodedData[0]["response"]["items"][w]:
					imageUrl = decodedData[0]["response"]["items"][w]["photo_807"]
				else:
					imageUrl = decodedData[0]["response"]["items"][w]["photo_604"]
				utils.downloadImage(imageUrl, options.preset["SETUP"]["data_location"]+"/"+str(albumFolder)+"/"+str(pid)+".jpg")
				pid += 1
		else:
			utils.outputMessage(40, "API error: "+decodedData[0]["error"]["error_msg"]+".")
		if numbers < 1: 
			if "error" not in decodedData[0]: utils.outputMessage(20, "Finished "+str(albumFolder)+" album, downloaded "+str(decodedData[0]["response"]["count"])+" photos.")
			break
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
