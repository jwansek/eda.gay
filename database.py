from urllib.parse import urlparse
from dataclasses import dataclass
from lxml import html
import configparser
import curiouscat
import threading
import services
import operator
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
        self.config = configparser.ConfigParser(interpolation = None)
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
        self.__connection.commit()
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

    def get_sidebar_images(self):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT alt, url FROM images WHERE sidebar_image = 1;")
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
            SELECT categories.category_name, thoughts.title, thoughts.dt, thoughts.markdown_text, thoughts.redirect 
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

    def get_cached_tweets(self, numToGet = None):
        with self.__connection.cursor() as cursor:
            sql = "SELECT tweet, tweet_id, account FROM diary WHERE account = %s ORDER BY tweeted_at"
            args = (self.config.get("twitter", "main_account"), )
            if numToGet is not None:
                sql += " LIMIT %s;"
                args = (self.config.get("twitter", "main_account"), numToGet)
            else:
                sql += ";"
            cursor.execute(sql, args)

            return [(i[0], "https://%s/%s/status/%d" % (self.config.get("nitter", "outsideurl"), i[2], i[1])) for i in cursor.fetchall()]

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

    def get_my_diary_twitter(self):
        return self.config.get("twitter", "diary_account")

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

    def append_diary(self, tweet_id, tweeted_at, replying_to, tweet, account):
        if tweet is None:
            tweet = "(Image only)"
        with self.__connection.cursor() as cursor:
            cursor.execute("INSERT INTO diary VALUES (%s, %s, %s, %s, %s);", (tweet_id, tweeted_at, replying_to, tweet, account))
        self.__connection.commit()

        print("Appended diary with tweet " + tweet + " @ " + str(tweeted_at))

    def append_diary_images(self, tweet_id, imurl):
        with self.__connection.cursor() as cursor:
            cursor.execute("INSERT INTO diaryimages (tweet_id, link) VALUES (%s, %s);", (tweet_id, imurl))
        self.__connection.commit()
        

    def get_diary(self, account = None):
        threading.Thread(target = update_cache).start()
        out = {}
        if account is None:
            account = self.get_my_diary_twitter()

        with self.__connection.cursor() as cursor:
            # cursor.execute("SELECT tweet_id, tweeted_at, tweet FROM diary WHERE replying_to IS NULL ORDER BY tweeted_at DESC;")
            # attempt to ignore curiouscat automatic tweets by comparing with the q&a table
            cursor.execute("SELECT tweet_id, tweeted_at, tweet FROM diary WHERE replying_to IS NULL AND tweet_id NOT IN (SELECT tweet_id FROM diary INNER JOIN qnas ON SUBSTRING(tweet, 1, 16) = SUBSTRING(question, 1, 16)) AND account = %s ORDER BY tweeted_at DESC;", (account, ))
            for tweet_id, tweeted_at, tweet_text in cursor.fetchall():
                # print(tweet_id, tweeted_at, tweet_text)
                out[tweeted_at] = [{
                    "text": tweet_text, 
                    "images": self.get_diary_image(tweet_id), 
                    "link": "https://%s/%s/status/%d" % (
                        self.config.get("nitter", "outsideurl"), 
                        self.get_my_diary_twitter(), 
                        tweet_id
                    )
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
        
    def get_child_tweets(self, parent_id):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT tweet_id, tweet FROM diary WHERE replying_to = %s;", (parent_id, ))
            out = cursor.fetchall()
        if out == ():
            return None
        
        out = out[0]
        id_ = out[0]
        return {
            "text": out[1], 
            "images": self.get_diary_image(id_), 
            "link": "https://%s/%s/status/%d" % (
                self.config.get("nitter", "outsideurl"), self.get_my_diary_twitter(), id_
            )
        }, id_

    def get_newest_diary_tweet_id(self, account = None):
        if account is None:
            account = self.get_my_diary_twitter()
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT MAX(tweet_id) FROM diary WHERE account = %s;", (account, ))
            return cursor.fetchone()[0]

    def get_curiouscat_username(self):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT link FROM headerLinks WHERE name = 'curiouscat';")
        return urlparse(cursor.fetchone()[0]).path.split("/")[1]

    def append_curiouscat_qnas(self, qnas):
        with self.__connection.cursor() as cursor:
            for qna in qnas:
                cursor.execute("SELECT curiouscat_id FROM qnas WHERE curiouscat_id = %s;", (qna["id"], ))
                if cursor.fetchone() is None:

                    cursor.execute("INSERT INTO `qnas` VALUES (%s, %s, %s, %s, %s);", (
                        qna["id"], qna["link"], qna["datetime"], qna["question"], qna["answer"]
                    ))
                    print("Appended question with timestamp %s" % datetime.datetime.fromtimestamp(qna["id"]).isoformat())

                else:
                    print("Skipped question with timestamp %s" % datetime.datetime.fromtimestamp(qna["id"]).isoformat())
        self.__connection.commit()

    def get_biggest_curiouscat_timestamp(self):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT MAX(`timestamp`) FROM `qnas`;")
            return cursor.fetchone()[0]

    def get_curiouscat_qnas(self):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT * FROM qnas;")
            return sorted(cursor.fetchall(), key = operator.itemgetter(2), reverse = True)

def update_cache():
    print("Updating cache...")
    with Database() as db:
        db.append_curiouscat_qnas(
            curiouscat.get_all_curiouscat_qnas_before(
                db.get_curiouscat_username(), 
                db.get_biggest_curiouscat_timestamp()
            )
        )
        print("Finished adding curiouscat...")
        db.update_commit_cache(services.request_recent_commits(since = db.get_last_commit_time()))
        print("Finished adding github commits...")
        for id_, dt, replying_to, text, username, images in services.scrape_nitter(db.get_my_diary_twitter(), db.get_newest_diary_tweet_id()):
            db.append_diary(id_, dt, replying_to, text, username)
            for image in images:
                db.append_diary_images(id_, image)
        print("Finished getting diary tweets...")
        for id_, dt, replying_to, text, username, images in services.scrape_nitter(
            db.config.get("twitter", "main_account"), db.get_newest_diary_tweet_id(db.config.get("twitter", "main_account"))
            ):
            db.append_diary(id_, dt, replying_to, text, username)
            for image in images:
                db.append_diary_images(id_, image)
    print("Done updating commit cache...")


if __name__ == "__main__":
    with Database() as db:
        print(db.get_cached_tweets())

    # update_cache()
