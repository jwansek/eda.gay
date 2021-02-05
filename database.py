import pymysql
import app

class Database:
    def __enter__(self):
        self.__connection = pymysql.connect(
            **app.CONFIG["mysql"],
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

    def get_header_articles(self):
        with self.__connection.cursor() as cursor:
            cursor.execute("SELECT articleName, link FROM headerArticles;")
            return cursor.fetchall()


if __name__ == "__main__":
    with Database() as db:
        print(db.get_image("headerImage"))