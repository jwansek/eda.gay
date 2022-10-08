from urllib.parse import urlparse
from dataclasses import dataclass
from github import Github
from lxml import html
import configparser
import threading
import datetime
import requests
import twython
import pymysql
import random
import os
import re

@dataclass
class Database:
    safeLogin:bool = True   #automatically login with the user in the config file, who is read only
    user:str = None         #otherwise, login with the given username and passwd
    passwd:str = None

    def __enter__(self):
        self.config = configparser.ConfigParser()
        self.config.read("edaweb.conf")

        if self.safeLogin:
            self.__connection = pymysql.connect(
                **self.config["mysql"],
                charset = "utf8mb4"
            )
        else:
            self.__connection = pymysql.connect(
                user = self.user,
                passwd = self.passwd,
                host = self.config["mysql"]["host"],
                db = self.config["mysql"]["db"],
                charset = "utf8mb4"
            )
        return self

    def __exit__(self, type, value, traceback):
        self.__connection.close()

    def get_header_links(self):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT name, link FROM headerLinks ORDER BY name;")
            return cursor.fetchall()

    def get_image(self, imageName):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT alt, url FROM images WHERE imageName = %s;", (imageName, ))
            return cursor.fetchone()

    def get_pfp_images(self):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT alt, url FROM images WHERE pfp_img = 1;")
            return cursor.fetchall()

    def get_header_articles(self):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT articleName, link FROM headerArticles;")
            return cursor.fetchall()

    def get_all_categories(self):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT category_name FROM categories;")
            return [i[0] for i in cursor.fetchall()]

    def add_category(self, category):
        if not category in self.get_all_categories():
            with self.__connection.cursor() as cursor:
                cursor.execute("INSERT INTO categories (category_name) VALUES (%s);", (category, ))

            self.__connection.commit()
            return True
            
        return False

    def add_thought(self, category, title, markdown):
        with self.__connection.cursor() as cursor:
            cursor.execute("""
            INSERT INTO thoughts (category_id, title, markdown_text) 
            VALUES ((
                SELECT category_id FROM categories WHERE category_name = %s
            ), %s, %s);""", (category, title, markdown))
        self.__connection.commit()

    def get_thought(self, id_):
        with self.__connection.cursor() as cursor:
            cursor.execute("""
            SELECT categories.category_name, thoughts.title, thoughts.dt, thoughts.markdown_text 
            FROM thoughts INNER JOIN categories 
            ON thoughts.category_id = categories.category_id 
            WHERE thought_id = %s;""", (id_, ))
            return cursor.fetchone()

    def get_similar_thoughts(self, category, id_):
        with self.__connection.cursor() as cursor:
            cursor.execute("""
            SELECT thought_id, title, dt, category_name FROM thoughts 
            INNER JOIN categories ON thoughts.category_id = categories.category_id 
            WHERE category_name = %s AND thought_id != %s;""", 
            (category, id_))
            return cursor.fetchall()

    def get_featured_thoughts(self):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT thought_id, title FROM thoughts WHERE featured = 1;")
            return cursor.fetchall()

    def update_thought_markdown(self, id_, markdown):
        with self.__connection.cursor() as cursor:
            cursor.execute("UPDATE thoughts SET markdown_text = %s WHERE thought_id = %s;", (markdown, id_))
        self.__connection.commit()

    def get_categories_not(self, category_name):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT category_name FROM categories WHERE category_name != %s;", (category_name, ))
            return [i[0] for i in cursor.fetchall()]

    def get_all_thoughts(self):
        with self.__connection.cursor() as cursor:
            cursor.execute("""
            SELECT thought_id, title, dt, category_name FROM thoughts 
            INNER JOIN categories ON thoughts.category_id = categories.category_id;
            """)
            return cursor.fetchall()

    def get_cached_tweets(self, numToGet = None, recurse = True):
        with self.__connection.cursor() as cursor:
            if numToGet is not None:
                cursor.execute("SELECT text, url FROM twitterCache ORDER BY appended DESC LIMIT %s;", (numToGet, ))
            else:
                cursor.execute("SELECT text, url FROM twitterCache ORDER BY appended DESC;")
            if recurse:
                threading.Thread(target = update_cache).start()
            return list(cursor.fetchall())

    def update_twitter_cache(self, requested):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT DISTINCT url FROM twitterCache;")
            urls = [i[0] for i in cursor.fetchall()]
            for url, text in requested:
                if url not in urls:
                    cursor.execute("INSERT INTO twitterCache (text, url) VALUES (%s, %s);", (text, url))
        self.__connection.commit()

    def get_cached_commits(self, since = None, recurse = True):
        with self.__connection.cursor() as cursor:
            if since is not None:
                cursor.execute("SELECT message, url, commitTime, additions, deletions, total FROM commitCache WHERE commitTime > %s ORDER BY commitTime DESC;", (since, ))
            else:
                cursor.execute("SELECT message, url, commitTime, additions, deletions, total FROM commitCache ORDER BY commitTime DESC;")
            return [{
                "repo": urlparse(i[1]).path.split("/")[2],
                "message": i[0],
                "url": i[1],
                "datetime": i[2],
                "stats": {
                    "additions": i[3],
                    "deletions": i[4],
                    "total": i[5]
                }
            } for i in cursor.fetchall()]

    def update_commit_cache(self, requested):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT DISTINCT url FROM commitCache;")
            urls = [i[0] for i in cursor.fetchall()]
            for commit in requested:
                if commit["url"] not in urls:
                    cursor.execute("""
                    INSERT INTO commitCache (message, url, commitTime, additions, deletions, total)
                    VALUES (%s, %s, %s, %s, %s, %s)""",
                    (commit["message"], commit["url"], commit["datetime"], commit["stats"]["additions"], commit["stats"]["deletions"], commit["stats"]["total"])
                )
        self.__connection.commit()

    def get_last_commit_time(self):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT MAX(commitTime) FROM commitCache;")
            return cursor.fetchone()[0]

    def get_my_twitter(self):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT link FROM headerLinks WHERE name = 'twitter';")
            return cursor.fetchone()[0]

    def get_iso_cd_options(self):
        iso_dir = self.config.get("cds", "location")
        return [
            i
            for i in os.listdir(iso_dir)
            if os.path.splitext(i)[-1].lower() in [".iso"]
            and os.path.getsize(os.path.join(iso_dir, i)) < self.config.getint("cds", "maxsize")
        ]

    def append_cd_orders(self, iso, email, house, street, city, county, postcode, name):
        with self.__connection.cursor() as cursor:
            cursor.execute("""
            INSERT INTO cd_orders_2 (iso, email, house, street, city, county, postcode, name)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """, (iso, email, house, street, city, county, postcode, name))
            id_ = cursor.lastrowid
        self.__connection.commit()
        return id_

    def append_diary(self, tweet_id, tweeted_at, replying_to, tweet):
        with self.__connection.cursor() as cursor:
            cursor.execute("INSERT INTO diary VALUES (%s, %s, %s, %s);", (tweet_id, tweeted_at, replying_to, tweet))
        print("Appended diary with tweet '%s'" % tweet)

    def append_diary_images(self, tweet_id, imurl):
        with self.__connection.cursor() as cursor:
            cursor.execute("INSERT INTO diaryimages (tweet_id, link) VALUES (%s, %s);", (tweet_id, imurl))

    def get_diary(self, twitteracc = "FUCKEDUPTRANNY"):
        threading.Thread(target = update_cache).start()
        out = {}
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT tweet_id, tweeted_at, tweet FROM diary WHERE replying_to IS NULL ORDER BY tweeted_at DESC;")
            for tweet_id, tweeted_at, tweet_text in cursor.fetchall():
                # print(tweet_id, tweeted_at, tweet_text)
                out[tweeted_at] = [{
                    "text": tweet_text, 
                    "images": self.get_diary_image(tweet_id), 
                    "link": "https://%s/%s/status/%d" % (self.config.get("nitter", "domain"), twitteracc, tweet_id)
                }]

                next_tweet = self.get_child_tweets(tweet_id)
                while next_tweet is not None:
                    tweet, id_ = next_tweet
                    out[tweeted_at].append(tweet)
                    next_tweet = self.get_child_tweets(id_)
        
        return out

    def get_diary_image(self, tweet_id):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT link FROM diaryimages WHERE tweet_id = %s;", (tweet_id, ))
            return [i[0] for i in cursor.fetchall()]
        
    def get_child_tweets(self, parent_id, twitteracc = "FUCKEDUPTRANNY"):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT tweet_id, tweet FROM diary WHERE replying_to = %s;", (parent_id, ))
            out = cursor.fetchall()
        if out == ():
            return None
        
        out = out[0]
        id_ = out[0]
        return {"text": out[1], "images": self.get_diary_image(id_), "link": "https://%s/%s/status/%d" % (self.config.get("nitter", "domain"), twitteracc, id_)}, id_

    def get_newest_diary_tweet_id(self):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT MAX(tweet_id) FROM diary;")
            return cursor.fetchone()[0]

    def fetch_diary(self, twitteracc = "FUCKEDUPTRANNY"):
        twitter = twython.Twython(*dict(dict(self.config)["twitter"]).values())
        for tweet in twitter.search(q = "(from:%s)" % twitteracc, since_id = self.get_newest_diary_tweet_id())["statuses"]:
            tweet_id = tweet["id"]
            tweeted_at = datetime.datetime.strptime(tweet["created_at"], "%a %b %d %H:%M:%S %z %Y")
            replying_to = tweet["in_reply_to_status_id"]
            tweet_text = re.sub(r"https://t\.co/\w{10}", "", tweet["text"], 0, re.MULTILINE)
            
            if tweet["in_reply_to_screen_name"] == twitteracc or tweet["in_reply_to_screen_name"] is None:
                self.append_diary(tweet_id, tweeted_at, replying_to, tweet_text)

            if "media" in tweet["entities"].keys():
                associated_images = [
                    i["media_url_https"].replace("pbs.twimg.com", self.config.get("nitter", "domain") + "/pic") 
                    for i in tweet["entities"]["media"]
                ]
                for im in associated_images:
                    self.append_diary_images(tweet_id, im)

        self.__connection.commit()

