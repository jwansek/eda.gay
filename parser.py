#!/usr/bin/env python3

from urllib.parse import urlparse
from pygments import highlight
from pygments.formatters import HtmlFormatter, ClassNotFound
from pygments.lexers import get_lexer_by_name
import webbrowser
import database
import argparse
import getpass
import houdini
import misaka
import app
import sys
import re
import os

class HighlighterRenderer(misaka.SaferHtmlRenderer):
    def blockcode(self, text, lang):
        try:
            lexer = get_lexer_by_name(lang, stripall=True)
        except ClassNotFound:
            lexer = None

        if lexer:
            formatter = HtmlFormatter()
            return highlight(text, lexer, formatter)
        # default
        return '\n<pre><code>{}</code></pre>\n'.format(houdini.escape_html(text.strip()))

    def blockquote(self, content):
        content = content[3:-5] # idk why this is required...
        out = '\n<blockquote>'
        for line in houdini.escape_html(content.strip()).split("\n"):
            out += '\n<span class="quote">{}</span><br>'.format(line)
        return out + '\n</blockquote>'

    def image(self, link, title, alt):
        return "<a href='%s' target='_blank'><img alt='%s' src='%s'></a>" % (
            urlparse(link)._replace(query='').geturl(), alt, link
        )

def get_thought_from_id(db, id_):
    category_name, title, dt, markdown = db.get_thought(id_)
    return category_name, title, dt, parse_text(markdown)

def parse_file(path):
    with open(path, "r") as f:
        unformatted = f.read()

    return parse_text(unformatted)    

def parse_text(unformatted):
    renderer = HighlighterRenderer()
    md = misaka.Markdown(renderer, extensions=('fenced-code', 'quote'))

    return md(unformatted)

def preview_markdown(path, title, category):
    def startBrowser():
        webbrowser.get("firefox").open("http://localhost:5000/preview")
        del os.environ["PREVIEW"]
        del os.environ["PREVIEW_TITLE"]
        del os.environ["CATEGORY"]

    os.environ["PREVIEW"] = parse_file(path)
    os.environ["PREVIEW_TITLE"] = title
    os.environ["CATEGORY"] = category

    import threading
    threading.Timer(1.25, startBrowser ).start()
    
    app.app.run(host = "0.0.0.0", debug = True)

def main():
    p = argparse.ArgumentParser()
    subparse = p.add_subparsers(help = "sub-command help")
    save_parser = subparse.add_parser("save", help = "Add a markdown file to the database")
    preview_parser = subparse.add_parser("preview", help = "Preview a markdown render")
    echo_parser = subparse.add_parser("echo", help = "Print markdown render to stdout")
    update_parser = subparse.add_parser("update", help = "Replace a markdown file")
    export_parser = subparse.add_parser("export", help = "Export a database markdown file to disk")

    for s in [save_parser, preview_parser, echo_parser, update_parser]:
        s.add_argument(
            "-m", "--markdown",
            help = "Path to a markdown file",
            type = str,
            required = True
        )
    
    for s in [save_parser, preview_parser]:
        s.add_argument(
            "-t", "--title",
            help = "Article title",
            type = str,
            required = True
        )
        s.add_argument(
            "-c", "--category",
            help = "Article category",
            type = str,
            required = True
        )

    for s in [save_parser, update_parser, export_parser]:
        s.add_argument(
            "-u", "--username",
            help = "Username to use for the database",
            type = str,
            required = True
        )

    for s in [export_parser, update_parser]:
        s.add_argument(
            "-i", "--id",
            help = "Article's id",
            type = int,
            required = True
        )

    export_parser.add_argument(
        "-o", "--out",
        help = "Path to write the markdown file to",
        type = str,
        required = True
    )

    args = vars(p.parse_args())

    if "username" in args.keys():
        args["password"] = getpass.getpass("Enter password for %s@%s: " % (args["username"], app.CONFIG["mysql"]["host"]))

    try:
        verb = sys.argv[1]
    except IndexError:
        print("No verb specified... Nothing to do... Exiting...")
        exit()
    
    if verb in ["save", "export", "update"]:
        with database.Database(
            safeLogin = False,
            user = args["username"],
            passwd = args["password"]
        ) as db:
            if verb == "save":
                if db.add_category(args["category"]):
                    print("Added category...")
                with open(args["markdown"], "r") as f:
                    db.add_thought(args["category"], args["title"], f.read())
                print("Added thought...")

            elif verb == "export":
                with open(args["out"], "w") as f:
                    f.writelines(db.get_thought(args["id"])[-1])
                print("Written to %s" % args["out"])

            elif verb == "update":
                with open(args["markdown"], "r") as f:
                    db.update_thought_markdown(args["id"], f.read())

    if verb == "preview":
        preview_markdown(args["markdown"], args["title"], args["category"])

    elif verb == "echo":
        print(parse_file(args["markdown"]))

if __name__ == "__main__":
    main()
