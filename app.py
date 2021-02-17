from PIL import Image
import configparser
import webbrowser
import datetime
import database
import services
import parser
import flask
import os
import io

app = flask.Flask(__name__)
CONFIG = configparser.ConfigParser()
CONFIG.read("edaweb.conf")

def get_template_items(title, db):
    return {
        "links": db.get_header_links(),
        "image": db.get_pfp_image(),
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
        category_name, title, dt, parsed = parser.get_thought_from_id(db, thought_id)
        return flask.render_template_string(
            parsed,
            **get_template_items(title, db),
            thought = True,
            dt = "published: " + str(dt),
            category = category_name,
            othercategories = db.get_categories_not(category_name)
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


@app.route("/preview")
def preview():
    if "PREVIEW" in os.environ:
        with database.Database() as db:
            return flask.render_template_string(
                os.environ["PREVIEW"],
                **get_template_items(os.environ["PREVIEW_TITLE"], db),
                thought = True,
                dt = "preview rendered: " + str(datetime.datetime.now()),
                category = os.environ["CATEGORY"],
                othercategories = db.get_categories_not(os.environ["CATEGORY"])
            )
    else:
        flask.abort(404)

    

if __name__ == "__main__":
    app.run(host = "0.0.0.0", debug = True)
