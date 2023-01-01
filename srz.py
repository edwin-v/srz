#!/usr/bin/python3

PNAME = "srz.py"
SYNTHRIDERS_DIR = "/opt/Steam/SteamLibrary/steamapps/common/SynthRiders"
CUSTOMS_DIR = "/CustomSongs"
SYNTH_EXT = ".synth"
METAFILE = "synthriderz.meta.json"
TMPDIR = "/tmp/_srz"
SRZ_BASE = "https://synthriderz.com"
SRZ_API = "https://synthriderz.com/api/beatmaps"
SRZ_ONECLICKURL = "synthriderz://beatmap/"
SELECTS = "id,hash,title,artist,mapper,duration,BPM,difficulties,filename,download_url"


import sys
import os
import glob
import json
from zipfile import ZipFile
import requests
import dbus


"""
Download JSON data with song info
"""
def DownloadSongInfo(id):
    url = SRZ_API + "/" + str(id) + "?" + SELECTS
    req = requests.get(url)
    if req.status_code == 200:
        return json.loads(req.content)



"""
Generate a list of song information
"""
def ScanCustoms(warnings=True):
    customs = []
    file_list = glob.glob( SYNTHRIDERS_DIR + CUSTOMS_DIR + "/*" + SYNTH_EXT )
    for f in file_list:
        with ZipFile(f, 'r') as custom:
            try:
                custom.extract(METAFILE, TMPDIR)
            except:
                if warnings:
                    print("[Warning] Unknown file:", f);
                continue
        jfile = open(TMPDIR + "/" + METAFILE)
        custom_data = json.load(jfile)
        jfile.close()
        custom_data["filename"] = os.path.basename(f)
        customs.append(custom_data)
    os.remove(TMPDIR + "/" + METAFILE)
    return customs



"""
Find an installed custom by id
This function assumes the current naming system where all
filenames start with the song id followed by a hyphen
"""
def FindCustom(id):
    file_list = glob.glob( SYNTHRIDERS_DIR + CUSTOMS_DIR + "/" + str(id) + "-*" + SYNTH_EXT )
    if len(file_list) == 0:
        return

    for f in file_list:
        with ZipFile(f, 'r') as custom:
            try:
                custom.extract(METAFILE, TMPDIR)
            except:
                # skip files without information
                continue
        jfile = open(TMPDIR + "/" + METAFILE)
        custom_data = json.load(jfile)
        jfile.close()
        os.remove(TMPDIR + "/" + METAFILE)
        if custom_data["id"] == id:
            custom_data["filename"] = os.path.basename(f)
            return custom_data


"""
Print some interesting song information and the download state
"""
def PrintSongInfo(id):
    songinfo = DownloadSongInfo(id)
    if songinfo:
        print("Song ID:     ", songinfo["id"])
        print("Title:       ", songinfo["title"])
        print("Artist:      ", songinfo["artist"])
        print("Mapper:      ", songinfo["mapper"])
        print("Duration:    ", songinfo["duration"])
        print("BPM:         ", songinfo["bpm"])
        print("Difficulties:", end=" ")
        for d in songinfo["difficulties"]:
            if d:
                print(d, end=" ")
        print()
        print("Last updated:", songinfo["updated_at"])
        
        current_customs = ScanCustoms(False)
        if songinfo["id"] in current_customs.keys():
            if current_customs[songinfo["id"]] == songinfo["filename"]:
                print("This song is installed and up to date.")
            else:
                print("This song is installed but out of date.")
        else:
            print("This song is not installed.")         
        
    else:
        print("Failed to get info for song with id:", id)



"""
List all songs and if they're up to date.
Since synthriderz.com includes versions in the filename now, this
can be done by a simple filename comparison.
"""
def CheckCustoms():
    current_customs = ScanCustoms()
    for c in current_customs:
        status = "OK"
        songinfo = DownloadSongInfo(c["id"])
        if not songinfo:
            status = "NOT FOUND"
        elif c["hash"] != songinfo["hash"]:
            status = "OUT OF DATE"
        elif c["filename"] != songinfo["filename"]:
            status = "OK (OLD NAME)"
            
        print("[" + str(c["id"]) + "]", c["filename"], "--", status)



"""
Download a song from JSON data unless the correct file exists
"""
def DownloadSongJSON(songinfo, dbus_notify = None):
    current = FindCustom(songinfo["id"])
    if current:
        # skip if song is up to date
        if current["hash"] == songinfo["hash"]:
            if dbus_notify:
                dbus_notify.Notify("", 0, "", "Song already downloaded and up to date.", songinfo["artist"] + " / " + songinfo["title"], [], {"urgency": 1}, 2500)
            return
        # remove the old song file
        try:
            os.remove(SYNTHRIDERS_DIR + CUSTOMS_DIR + "/" + current["filename"])
        except:
            print("Can't remove the old version:", current["filename"])
    
    # download the new song
    url = SRZ_BASE + songinfo["download_url"]
    req = requests.get(url)
    if req.status_code == 200:
        sf = open(SYNTHRIDERS_DIR + CUSTOMS_DIR + "/" + songinfo["filename"], "wb")
        sf.write(req.content)
        sf.close()
        print("Song",songinfo["id"],"Downloaded to", songinfo["filename"])
        print(songinfo["title"], "by", songinfo["artist"], "(mapped by", songinfo["mapper"] + ")")
        if dbus_notify:
            dbus_notify.Notify("", 0, "", "Song downloaded to Synth Riders.", songinfo["artist"] + " / " + songinfo["title"], [], {"urgency": 1}, 2500)
        
    else:
        print("Failed to download song from:", url);
        print("Error code:", req.status_code)
        if dbus_notify:
            dbus_notify.Notify("", 0, "", "Failed to download song. Error: "+str(req.status_code), songinfo["artist"] + " / " + songinfo["title"], [], {"urgency": 1}, 2500)



