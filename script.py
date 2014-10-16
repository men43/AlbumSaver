import karasykUtils,os,sys,json,time

class options(object):
	preset = {
	"SETUP": {
		"script_location":os.path.dirname(os.path.realpath(sys.argv[0])) + "\\",
		"data_location":"res",
		"links_file":"links.txt",
		"config_file":"config.ini",
		"log_file":"dump.log",
		"script_version":"0.7",
		"api_version":"5.25",
		"photo_sorting":"0",
	},"OUTPUT": {
		"output_log":1,
		"output_console":1,
	},"AUTHORIZATION": {
		"access_token":"",
		"use_token":0
	}}
	set = {}

def startup():
	if os.path.exists(options.preset["SETUP"]["config_file"]):
		upd = 0
		ch = karasykUtils.config.checkConfig(options.preset)
		if ch[0] == 0 and len(ch) < 2:
			print("Starting VK PhotoSaver. Your config file is up to date. Version v"+options.preset["SETUP"]["script_version"])
		else:
			answer = input("Detected "+str(len(ch))+" missing elements in your config. Want to update? (y/n): ")
			if(answer == "y"):
				if(ch[0] == 1):
					answer = input("Detected version mismatch. Do you want to update your config with default values? (y/n): ")
					if(answer == "y"): upd = 1
				karasykUtils.config.configResolve(options.preset,upd)
	else:
		karasykUtils.config.createConfig(options.preset)
	options.set = karasykUtils.config.readConfig(options.preset["SETUP"]["config_file"])
	karasykUtils.output.initLogging(options.preset["OUTPUT"]["output_log"], options.preset["OUTPUT"]["output_console"], options.preset["SETUP"]["log_file"])
	karasykUtils.web.checkVersion(options.preset["SETUP"]["script_version"])
	if options.set[("AUTHORIZATION","access_token")].strip() == "" and options.set[("AUTHORIZATION","use_token")] is 1:
		karasykUtils.output.outputMessage(30, "Can't find your access token, you can input it manually.")
		accessToken = input("Token (press ENTER for non-token mode): ")
		if accessToken.strip() == "":
			karasykUtils.output.outputMessage(20, "Non-token mode enabled.")
			options.set[("AUTHORIZATION","access_token")] = ""
			options.set[("AUTHORIZATION","use_token")] = 0
		else:
			options.set[("AUTHORIZATION","access_token")] = accessToken
	if os.path.exists(options.set[("SETUP","script_location")]+options.set[("SETUP","data_location")]) != True:
		karasykUtils.output.outputMessage(20, "Can't find data folder, creating.")
		os.mkdir(options.set[("SETUP","script_location")]+options.set[("SETUP","data_location")])
	if os.path.exists(options.set[("SETUP","links_file")]):
		karasykUtils.output.outputMessage(20, "Links file is present, reading.")
	else:
		karasykUtils.output.outputMessage(50, "Can't find links file. Terminating.")
		sys.exit()
	return open(options.set[("SETUP","links_file")], 'r').readlines()

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
			rawAlbumData = karasykUtils.web.apiGet("photos.get?"+apiRequest,options.set)
			rawAlbumName = karasykUtils.web.apiGet("photos.getAlbums?owner_id="+str(full[0])+"&album_ids="+str(full[1]),options.set)
		except:
			karasykUtils.output.outputMessage(50, "Can't connect to VK API. Check your internet connection. Terminating.")
			sys.exit()
		decodedData = [json.loads(rawAlbumData), json.loads(rawAlbumName)]
		if specical == 0 and "error" not in decodedData[1]: albumFolder = decodedData[1]["response"]["items"][0]["title"]
		if specical != 0: albumFolder = str(full[0])+"_"+specical
		if pid == 1 and "error" not in decodedData[1]:
			try:
				os.mkdir(options.set[("SETUP","data_location")]+"/"+str(albumFolder))
			except OSError:
				albumFolder += "_"+str(int(time.time()))
				os.mkdir(options.set[("SETUP","data_location")]+"/"+str(albumFolder))
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
				karasykUtils.web.downloadImage(imageUrl, options.set[("SETUP","data_location")]+"/"+str(albumFolder)+"/"+str(pid)+".jpg")
				karasykUtils.output.outputMessage(20, "Saved "+str(pid)+".jpg")
				pid += 1
		else:
			karasykUtils.output.outputMessage(40, "API error: "+decodedData[0]["error"]["error_msg"])
		if numbers < 1:
			if "error" not in decodedData[0]: karasykUtils.output.outputMessage(20, "Finished "+str(albumFolder)+" album, downloaded "+str(decodedData[0]["response"]["count"])+" photos.")
			break
	return

def run():
	links = startup()
	if len(links) == 0:
		karasykUtils.output.outputMessage(50, "Links file is empty, terminating.")
		sys.exit()
	for n,i in enumerate(links):
		downloadAlbum(i.rstrip("\n"),n)
	return
run()