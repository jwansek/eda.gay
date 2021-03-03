from dataclasses import dataclass
import configparser
import pymysql
import random

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

if __name__ == "__main__":
    with Database() as db:
        print(db.get_header_articles())