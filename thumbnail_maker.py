# thumbnail_maker.py
import logging
import os
import time
from urllib.parse import urlparse
from urllib.request import urlretrieve
import concurrent.futures
import asyncio

import PIL
from PIL import Image

FORMAT = "[%(threadName)s, %(asctime)s, %(levelname)s] %(message)s"
logging.basicConfig(filename='logfile.log', level=logging.DEBUG, format=FORMAT)


class ThumbnailMakerService(object):
    def __init__(self, home_dir='.'):
        self.home_dir = home_dir
        self.input_dir = self.home_dir + os.path.sep + 'incoming'
        self.output_dir = self.home_dir + os.path.sep + 'outgoing'
        self._event_loop = asyncio.get_event_loop()
        self._executor = concurrent.futures.ThreadPoolExecutor()

    async def download_image_async(self, url):
        return await self._event_loop.run_in_executor(self._executor, self.download_image, url)

    def download_image(self, url):
        # download each image and save to the input dir
        logging.info("downloading image at URL " + url)
        img_filename = urlparse(url).path.split('/')[-1]
        urlretrieve(url, self.input_dir + os.path.sep + img_filename)
        logging.info("image saved to " + self.input_dir + os.path.sep + img_filename)

    def download_images(self, img_url_list):
        # validate inputs
        if not img_url_list:
            return
        os.makedirs(self.input_dir, exist_ok=True)

        logging.info("beginning image downloads")

        start = time.perf_counter()
        futures = []
        for url in img_url_list:
            futures.append(asyncio.ensure_future(self.download_image_async(url)))

        self._event_loop.run_until_complete(futures)

        end = time.perf_counter()

        logging.info("downloaded {} images in {} seconds".format(len(img_url_list), end - start))

    def perform_resizing(self):
        # validate inputs
        if not os.listdir(self.input_dir):
            return
        os.makedirs(self.output_dir, exist_ok=True)

        logging.info("beginning image resizing")
        target_sizes = [32, 64, 200]
        num_images = len(os.listdir(self.input_dir))

        start = time.perf_counter()
        for filename in os.listdir(self.input_dir):
            orig_img = Image.open(self.input_dir + os.path.sep + filename)
            for basewidth in target_sizes:
                img = orig_img
                # calculate target height of the resized image to maintain the aspect ratio
                wpercent = (basewidth / float(img.size[0]))
                hsize = int((float(img.size[1]) * float(wpercent)))
                # perform resizing
                img = img.resize((basewidth, hsize), PIL.Image.LANCZOS)

                # save the resized image to the output dir with a modified file name
                new_filename = os.path.splitext(filename)[0] + \
                    '_' + str(basewidth) + os.path.splitext(filename)[1]
                img.save(self.output_dir + os.path.sep + new_filename)

            os.remove(self.input_dir + os.path.sep + filename)
        end = time.perf_counter()

        logging.info("created {} thumbnails in {} seconds".format(num_images, end - start))

    def make_thumbnails(self, img_url_list):
        logging.info("START make_thumbnails")
        start = time.perf_counter()

        self.download_images(img_url_list)
        # self.perform_resizing()

        end = time.perf_counter()
        logging.info("END make_thumbnails in {} seconds\n\n".format(end - start))
