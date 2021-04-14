from paste.translogger import TransLogger
from waitress import serve
from PIL import Image
import configparser
import webbrowser
import datetime
import database
import services
import urllib
import random
import parser
import flask
import sys
import os
import io

app = flask.Flask(__name__)
CONFIG = configparser.ConfigParser()
CONFIG.read("edaweb.conf")
shown_images = set()

def get_pfp_img(db:database.Database):
    global shown_images
    dbimg = db.get_pfp_images()
    if len(shown_images) == len(dbimg):
        shown_images = set()
    folder = set(dbimg).difference(shown_images)
    choice = random.choice(list(folder))
    shown_images.add(choice)
    return choice

def get_correct_article_headers(db:database.Database, title):
    db_headers = list(db.get_header_articles())
    if title in [i[0] for i in db_headers]:
        out = []
        for i in db_headers:
            if i[0] != title:
                out.append(i)
        return out + [("index", "/")]
    else:
        return db_headers + [("index", "/")]

def get_template_items(title, db):
    return {
        "links": db.get_header_links(),
        "image": get_pfp_img(db),
        "title": title,
        "articles": get_correct_article_headers(db, title)
    }

@app.route("/")
def index():
    with database.Database() as db:
        recentTweets = []
        with open(os.path.join("static", "index.md"), "r") as f:
            return flask.render_template(
                "index.html", 
                **get_template_items("eden's site :3", db),
                markdown = parser.parse_text(f.read()),
                featured_thoughts = db.get_featured_thoughts(),
                tweets = db.get_cached_tweets(7) + [("view all tweets...", db.get_my_twitter())],
                commits = db.get_cached_commits(since = datetime.datetime.now() - datetime.timedelta(days = 7))
            )

@app.route("/robots.txt")
def robots():
    return flask.send_from_directory("static", "robots.txt")

@app.route("/discord")
def discord():
    with database.Database() as db:
        return flask.render_template(
            "discord.html", 
            **get_template_items("discord", db),
            discord = CONFIG["discord"]["username"]
        )

@app.route("/services")
def serve_services():
    with database.Database() as db:
        return flask.render_template(
            "services.html",
            **get_template_items("services", db),
            docker = services.get_docker_stats(),
            qbit = services.get_qbit_stats(),
            trans = services.get_trans_stats(),
            pihole = services.get_pihole_stats()
        )

@app.route("/thought")
def get_thought():
    thought_id = flask.request.args.get("id", type=int)
    with database.Database() as db:
        try:
            category_name, title, dt, parsed = parser.get_thought_from_id(db, thought_id)
        except TypeError:
            flask.abort(404)
            return
        return flask.render_template_string(
            '{% extends "template.html" %}\n{% block content %}\n' + parsed + '\n{% endblock %}',
            **get_template_items(title, db),
            thought = True,
            dt = "published: " + str(dt),
            category = category_name,
            othercategories = db.get_categories_not(category_name),
            related = db.get_similar_thoughts(category_name, thought_id)
        )

@app.route("/thoughts")
def get_thoughts():
    with database.Database() as db:
        all_ = db.get_all_thoughts()
        tree = {}
        for id_, title, dt, category in all_:
            if category not in tree.keys():
                tree[category] = [(id_, title, dt)]
            else:
                tree[category].append((id_, title, str(dt)))

        return flask.render_template(
            "thoughts.html",
            **get_template_items("thoughts", db),
            tree = tree
        )

@app.route("/img/<filename>")
def serve_image(filename):
    imdirpath = os.path.join(".", "static", "images")
    if filename in os.listdir(imdirpath):
        try:
            w = int(flask.request.args['w'])
            h = int(flask.request.args['h'])
        except (KeyError, ValueError):
            return flask.send_from_directory(imdirpath, filename)

        img = Image.open(os.path.join(imdirpath, filename))
        img.thumbnail((w, h), Image.ANTIALIAS)
        io_ = io.BytesIO()
        img.save(io_, format='JPEG')
        return flask.Response(io_.getvalue(), mimetype='image/jpeg')
    else:
        flask.abort(404)

@app.route("/random")
def serve_random():
    try:
        tags = flask.request.args['tags'].split(" ")
    except KeyError:
        flask.abort(400)
    
    sbi = services.get_random_image(tags)
    req = urllib.request.Request(sbi.imurl)
    mediaContent = urllib.request.urlopen(req).read()
    with open(os.path.join("static", "images", "random.jpg"), "wb") as f:
        f.write(mediaContent)

    with database.Database() as db:
        return flask.render_template(
            "random.html",
            **get_template_items("random image", db),
            sbi = sbi,
            localimg = "/img/random.jpg?seed=%i" % random.randint(0, 9999)
        )


@app.route("/preview")
def preview():
    if "PREVIEW" in os.environ:
        with database.Database() as db:
            return flask.render_template_string(
                 '{% extends "template.html" %}\n{% block content %}\n' + os.environ["PREVIEW"] + '\n{% endblock %}',
                **get_template_items(os.environ["PREVIEW_TITLE"], db),
                thought = True,
                dt = "preview rendered: " + str(datetime.datetime.now()),
                category = os.environ["CATEGORY"],
                othercategories = db.get_categories_not(os.environ["CATEGORY"])
            )
    else:
        flask.abort(404)

if __name__ == "__main__":
    try:
        if sys.argv[1] == "--production":
            #serve(TransLogger(app), host='127.0.0.1', port = 6969)
            serve(TransLogger(app), host='0.0.0.0', port = 6969, threads = 8)
        else:
            app.run(host = "0.0.0.0", port = 5001, debug = True)
    except IndexError:
        app.run(host = "0.0.0.0", port = 5001, debug = True)
