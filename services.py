import multiprocessing
import qbittorrent
import datetime
import docker
import clutch
import pihole
import queue
import json
import time
import app

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

        t.join(timeout = app.CONFIG["servicetimeout"].getint("seconds"))

        # print("Request took:", time.time() - ti)
        try:
            return returnVan[0]
        except IndexError:
            if t.is_alive():
                t.terminate()

    return beginTimeout

@timeout
def get_docker_stats():

    client = docker.DockerClient(base_url = "tcp://%s:%s" % (app.CONFIG["docker"]["url"], app.CONFIG["docker"]["port"]))
    return {
        container.name: container.status
        for container in client.containers.list(all = True)
    }

@timeout
def get_qbit_stats():
    numtorrents = 0
    bytes_dl = 0
    bytes_up = 0
    qb = qbittorrent.Client('http://%s:%s/' % (app.CONFIG["qbittorrent"]["url"], app.CONFIG["qbittorrent"]["port"]))
    qb.login(username = app.CONFIG["qbittorrent"]["user"], password = app.CONFIG["qbittorrent"]["passwd"])

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
        address = "http://%s:%s/transmission/rpc" % (app.CONFIG["transmission"]["url"], app.CONFIG["transmission"]["port"]),
        username = app.CONFIG["transmission"]["user"],
        password = app.CONFIG["transmission"]["passwd"]
    )
    stats = json.loads(client.session.stats().json())
    return {
       "bytes_dl": humanbytes(stats["arguments"]["cumulative_stats"]["downloaded_bytes"]),
       "bytes_up": humanbytes(stats["arguments"]["cumulative_stats"]["uploaded_bytes"]),
       "num": stats["arguments"]["torrent_count"],
       "ratio": "%.3f" % (float(stats["arguments"]["cumulative_stats"]["uploaded_bytes"]) / float(stats["arguments"]["cumulative_stats"]["downloaded_bytes"]))
    }

@timeout
def get_pihole_stats():
    ph = pihole.PiHole(app.CONFIG["pihole"]["url"])
    return {
        "status": ph.status,
        "queries": ph.total_queries,
        "clients": ph.unique_clients,
        "percentage": ph.ads_percentage,
        "blocked": ph.blocked,
        "domains": ph.domain_count,
        "last_updated": str(datetime.datetime.fromtimestamp(ph.gravity_last_updated["absolute"]))
    }


if __name__ == "__main__":
    print(get_pihole_stats())