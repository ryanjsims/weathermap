#!/usr/bin/python3.7

from json.decoder import JSONDecodeError
from http.client import RemoteDisconnected
from typing import Tuple
import requests
from PIL import Image
from io import BytesIO
import time
import os
import math
import grp, pwd
import sys
from threading import Thread, Event
from multiprocessing import Process
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
from datetime import datetime
from dateutil.tz import tzlocal, tzutc
import logging as log
from logging.handlers import RotatingFileHandler

import weatherportal

MB = 1024 * 1024

class BraceMessage:
    def __init__(self, fmt, *args, **kwargs):
        self.fmt = fmt
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        return self.fmt.format(*self.args, **self.kwargs)

__ = BraceMessage

class RedirectingRotatingFileHandler(RotatingFileHandler):
    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0, encoding=None, delay=False, redirectstderr=False, redirectstdout=False):
        super().__init__(filename, mode, maxBytes=maxBytes, backupCount=backupCount, encoding=encoding, delay=delay)
        self.stderr = redirectstderr
        self.stdout = redirectstdout
        self.doRedirect()

    def doRollover(self) -> None:
        super().doRollover()
        self.doRedirect()
    
    def doRedirect(self):
        if self.stderr:
            sys.stderr = self.stream
        if self.stdout:
            sys.stdout = self.stream

log.basicConfig(
    level=log.INFO,
    format="[{asctime}] [{levelname}]: {message}", 
    datefmt="%Y-%m-%d %H:%M:%S %Z", 
    style='{',
    handlers=[RedirectingRotatingFileHandler("/var/log/weathermap.log", maxBytes=25*MB, backupCount=5, redirectstderr=True, redirectstdout=True)]
)

