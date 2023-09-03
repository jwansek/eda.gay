from dataclasses import dataclass
from io import StringIO
from lxml import html, etree
from github import Github
import multiprocessing
import pihole as ph
import qbittorrent
import configparser
import requests
import datetime
import urllib
import docker
import clutch
import random
import queue
import json
import time
import os

theLastId = 0
CONFIG = configparser.ConfigParser(interpolation = None)
CONFIG.read("edaweb.conf")

def humanbytes(B):
   'Return the given bytes as a human friendly KB, MB, GB, or TB string'
   B = float(B)
   KB = float(1024)
   MB = float(KB ** 2) # 1,048,576
   GB = float(KB ** 3) # 1,073,741,824
   TB = float(KB ** 4) # 1,099,511,627,776

   if B < KB:
      return '{0} {1}'.format(B,'Bytes' if 0 == B > 1 else 'Byte')
   elif KB <= B < MB:
      return '{0:.2f} KB'.format(B/KB)
   elif MB <= B < GB:
      return '{0:.2f} MB'.format(B/MB)
   elif GB <= B < TB:
      return '{0:.2f} GB'.format(B/GB)
   elif TB <= B:
      return '{0:.2f} TB'.format(B/TB)

def timeout(func):
    # cant get this to work with queue.Queue() for some reason?
    # this works but Manager() uses an extra thread than Queue()
    manager = multiprocessing.Manager()
    returnVan = manager.list()
    # ti = time.time()
   
    def runFunc(q, func):
        q.append(func())

    def beginTimeout():
        t = multiprocessing.Process(target = runFunc, args = (returnVan, func))
        t.start()

        t.join(timeout = CONFIG["servicetimeout"].getint("seconds"))

        # print("Request took:", time.time() - ti)
        try:
            return returnVan[0]
        except IndexError:
            if t.is_alive():
                t.terminate()

    return beginTimeout

@timeout
def get_docker_stats():
    client = docker.DockerClient(base_url = "tcp://%s:%s" % (CONFIG["docker"]["url"], CONFIG["docker"]["port"]))
    return {
        container.name: container.status
        for container in client.containers.list(all = True)
    }

# currently unused
@timeout
def get_qbit_stats():
    numtorrents = 0
    bytes_dl = 0
    bytes_up = 0
    qb = qbittorrent.Client('http://%s:%s/' % (CONFIG["qbittorrent"]["url"], CONFIG["qbittorrent"]["port"]))
    qb.login(username = CONFIG["qbittorrent"]["user"], password = CONFIG["qbittorrent"]["passwd"])

    for torrent in qb.torrents():
        numtorrents += 1
        bytes_up += torrent["uploaded"] 
        bytes_dl += torrent["downloaded"]
        
    return {
       "bytes_dl": humanbytes(bytes_dl),
       "bytes_up": humanbytes(bytes_up),
       "num": numtorrents,
       "ratio": "%.3f" % (float(bytes_up) / float(bytes_dl))
    }

@timeout
def get_trans_stats():
    client = clutch.client.Client(
        address = "http://%s:%s/transmission/rpc" % (CONFIG["transmission"]["url"], CONFIG["transmission"]["port"]),
        # username = CONFIG["transmission"]["username"],
        # password = CONFIG["transmission"]["password"]
    )
    stats = json.loads(client.session.stats().json())
    active_for = datetime.timedelta(seconds = stats["arguments"]["cumulative_stats"]["seconds_active"])
    return {
       "bytes_dl": humanbytes(stats["arguments"]["cumulative_stats"]["downloaded_bytes"]),
       "bytes_up": humanbytes(stats["arguments"]["cumulative_stats"]["uploaded_bytes"]),
       "num": stats["arguments"]["torrent_count"],
       "ratio": "%.3f" % (float(stats["arguments"]["cumulative_stats"]["uploaded_bytes"]) / float(stats["arguments"]["cumulative_stats"]["downloaded_bytes"])),
       "active_for": str(active_for)
    }

