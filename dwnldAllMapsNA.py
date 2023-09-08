import requests
from bs4 import BeautifulSoup
import datetime as dt
import re
import os
import sys
from zipfile import ZipFile
from rich.progress import Progress


# returns 2 dimensional list matrix containing name, url, and release date
def parseOSMANDPage():
    URL = "https://osmand.net/list.php"
    URL_main = "https://osmand.net"

    page = requests.get(URL)

    soup = BeautifulSoup(page.content, "html.parser")
    # print(soup.title.string)

    table = soup.find("table")
    table_rows = table.find_all("tr")[1:]

    # print(table_rows[1])
    # print(table_rows[1].a.get("href")) #gets url
    # print(table_rows[1].a.text) # gets title of file

    mapFilesUSAFull = []
    
    for tr in table_rows:
       name = tr.a.text.lower() #lowercase the filename to make it easier to parse
       usa = re.search("\Aus.*2.obf.zip", name) #get only usa
       
       if usa:
        td = tr.find_all("td")
        releaseDate = td[1].text # get release date

        name_spl = name.split("_")
        if name_spl[2] == "northamerica":
                # filename, url, date
                info = [tr.a.text, URL_main + tr.a.get("href"), releaseDate] 
                mapFilesUSAFull.append(info)
    
    return mapFilesUSAFull

# parse to download the supermaps from OpenSuperMaps
def parseSuperMaps():
    URL = "https://opensupermaps.com/"

    page = requests.get(URL)

    soup = BeautifulSoup(page.content, "html.parser")
    # print(soup.title.string)

    table = soup.find("table")
    table_rows = table.find_all("tr")[1:]

    # print(table_rows[0])
    # print(table_rows[1].a.get("href")) #gets url
    # print(table_rows[1].a.text) # gets title of file

    # print(os.path.join(URL, table_rows[1].a.get("href"))) # file url download

    superMaps = []
    for tr in table_rows:
        td = tr.find_all("td")
        name = td[0].a.text
        usa = re.search("\AUS.*", name)

        if usa:
            info = [name, os.path.join(URL, td[0].a.get("href"))]
            superMaps.append(info)
    return superMaps


def superMapsSetup(superMaps):
    basePath = os.path.join(os.getcwd(),"USA_Super_Maps") # name of usa maps directory
    yesExist = os.path.exists(basePath)
    
    # create main maps download dir
    if not yesExist:
        os.makedirs(basePath)

    for row in superMaps:
        name = row[0]
        URL = row[1]
        name = name.replace(" ", "-")
        downloadSuperMaps(name, basePath, URL)

# make directories, check if exist, and initiate download if not exist
def setupDirectories(mapTable):
    basePath = os.path.join(os.getcwd(),"USA_Maps") # name of usa maps directory
    yesExist = os.path.exists(basePath)
    
    # create main maps download dir
    if not yesExist:
        os.makedirs(basePath)
    
    # date stuffz
    dateStr = mapTable[0][2] # get date from first entry
    maps_Date = dt.datetime.strptime(dateStr, "%d.%m.%Y").date()
    today = dt.date.today()
    # print(today)
    # print(maps_Date)

    maps_dateStr = maps_Date.strftime("%Y_%m_%d")
    currMapsDateDir = os.path.join(basePath, maps_dateStr)
    currMapsDirExist = os.path.exists(currMapsDateDir)

    # case where latest maps folder not exist, then download them
    if not currMapsDirExist: 
        os.makedirs(currMapsDateDir)
        zipDir = os.path.join(currMapsDateDir, "zip")
        unzipDir = os.path.join(currMapsDateDir, "unziped")
        os.makedirs(zipDir)
        os.makedirs(unzipDir)
        
        for row in mapTable:
            zipFileName = row[0]
            fileURL = row[1]
            downloadMap(zipFileName, zipDir, fileURL)
            unzipMapArchive(zipFileName, zipDir, unzipDir)
        

    else: # check if latest maps does exist
        listOfDates = []
        # scan the download dir dates
        for dateDir in os.listdir(basePath):
            d = os.path.join(basePath, dateDir)
            if os.path.isdir(d):
                listOfDates.append(dateDir)
 
        listOfDates.sort(key=lambda date: dt.datetime.strptime(date, "%Y_%m_%d"))

        if maps_dateStr == listOfDates[len(listOfDates)-1]:
            exitProgram()

    # for state in mapTable:
    #     print(state)

def downloadSuperMaps(fileName, dwldDir, URL):
    r = requests.get(URL, stream = True)
    newFileName = "Super_" + fileName +".obf"

    with Progress() as progress:
        size = int(r.headers["Content-length"])
        with open(os.path.join(dwldDir, newFileName), "wb") as f:
            dl = progress.add_task("[red]Begin Download of {}[/red]".format(newFileName), total=size)
            for chunk in r.iter_content(chunk_size = 1024*1024):
                if chunk:
                    f.write(chunk)
                    progress.update(dl, advance=len(chunk), description="[yellow]Downloading {}...[/yellow]".format(newFileName))
            progress.update(dl, description="[green]Download of {} DONE[/green]".format(newFileName))

# inputs: fileName: str
# dwnldDir: str of dest dir for zip file
# mapURL: str of web URL to download from
def downloadMap(fileName, dwldDir, mapURL):
    # print("Downloading file: {}".format(fileName))
    r = requests.get(mapURL, stream = True)

    with Progress() as progress:
        size = int(r.headers["Content-length"])
        with open(os.path.join(dwldDir,fileName), "wb") as f:
            dl = progress.add_task("[red]Begin Download of {}[/red]".format(fileName), total=size)
            for chunk in r.iter_content(chunk_size = 1024*1024):
                if chunk:
                    f.write(chunk)
                    progress.update(dl, advance=len(chunk), description="[yellow]Downloading {}...[/yellow]".format(fileName))
            progress.update(dl, description="[green]Download of {} DONE[/green]".format(fileName))


def unzipMapArchive(zipFileName, dirOfZip, destOfUnzip):
    with ZipFile(os.path.join(dirOfZip, zipFileName)) as zf:
        obfFileName = zipFileName.rsplit(".",1)[0]
        zf.extract(obfFileName, destOfUnzip)
        print("Finished unzipping {}".format(zipFileName))


def exitProgram():
    print("Most up to date maps exist! Exiting now!")
    sys.exit(0)

def main():
    # usaMaps = parseOSMANDPage()
    # setupDirectories(usaMaps)

    superMaps = parseSuperMaps()
    superMapsSetup(superMaps)

if __name__ == "__main__":
    main()