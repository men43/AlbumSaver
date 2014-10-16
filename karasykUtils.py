import time,os,sys,configparser,urllib.request,logging

class output(object):
	def initLogging(outputLog, outputConsole, logFile):
		format = logging.Formatter("[%(asctime)s][%(levelname)s] %(message)s", "%d-%m-%y, %H:%M:%S")
		logger = logging.getLogger("root")
		logger.setLevel(20)
		if outputLog != 0:
			fileHandler = logging.FileHandler(logFile)
			fileHandler.setFormatter(format)
			logger.addHandler(fileHandler)
		if outputConsole != 0:
			consoleHandler = logging.StreamHandler()
			consoleHandler.setFormatter(format)
			logger.addHandler(consoleHandler)
		return
	def outputMessage(logLevel, message):
		output = logging.getLogger("root")
		output.log(logLevel, message)
		return
class config(object):
	def createConfig(configPreset):
		config = configparser.ConfigParser()
		for section in configPreset.keys():
			config.add_section(section)
			for key in configPreset[section].keys():
				config.set(section, key, str(configPreset[section][key]))
		with open(configPreset["SETUP"]["config_file"], 'w+') as configfile:
			config.write(configfile)
		return
	def readConfig(configFile):
		config = configparser.ConfigParser()
		config.read(configFile)
		temp = {}
		for opt in config:
			for n, key in enumerate(config[opt].keys()):
				rem = list(config[opt].values())
				temp[(opt, key)] = rem[n]
		return temp
	def checkConfig(configPreset): #extremely bad but its working
		config = configparser.ConfigParser()
		config.read(configPreset["SETUP"]["config_file"])
		mismatch = 0
		temp = {}
		vr = {}
		for opt in config:
			for n, key in enumerate(config[opt].keys()):
				rem = list(config[opt].values())
				temp[(opt, key)] = rem[n]
		if configPreset["SETUP"]["script_version"].replace(".",",") > temp[("SETUP","script_version")].replace(".",","):
			mismatch = 1
		if configPreset["SETUP"]["script_version"].replace(".",",") < temp[("SETUP","script_version")].replace(".",","):
			mismatch = 2
		for opt in configPreset.keys():
			for key in configPreset[opt].keys():
				try:
					temp[(opt,key)]
				except KeyError:
					vr[(key)] = mismatch
		vr[0] = mismatch
		return vr
	def configResolve(configPreset, update):
		config = configparser.ConfigParser()
		override = configparser.ConfigParser()
		config.read(configPreset["SETUP"]["config_file"])
		temp = {}
		for opt in config:
			for n, key in enumerate(config[opt].keys()):
				rem = list(config[opt].values())
				temp[(opt, key)] = rem[n]
		for section in configPreset.keys():
			override.add_section(section)
			for key in configPreset[section].keys():
				if(update == 0):
					try:
						override.set(section, key, str(temp[(section,key)]))
					except KeyError:
						override.set(section, key, str(configPreset[section][key]))
				elif(update == 1):
					override.set(section, key, str(configPreset[section][key]))
		with open(configPreset["SETUP"]["config_file"], 'w+') as configfile:
			override.write(configfile)
		return
class web(object):
	def apiGet(request,settingsSet):
#+method+"?"+params+"&rev="+options.preset["SETUP"]["photo_sorting"]+"&v="+options.preset["SETUP"]["api_version"]+"&access_token="+options.preset["AUTHORIZATION"]["access_token"])
		if settingsSet[("AUTHORIZATION","use_token")] == 1:
			request = urllib.request.Request("https://api.vk.com/method/"+request+"&rev="+settingsSet[("SETUP","photo_sorting")]+"&v="+settingsSet[("SETUP","api_version")])
		else:
			request = urllib.request.Request("https://api.vk.com/method/"+request+"&rev="+settingsSet[("SETUP","photo_sorting")]+"&v="+settingsSet[("SETUP","api_version")]+"&access_token="+settingsSet[("AUTHORIZATION","access_token")])
		return urllib.request.urlopen(request).read().decode("utf8")
	def downloadImage(url, filename):
		request = urllib.request.Request(url)
		image = urllib.request.urlopen(request)
		writeable = open(filename, "wb")
		writeable.write(image.read())
		writeable.close()
		return
	def checkVersion(scriptVersion):#PhotoSaver method
		try:
			request = urllib.request.Request("https://raw.githubusercontent.com/men43/AlbumSaver/master/version")
			latest = urllib.request.urlopen(request).read().decode("utf8")
		except:
			latest = 0
		if str(latest) > scriptVersion:
			print("Your script is out of date. Get a new version here: https://github.com/men43/AlbumSaver")
		elif latest == 0:
			print("Can't check script version. You might have network issues.")
		return