"""
Download a song by id
"""
def DownloadSongID(id):
    songinfo = DownloadSongInfo(id)
    if songinfo:
        DownloadSongJSON(songinfo)



"""
Download song by synthriderz:// url
"""
def DownloadSongURL(url):
    # prepare dbus notification for 
    dbusintf = "org.freedesktop.Notifications"
    dbusobj = "/org/freedesktop/Notifications"
    notify = dbus.Interface(dbus.SessionBus().get_object(dbusintf, dbusobj), dbusintf)
    # find song info by hash
    url = SRZ_API + "/?" + SELECTS + '&s={"hash": "' + url[len(SRZ_ONECLICKURL):] + '"}'
    req = requests.get(url)
    if req.status_code != 200:
        print("[Error] Failed to download song information.")
        notify.Notify("", 0, "", "Failed to download song.", "", [], {"urgency": 1}, 2500)
        return
    songinfo = json.loads(req.content)
    DownloadSongJSON(songinfo["data"][0], dbus_notify=notify)



"""
Check installed songs for updates and download them
"""
def UpdateInstalledSongs():
    file_list = glob.glob( SYNTHRIDERS_DIR + CUSTOMS_DIR + "/*" + SYNTH_EXT )
    for f in file_list:
        with ZipFile(f, 'r') as custom:
            try:
                custom.extract(METAFILE, TMPDIR)
            except:
                print("[Warning] Unknown file:", f);
                continue
  
        jfile = open(TMPDIR + "/" + METAFILE)
        custom_data = json.load(jfile)
        jfile.close()
        os.remove(TMPDIR + "/" + METAFILE)
        songinfo = DownloadSongInfo(custom_data["id"])
        
        if not songinfo:
            print("[Error] No song with id", custom_data["id"], " found in ", os.path.basename(f))
            continue
        
        if(songinfo["hash"] == custom_data["hash"]):
            if(songinfo["filename"] == os.path.basename(f)):
                print(songinfo["title"], "by", songinfo["artist"], "(mapped by", songinfo["mapper"] + ") is up to date")
            else:
                os.rename(f, SYNTHRIDERS_DIR + CUSTOMS_DIR + "/" + songinfo["filename"])
                print(songinfo["title"], "by", songinfo["artist"], "(mapped by", songinfo["mapper"] + ") is up to date and renamed to the current naming convention")
            continue

        DownloadSongJSON(songinfo)



"""
Download song info per page and check for new and updated songs
"""
def DownloadAllSongs():
    page = 1
    while True:
        # download a page of song info
        url = SRZ_API + "?select=" + SELECTS + "&page=" + str(page)
        req = requests.get(url)
        if req.status_code != 200:
            print("[Error] Failed to download song information.")
            return

        pagedata = json.loads(req.content)
        
        if page == 0:
            print("Checking and/or downloading", pagedata["total"], "songs.")
        
        for songinfo in pagedata["data"]:
            DownloadSongJSON(songinfo)
        
        page += 1
        
        if pagedata["page"] == pagedata["pageCount"]:
            return



"""
Perform a text search in the song list on synthriderz.com
"""
def SearchSongs(text):
    url = SRZ_API + "/?" + SELECTS + '&s={"text_search":{"$tsQuery":"'+text+'"}}'
    req = requests.get(url)
    if req.status_code != 200:
        print("[Error] Search failed for text:", text)
        return
    res = json.loads(req.content)
    
    if res["count"] == 0:
        print("No results found for text:", text)
        return
    
    print("Search results for text:", text)
    for i in range(res["count"]):
        songinfo = res["data"][i]
        print("%5i:" % songinfo["id"], songinfo["title"], "by", songinfo["artist"], "(mapped by", songinfo["mapper"] + ")")
    



"""
Print the usage information
"""
def print_usage():
    print(PNAME, "- A download and update tool for SynthRiderz.com")
    print()
    print("Usage:")
    print("   srz command [argument]")
    print()
    print("Available commands:")
    print("   d id         download a song by id number")
    print("   d url        download using a synthriderz:// url")
    print("   u            make sure all songs are up to date")
    print("   a            download all new and updated songs")
    print("   c            check installed songs for validity and updates")
    print("   i id         print information for a song with id number")
    print("   s keyword    search for a song and display id and information")



def main(argv):
    # create temporary dir
    try:
        os.mkdir(TMPDIR)
    except OSError as error:
        if not error.errno == 17:
            print("Can't create temporary directory:", TMPDIR);
            return

    # display song inf
    if(argv[0] == "i"):
        if len(argv)>1:
            try:
                id = int(argv[1])
            except:
                id = 0
                
            if id>1:
                PrintSongInfo(id)
            else:
                print("Error: invalid song id")

    # check song status
    elif(argv[0] == "c"):
        CheckCustoms()

    # download song
    elif(argv[0] == "d"):
        if len(argv)>1:
            if(argv[1].startswith(SRZ_ONECLICKURL)):
                DownloadSongURL(argv[1]);
            else:
                try:
                    id = int(argv[1])
                except:
                    id = 0
                    
                if id>1:
                    DownloadSongID(id)
                else:
                    print("Error: invalid song id")

    # download updates
    elif(argv[0] == "u"):
        UpdateInstalledSongs()

    # download all songs
    elif(argv[0] == "a"):
        DownloadAllSongs()

    # search
    elif(argv[0] == "s"):
        SearchSongs(' '.join(argv[1:]))


    os.rmdir(TMPDIR)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1:])
    else:
        print_usage()