@timeout
def get_pihole_stats():
    pihole = ph.PiHole(CONFIG["pihole"]["url"])
    return {
        "status": pihole.status,
        "queries": pihole.total_queries,
        "clients": pihole.unique_clients,
        "percentage": pihole.ads_percentage,
        "blocked": pihole.blocked,
        "domains": pihole.domain_count,
        "last_updated": str(datetime.datetime.fromtimestamp(pihole.gravity_last_updated["absolute"]))
    }

@dataclass
class SafebooruImage:
    id_: int
    url: str
    searchTags: list
    tags: list
    source: str
    imurl: str

    def remove_tag(self, tag):
        return list(set(self.searchTags).difference(set([tag])))

@dataclass
class DownloadedImage:
    imurl: str
    
    def __enter__(self):
        self.filename = os.path.join("static", "images", "random.jpg")

        req = urllib.request.Request(self.imurl, headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_5_8) AppleWebKit/534.50.2 (KHTML, like Gecko) Version/5.0.6 Safari/533.22.3'})
        mediaContent = urllib.request.urlopen(req).read()
        with open(self.filename, "wb") as f:
            f.write(mediaContent)
        return self.filename

    def __exit__(self, type, value, traceback):
        os.remove(self.filename)

def get_num_pages(tags):
    pages_url = "https://safebooru.org/index.php?page=post&s=list&tags=%s" % "+".join(tags)
    tree = html.fromstring(requests.get(pages_url).content)
    try:
        finalpage_element = tree.xpath("/html/body/div[6]/div/div[2]/div[2]/div/a[12]")[0]
    except IndexError:
        return 1
    else:
        return int(int(urllib.parse.parse_qs(finalpage_element.get("href"))["pid"][0]) / (5*8))

def get_id_from_url(url):
    return int(urllib.parse.parse_qs(url)["id"][0])

def get_random_image(tags):
    global theLastId
    searchPage = random.randint(1, get_num_pages(tags)) * 5 * 8
    url = "https://safebooru.org/index.php?page=post&s=list&tags=%s&pid=%i" % ("+".join(tags), searchPage)
    tree = html.fromstring(requests.get(url).content)

    imageElements = [e for e in tree.xpath("/html/body/div[6]/div/div[2]/div[1]")[0].iter(tag = "a")]
    try:
        element = random.choice(imageElements)
    except IndexError:
        # raise ConnectionError("Couldn't find any images")
        return get_random_image(tags)

    url = "https://safebooru.org/" + element.get("href")
    if get_id_from_url(url) == theLastId:
        return get_random_image(tags)
    theLastId = get_id_from_url(url)

    try:
        sbi = SafebooruImage(
            id_ = get_id_from_url(url),
            url = url,
            tags = element.find("img").get("alt").split(),
            searchTags = tags,
            source = fix_source_url(get_source(url)),
            imurl = get_imurl(url)
        )
    except (ConnectionError, KeyError) as e:
        print("[ERROR]", e)
        return get_random_image(tags)

    if link_deleted(sbi.url):
        print("Retried since the source was deleted...")
        return get_random_image(tags)

    return sbi

def get_source(url):
    tree = html.fromstring(requests.get(url).content)
    for element in tree.xpath('//*[@id="stats"]')[0].iter("li"):
        if element.text.startswith("Source: h"):
            return element.text[8:]
        elif element.text.startswith("Source:"):
            for child in element.iter():
                if child.get("href") is not None:
                    return child.get("href")
    raise ConnectionError("Couldn't find source image for id %i" % get_id_from_url(url))

def fix_source_url(url):
    parsed = urllib.parse.urlparse(url)
    if parsed.netloc == "www.pixiv.net":
        return "https://www.pixiv.net/en/artworks/" + urllib.parse.parse_qs(parsed.query)["illust_id"][0]
    elif parsed.netloc in ["bishie.booru.org", "www.secchan.net"]:
        return ConnectionError("Couldn't get source")
    elif "pximg.net" in parsed.netloc or "pixiv.net" in parsed.netloc:
        return "https://www.pixiv.net/en/artworks/" + parsed.path.split("/")[-1][:8]
    elif parsed.netloc == "twitter.com":
        return url.replace("twitter.com", "nitter.eda.gay")
    return url

