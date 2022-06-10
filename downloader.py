from dataclasses import dataclass
from lxml import html
import requests
import shutil
import urllib
import os

@dataclass
class CompressedImages:
    nhentai_id: int

    def __enter__(self):
        self.folderpath = os.path.join("static", str(self.nhentai_id))
        self.zippath = os.path.join("static", "zips", "%i.zip" % self.nhentai_id)
        os.mkdir(self.folderpath)

        self.num_downloaded = self.download_images("https://nhentai.net/g/%i" % self.nhentai_id, self.folderpath, "nhentai.net")

        shutil.make_archive(self.zippath[:-4], "zip", self.folderpath)

        return self.zippath

    def __exit__(self, type, value, traceback):
        # os.remove(self.zippath)
        shutil.rmtree(self.folderpath)

    def download_images(self, url:str, out:str, domain:str) -> int:
        tree = html.fromstring(requests.get(url).content)
        for i, element in enumerate(tree.xpath("//a[@class='gallerythumb']"), 1):
            imurl = self.get_img("https://%s%s" % (domain, element.get("href")), i)
            print(imurl)
            self.dl_img(imurl, out)

        return i

    def get_img(self, srcurl:str, num:int) -> str:
        tree = html.fromstring(requests.get(srcurl).content)
        for element in tree.xpath("//img"):
            try:
                if num == int(os.path.splitext(element.get("src").split("/")[-1])[0]):
                    return element.get("src")
            except ValueError:
                pass

    def dl_img(self, imurl, outpath:str):
        req = urllib.request.Request(imurl, headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_5_8) AppleWebKit/534.50.2 (KHTML, like Gecko) Version/5.0.6 Safari/533.22.3'})
        mediaContent = urllib.request.urlopen(req).read()
        with open(os.path.join(outpath, imurl.split("/")[-1]), "wb") as f:
            f.write(mediaContent)

if __name__ == "__main__":
    with CompressedImages(306013) as zippath:
        import subprocess
        subprocess.run(["cp", zippath, "/home/eden/Downloads"])