host = ""
path = ""
size = 256
lat = 33.317027
lon = -111.875500
z = 9                           #zoom level
color = 4                       #Weather channel colors
options = "0_0"                 #smoothed with no snow
dimensions = (200000, 200000)   #dimensions of final image in meters
img_size = (64, 64)            #Number of LEDs in matrix rows and columns
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
    
    images = [{"coords": coords, "image": None} for coords in to_download]

    def helper(coords):
        r = requests.get(tileXYURL.format(**globals(), x=coords[0], y=coords[1]))
        image = BytesIO()
        for chunk in r:
            image.write(chunk)
        image.seek(0)
        for image_obj in images:
            if image_obj["coords"] == coords:
                image_obj["image"] = Image.open(image)

    download_threads = []
    for image in images:
        download_threads.append(Thread(target=helper, args=(image["coords"],)))
        download_threads[-1].start()

    for thread in download_threads:
        thread.join() 

    combined = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    for i, image in enumerate(images):
        combined.paste(image["image"], ((i // image_dims[1]) * 256, (i % image_dims[1]) * 256))
        image["image"].close()
    
    resized = remove_alpha(combined.crop(map(int, absbounds)).resize(final_size), (0, 0, 0))
    combined.close()
    return resized


def save_with_perms(path: str, image: Image.Image, username: str, groupname: str, perms: int):
    image.save(path)
    os.chown(path, pwd.getpwnam(username).pw_uid, grp.getgrnam(groupname).gr_gid)
    os.chmod(path, perms)


def build_cache():
    finished = Event()
    cache_ready = Event()
    def task():
        log.info("Building cache...")
        global host, path, last_update
        for file in scantree("cache"):
            if file.is_file():
                os.remove(file.path)
        try:
            r = requests.get(mapsURL)
            data = r.json()

            last_update = data["generated"]
            host = data["host"]
            for snapshot in data["radar"]["past"]:
                path = snapshot["path"]
                img = download(lat, lon, z, dimensions, img_size)
                save_with_perms("cache/" + str(snapshot["time"]) + ".png", img, "daemon", "daemon", 0o660)
                timestamps.append(snapshot["time"])
                if not cache_ready.is_set():
                    cache_ready.set()
            for nowcast in data["radar"]["nowcast"]:
                path = nowcast["path"]
                img = download(lat, lon, z, dimensions, img_size)
                save_with_perms("cache/nowcast/" + str(nowcast["time"]) + ".png", img, "daemon", "daemon", 0o660)
        except JSONDecodeError as e:
            log.error(__("Unable to decode weathermaps json: {}", e))
        finally:
            finished.set()
            log.info("Built cache")
    build_thread = Thread(target=task)
    build_thread.daemon = True
    return finished, cache_ready, build_thread


def update_cache():
    global host, path, last_update
    try:
        log.info("Updating cache...")
        r = requests.get(mapsURL)
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
            img = download(lat, lon, z, dimensions, img_size)
            save_with_perms("cache/" + str(snapshot["time"]) + ".png", img, "daemon", "daemon", 0o660)
            timestamps.append(snapshot["time"])
            updates += 1
        for nowcast in data["radar"]["nowcast"]:
            path = nowcast["path"]
            img = download(lat, lon, z, dimensions, img_size)
            save_with_perms("cache/nowcast/" + str(nowcast["time"]) + ".png", img, "daemon", "daemon", 0o660)
            updates += 1
        webtimestamps = [snapshot["time"] for snapshot in data["radar"]["past"]]
        i = 0
        while i < len(timestamps):
            if timestamps[i] in webtimestamps:
                i += 1
                continue
            if(os.path.exists("cache/" + str(timestamps[i]) + ".png")):
                os.remove("cache/" + str(timestamps[i]) + ".png")
                timestamps.pop(i)
                updates += 1
        return updates
    except JSONDecodeError as e:
        log.error("Unable to decode weathermaps json: " + str(e))
    except ConnectionError as e:
        log.error("Connection error: " + str(e))
    except Exception as e:
        log.error(str(e))
    return 0


def get_cache():
    #return ["test_image.png"]
    return sorted(
        [{"path": "cache/" + name, "nowcast": False} for name in os.listdir("cache") if name != "nowcast"] + [{"path": "cache/nowcast/" + name, "nowcast": True} for name in os.listdir("cache/nowcast/")],
        key = lambda item: item["path"])


def grid_to_img(coord):
    to_return = [0, 0]
    if coord[0] < img_size[0]:
        to_return = coord
    else:
        to_return[0] = (img_size[0] - 1) - (coord[0] % img_size[0])
        to_return[1] = (img_size[1] - 1) - coord[1]
    return tuple(to_return)        


def img_to_grid(coord):
    to_return = [0, 0]
    if coord[1] < (img_size[1] // 2):
        to_return = coord
    else:
        to_return[0] = (img_size[0] * 2 - 1) - coord[0]
        to_return[1] = (img_size[1] - 1) - coord[1]
    return tuple(to_return)


def display():
    log.info("Initializing display...")
    options = RGBMatrixOptions()
    options.cols = 64
    options.rows = 32
    options.chain_length = 2
    options.gpio_slowdown = 2
    matrix = RGBMatrix(options=options)
    stop = Event()
    def loop():
        log.info("Starting display...")
        font = graphics.Font()
        font.LoadFont("fonts/4x6.bdf")
        past_color = graphics.Color(255, 255, 255)
        future_color = graphics.Color(255, 0, 255)
        cache = get_cache()
        next = cache[0]
        canvas = matrix.CreateFrameCanvas()
        try:
            while not stop.wait(5):
                try:
                    log.info(__("Updating display to {}", next["path"]))
                    try:
                        img = Image.open(next["path"]).convert("RGB")
                    except FileNotFoundError:
                        log.error(__("File not found: {}", next["path"]))
                        next = get_cache()[0]
                        img = Image.open(next["path"]).convert("RGB")
                    dt = datetime.fromtimestamp(int(next["path"].split(".")[0].split("/")[-1]), tz=tzutc()).astimezone(tzlocal())
                    timestr = dt.strftime("%H:%M")
                    datestr = dt.strftime("%m-%d")
                    time.sleep(0.1)
                    color = past_color
                    if next["nowcast"]:
                        color = future_color
                    next = cache[(cache.index(next) + 1) % len(cache)]
                    cache = get_cache()
                    for i in range(128):
                        for j in range(32):
                            pixel = img.getpixel(grid_to_img((i, j)))
                            canvas.SetPixel(i, j, pixel[0], pixel[1], pixel[2])
                    graphics.DrawText(canvas, font, 2, 11, color, timestr)
                    graphics.DrawText(canvas, font, 2, 17, color, datestr)
                    canvas = matrix.SwapOnVSync(canvas)
                except Exception as e:
                    log.error(__("Display Error:\n{exc_info}", exc_info=e))
        finally:
            matrix.Clear()

    display_process = Thread(target=loop)
    display_process.daemon = True
    return stop.set, display_process


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


def main():
    log.info(__("Current working directory: {}", os.getcwd()))
    stop, matrix_thread = display()
    server_thread = weatherportal.initialize_server(host="0.0.0.0")
    try:
        server_thread.start()
        finished, cache_ready, cache_thread = build_cache()
        cache_thread.start()
        while not cache_ready.wait(5):
            log.debug("Waiting on cache to build")
        matrix_thread.start()
        while True:
            time.sleep(60)
            while not finished.wait(5):
                pass
            try:
                updates = update_cache()
                log.info(__("Updated cache ({} files affected)", updates))
            except Exception as e:
                log.error(str(e))
    except KeyboardInterrupt:
        log.info("Caught ctrl-c, exiting...")
    except Exception as e:
        log.error(str(e))
    finally:
        stop()
        server_thread.shutdown()


if __name__ == "__main__":
    main()