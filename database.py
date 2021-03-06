from urllib.parse import urlparse
from dataclasses import dataclass
from github import Github
from lxml import html
import configparser
import threading
import datetime
import requests
import pymysql
import random
import os

@dataclass
class Database:
    safeLogin:bool = True   #automatically login with the user in the config file, who is read only
    user:str = None         #otherwise, login with the given username and passwd
    passwd:str = None

    def __enter__(self):
        config = configparser.ConfigParser()
        config.read("edaweb.conf")

        if self.safeLogin:
            self.__connection = pymysql.connect(
                **config["mysql"],
                charset = "utf8mb4"
            )
        else:
            self.__connection = pymysql.connect(
                user = self.user,
                passwd = self.passwd,
                host = config["mysql"]["host"],
                db = config["mysql"]["db"],
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
        urls = [i[1] for i in self.get_cached_tweets(recurse = False)]
        with self.__connection.cursor() as cursor:
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
        urls = [i["url"] for i in self.get_cached_commits(recurse = False)]
        with self.__connection.cursor() as cursor:
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

def update_cache():
    # print("updating cache...")
    with Database() as db:
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
    import datetime
    start = datetime.datetime.now()
    with Database() as db:
        print(db.get_cached_tweets())
        print("Took: ", (datetime.datetime.now() - start))