def get_imurl(url):
    tree = html.fromstring(requests.get(url).content)
    return tree.xpath('//*[@id="image"]')[0].get("src")

def link_deleted(url):
    text = requests.get(url).text
    return text[text.find("<title>") + 7 : text.find("</title>")] in ["Error | nitter", "イラストコミュニケーションサービス[pixiv]"]

def request_recent_commits(since = datetime.datetime.now() - datetime.timedelta(days=7)):
    g = Github(CONFIG.get("github", "access_code"))
    out = []
    for repo in g.get_user().get_repos():
        # print(repo.name, list(repo.get_branches()))
        try:
            for commit in repo.get_commits(since = since):
                out.append({
                    "repo": repo.name,
                    "message": commit.commit.message,
                    "url": commit.html_url,
                    "datetime": commit.commit.author.date,
                    "stats": {
                        "additions": commit.stats.additions,
                        "deletions": commit.stats.deletions,
                        "total": commit.stats.total
                    }
                })
        except Exception as e:
            print(e)

    return sorted(out, key = lambda a: a["datetime"], reverse = True) 

def scrape_nitter(username, get_until:int):
    new_tweets = []
    nitter_url = CONFIG.get("nitter", "internalurl")
    nitter_port = CONFIG.getint("nitter", "internalport")
    scrape_new_pages = True
    url = "http://%s:%d/%s" % (nitter_url, nitter_port, username)

    while scrape_new_pages:
        tree = html.fromstring(requests.get(url).content)
        for i, tweetUrlElement in enumerate(tree.xpath('//*[@class="tweet-link"]'), 0):
            if i > 0 and tweetUrlElement.get("href").split("/")[1] == username:
                id_ = int(urllib.parse.urlparse(tweetUrlElement.get("href")).path.split("/")[-1])
                tweet_link = "http://%s:%d%s" % (nitter_url, nitter_port, tweetUrlElement.get("href"))

                if id_ == get_until:
                    scrape_new_pages = False
                    break

                try:
                    dt, replying_to, text, images = parse_tweet(tweet_link)
                    new_tweets.append((id_, dt, replying_to, text, username, images))
                    print(dt, text)
                except IndexError:
                    print("Couldn't get any more tweets")
                    scrape_new_pages = False
                    break


        try:
            cursor = tree.xpath('//*[@class="show-more"]/a')[0].get("href")
        except IndexError:
            # no more elements
            break
        url = "http://%s:%d/%s%s" % (nitter_url, nitter_port, username, cursor)

    return new_tweets

def parse_tweet(tweet_url):
    # print(tweet_url)
    tree = html.fromstring(requests.get(tweet_url).content)
    # with open("2images.html", "r") as f:
    #     tree = html.fromstring(f.read())

    main_tweet_elem = tree.xpath('//*[@class="main-tweet"]')[0]

    dt_str = main_tweet_elem.xpath('//*[@class="tweet-published"]')[0].text
    dt = datetime.datetime.strptime(dt_str.replace("Â", ""), "%b %d, %Y · %I:%M %p UTC")
    text = tree.xpath('//*[@class="main-tweet"]/div/div/div[2]')[0].text
    replying_to_elems = tree.xpath('//*[@class="before-tweet thread-line"]/div/a')
    if replying_to_elems != []:
        replying_to = int(urllib.parse.urlparse(replying_to_elems[-1].get("href")).path.split("/")[-1])
    else:
        replying_to = None

    images = []
    images_elems = tree.xpath('//*[@class="main-tweet"]/div/div/div[3]/div/div/a/img')
    for image_elem in images_elems:
        images.append("https://" + CONFIG.get("nitter", "outsideurl") + urllib.parse.urlparse(image_elem.get("src")).path)

    return dt, replying_to, text, images





if __name__ == "__main__":
    # print(get_trans_stats())

    print(scrape_nitter(CONFIG.get("twitter", "diary_account"), 1694624180405260291))

    # print(parse_tweet("https://nitter.net/HONMISGENDERER/status/1694231618443981161#m"))
