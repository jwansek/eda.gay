import configparser
import database
import flask

app = flask.Flask(__name__)
CONFIG = configparser.ConfigParser()
CONFIG.read("edaweb.conf")

def get_template_items(title, db):
    return {
        "links": db.get_header_links(),
        "image": db.get_image("telegrampic"),
        "title": title,
        "articles": db.get_header_articles()
    }

@app.route("/")
def index():
    with database.Database() as db:
        return flask.render_template(
            "index.html", 
            **get_template_items("edaweb.co.uk", db)
        )

@app.route("/discord")
def discord():
    with database.Database() as db:
        return flask.render_template(
            "discord.html", 
            **get_template_items("Discord", db),
            discord = CONFIG["discord"]["username"]
        )

if __name__ == "__main__":
    app.run(host = "0.0.0.0", debug = True)
