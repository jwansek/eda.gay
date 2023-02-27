import datetime
import requests
import json

def get_curiouscat_qnas_after(name, last_timestamp = None):
    if last_timestamp is None:
        url = "https://curiouscat.live/api/v2/profile?username=%s&count=100" % (name)
    else:
        url = "https://curiouscat.live/api/v2/profile?username=%s&count=100&max_timestamp=%d" % (name, last_timestamp)

    req = requests.get(url)
    return req.json()["posts"]

def get_all_curiouscat_qnas(name):
    out = []
    period = get_curiouscat_qnas_after(name)
    out += period
    while len(period) == 100:       
        oldest = min([i["timestamp"] for i in period])
        period = get_curiouscat_qnas_after("jwnskanzkwk", last_timestamp = oldest - 1)

        out += period

    return post_process(out, name)

def get_all_curiouscat_qnas_before(name, min_dt):
    url = "https://curiouscat.live/api/v2/profile?username=%s&count=100&min_timestamp=%d" % (name, int(min_dt.timestamp()) + 1)
    req = requests.get(url)
    return post_process(req.json()["posts"], "name")

def post_process(cc, name):
    return [
        {
            "id": i["id"],
            "link": "https://curiouscat.me/%s/post/%d" % (name, i["id"]),
            "datetime": datetime.datetime.fromtimestamp(i["timestamp"]),
            "question": i["comment"],
            "answer": i["reply"]
        }
        for i in cc
    ]

if __name__ == "__main__":
    import database

    with database.Database() as db:
        print(db.append_curiouscat_qnas(get_all_curiouscat_qnas_before("jwnskanzkwk", db.get_biggest_curiouscat_timestamp())))