def update_cache():
    # print("updating cache...")
    with Database() as db:
        db.fetch_diary()
        db.update_twitter_cache(request_recent_tweets(10000))
        # print("Done updating twitter cache...")
        db.update_commit_cache(request_recent_commits(since = db.get_last_commit_time()))
        # print("Done updating commit cache...")

CONFIG = configparser.ConfigParser()
CONFIG.read("edaweb.conf")

def request_recent_tweets(numToGet):
    tweets = []
    domain = "http://" + CONFIG.get("nitter", "domain")
    with Database() as db:
        for title, url in db.get_header_links():
            if title == "twitter":
                break
    tree = html.fromstring(requests.get(url).content)
    for i, tweetUrlElement in enumerate(tree.xpath('//*[@class="tweet-link"]'), 0):
        if i > 0:
            tweets.append((
                domain + tweetUrlElement.get("href"),
                tweetUrlElement.getparent().find_class("tweet-content media-body")[0].text
            ))
        if len(tweets) >= numToGet:
            break
    return tweets
            
def request_recent_commits(since = datetime.datetime.now() - datetime.timedelta(days=7)):
    g = Github(CONFIG.get("github", "access_code"))
    out = []
    for repo in g.get_user().get_repos():
        # print(repo.name, list(repo.get_branches()))
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
    return sorted(out, key = lambda a: a["datetime"], reverse = True) 


if __name__ == "__main__":
    with Database() as db:
        print(db.get_diary())
