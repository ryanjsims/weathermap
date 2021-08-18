from json.decoder import JSONDecodeError
from http.client import RemoteDisconnected
from typing import Tuple
import requests
import numpy as np
from PIL import Image
from io import BytesIO
import json
import time
import os
import math
import sys

host = ""
path = ""
size = 256
lat = 33.317027
lon = -111.875500
z = 9                           #zoom level
color = 4                       #Weather channel colors
options = "0_0"                 #smoothed with no snow
dimensions = (200000, 200000)   #dimensions of final image in meters
grid_size = (256, 256)            #Number of LEDs in matrix rows and columns
mapsURL = "https://api.rainviewer.com/public/weather-maps.json"
tileURL = "{host}{path}/{size}/{z}/{lat}/{lon}/{color}/{options}.png"
tileXYURL = "{host}{path}/{size}/{z}/{x}/{y}/{color}/{options}.png"

zoom2res = [156543.00, 78271.52, 39135.76, 19567.88, 9783.94, 
        4891.97, 2445.98, 1222.99, 611.4962, 305.7481, 152.8741, 
        76.437, 38.2185, 19.1093, 9.5546, 4.7773, 2.3887, 1.1943,
        0.5972, 0.2986, 0.1493, 0.0746, 0.0373, 0.0187]

timestamps = []
last_update = 0

def scantree(path):
    """Recursively yield DirEntry objects for given directory."""
    for entry in os.scandir(path):
        if entry.is_dir(follow_symlinks=False):
            yield from scantree(entry.path)  # see below for Python 2.x
        else:
            yield entry

def deg2num(lat_deg, lon_deg, zoom, dec = []):
    assert 0 <= zoom <= 22, "Use a zoom level between 0 and 22, inclusive"
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = (lon_deg + 180.0) / 360.0 * n
    ytile = (1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n
    dec.append(xtile - int(xtile))
    dec.append(ytile - int(ytile))
    return (int(xtile), int(ytile))

def download(lat: float, lon: float, z: int, dim: Tuple[int, int], final_size: Tuple[int, int]) -> Image.Image:
    dec = []
    to_download = []
    x, y = deg2num(lat, lon, z, dec)
    xpix = int(dim[0] / zoom2res[z])
    ypix = int(dim[1] / zoom2res[z])
    centerx = int(256 * dec[0])
    centery = int(256 * dec[1])
    pxbounds = [centerx - xpix / 2, 
              centery - ypix / 2, 
              centerx + xpix / 2, 
              centery + ypix / 2]
    bounds = [math.floor((centerx - xpix / 2) / 256), 
              math.floor((centery - ypix / 2) / 256), 
              math.floor((centerx + xpix / 2) / 256), 
              math.floor((centery + ypix / 2) / 256)]
    width = (bounds[2] - bounds[0] + 1) * 256
    height = (bounds[3] - bounds[1] + 1) * 256
    absbounds = [-bounds[0] * 256 + pxbounds[0], -bounds[1] * 256 + pxbounds[1],
                 -bounds[0] * 256 + pxbounds[2], -bounds[1] * 256 + pxbounds[3]]
    for i in range(bounds[0], bounds[2] + 1):
        for j in range(bounds[1], bounds[3] + 1):
            to_download.append((x + i, y + j))
    image_dims = (bounds[2] + 1 - bounds[0], bounds[3] + 1 - bounds[1])
    images = []
    for i in range(len(to_download)):
        coords = to_download[i]
        r = requests.get(tileXYURL.format(**globals(), x=coords[0], y=coords[1]))
        image = BytesIO()
        for chunk in r:
            image.write(chunk)
        image.seek(0)
        images.append(Image.open(image))

    combined = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    for i, image in enumerate(images):
        combined.paste(image, ((i // image_dims[1]) * 256, (i % image_dims[1]) * 256))
        image.close()
    resized = remove_alpha(combined.crop(map(int, absbounds)).resize(final_size), (0, 0, 0))
    combined.close()
    return resized


def build_cache():
    global host, path, last_update
    for file in scantree("cache"):
        if file.is_file():
            os.remove(file.path)
    r = requests.get(mapsURL)
    try:
        data = r.json()

        last_update = data["generated"]
        host = data["host"]
        for snapshot in data["radar"]["past"]:
            path = snapshot["path"]
            img = download(lat, lon, z, dimensions, grid_size)
            img.save("cache/" + str(snapshot["time"]) + ".png")
            timestamps.append(snapshot["time"])
        for nowcast in data["radar"]["nowcast"]:
            path = nowcast["path"]
            img = download(lat, lon, z, dimensions, grid_size)
            img.save("cache/nowcast/" + str(nowcast["time"]) + ".png")
    except JSONDecodeError as e:
        print("[ERROR] Unable to decode weather maps json:", file=sys.stderr)
        print(e, file=sys.stderr)

def update_cache():
    global host, path, last_update
    r = requests.get(mapsURL)
    try:
        data = r.json()
        if data["generated"] == last_update:
            return 0
        updates = 0
        last_update = data["generated"]
        for file in scantree("cache/nowcast"):
            if file.is_file():
                os.remove(file.path)
        for snapshot in data["radar"]["past"]:
            if snapshot["time"] in timestamps:
                continue
            path = snapshot["path"]
            img = download(lat, lon, z, dimensions, grid_size)
            img.save("cache/" + str(snapshot["time"]) + ".png")
            timestamps.append(snapshot["time"])
            updates += 1
        for nowcast in data["radar"]["nowcast"]:
            path = nowcast["path"]
            img = download(lat, lon, z, dimensions, grid_size)
            img.save("cache/nowcast/" + str(nowcast["time"]) + ".png")
            updates += 1
        webtimestamps = [snapshot["time"] for snapshot in data["radar"]["past"]]
        i = 0
        while i < len(timestamps):
            if timestamps[i] in webtimestamps:
                i += 1
                continue
            os.remove("cache/" + str(timestamps[i]) + ".png")
            timestamps.pop(i)
            updates += 1
        return updates
    except JSONDecodeError as e:
        print("[ERROR] Unable to decode weather maps json:", file=sys.stderr)
        print(e, file=sys.stderr)
    except ConnectionError as e:
        print("[ERROR] Connection error:", file=sys.stderr)
        print(e, file=sys.stderr)
    except Exception as e:
        print("[ERROR] ", file=sys.stderr, end='')
        print(e, file=sys.stderr)
    return 0

def main():
    build_cache()
    print("{} [INFO] Built cache".format(int(time.time())))
    while True:
        time.sleep(60)
        try:
            updates = update_cache()
            print("{} [INFO] Updated cache ({} files affected)".format(int(time.time()), updates))
        except Exception as e:
            print("[ERROR] ", file=sys.stderr, end='')
            print(e, file=sys.stderr)


def remove_alpha(image: Image.Image, color: tuple=(255, 255, 255)):
    """Alpha composite an RGBA Image with a specified color.

    Source: http://stackoverflow.com/a/9459208/284318

    Keyword Arguments:
    image -- PIL RGBA Image object
    color -- Tuple r, g, b (default 255, 255, 255)
    """
    image.load()  # needed for split()
    background = Image.new('RGB', image.size, color)
    background.paste(image, mask=image.split()[3])  # 3 is the alpha channel
    return background

if __name__ == "__main__":
    main()