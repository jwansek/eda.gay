import argparse
from urllib.parse import urlparse
import webbrowser
import database
import getpass
import app
import re
import os

HEADER_INCREMENTER = 1
IMAGE_TYPES = [".png", ".jpg"]

def get_thought_from_id(db, id_):
    category_name, title, dt, markdown = db.get_thought(id_)
    return category_name, title, dt, parse_text(markdown)

def parse_file(path):
    with open(path, "r") as f:
        unformatted = f.read()

    return parse_text(unformatted)    

def parse_text(unformatted):
    formatted = parse_headers(unformatted)
    formatted = parse_asteriscs(formatted)
    formatted = parse_links(formatted)
    formatted = parse_code(formatted)
    formatted = parse_lists(formatted)
    formatted = add_linebreaks(formatted)

    return '{% extends "template.html" %}\n{% block content %}\n' + formatted + '\n{% endblock %}'

def parse_headers(test_str):
    regex = r"^#{1,5}\s\w.*$"
    matches = re.finditer(regex, test_str, re.MULTILINE)
    offset = 0

    for match in matches:
        # work out if its h2, h3 etc. from the number of #s
        headerNo = len(match.group().split(" ")[0]) + HEADER_INCREMENTER
        
        replacement = "<h%i>%s</h%i>" % (headerNo, " ".join(match.group().split(" ")[1:]), headerNo)

        #don't use .replace() in the unlikely case the the regex hit appears in a block
        test_str = test_str[:match.start()+offset] + replacement + test_str[match.end()+offset:]
        #replacing the hits fucks up the indexes, accommodate for this
        offset += (len(replacement) - (match.end() - match.start()))

    return test_str

def parse_asteriscs(test_str):
    regex = r"(?<!\\)\*{1,3}.*?\*{1,3}"
    matches = re.finditer(regex, test_str, re.MULTILINE)
    offset = 0

    for match in matches:
        if len(re.findall(r"\*{1,3}.*?\\\*{1,3}", match.group())) == 0:     #need to find a way of doing this with regexes
            if match.group().startswith(re.findall(r"\w\*{1,3}", match.group())[0][1:]):    #this too
                if match.group().startswith("***"):
                    replacement = "<b><i>%s</i></b>" % (match.group()[3:-3])
                elif match.group().startswith("**"):
                    replacement = "<b>%s</b>" % (match.group()[2:-2])
                else:
                    replacement = "<i>%s</i>" % (match.group()[1:-1])
        
                test_str = test_str[:match.start()+offset] + replacement + test_str[match.end()+offset:]
                offset += (len(replacement) - (match.end() - match.start()))

    return test_str

def parse_links(test_str):
    regex = r"(?<!\\)\[.*?\]\(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+\)"
    matches = re.finditer(regex, test_str, re.MULTILINE)
    offset = 0

    for match in matches:
        s = match.group().split("(")
        label = s[0][1:-1]
        url = s[1][:-1]

        if os.path.splitext(urlparse(url).path)[1] in IMAGE_TYPES:
            replacement = "<img alt='%s' src=%s>" % (label, url)
        else:
            replacement = "<a href=%s>%s</a>" % (url, label)

        test_str = test_str[:match.start()+offset] + replacement + test_str[match.end()+offset:]
        offset += (len(replacement) - (match.end() - match.start()))

    return test_str

def parse_code(test_str):
    regex = r"(?<!\\)`\w{1,}?`"
    # this only matches single words, but escaping is less complicated
    matches = re.finditer(regex, test_str, re.MULTILINE)
    offset = 0

    for match in matches:
        replacement = "<em class=inlineCode style='font-family: monospace;font-style: normal;'>%s</em>" % match.group()[1:-1]
        test_str = test_str[:match.start()+offset] + replacement + test_str[match.end()+offset:]
        offset += (len(replacement) - (match.end() - match.start()))

    out = ""
    inBlock = 0
    for line in test_str.split("\n"):
        if line == "```":
            if inBlock % 2 == 0:
                out += "<p class=codeBlock style='font-family: monospace;font-style: normal;white-space: pre-wrap;'>\n"
            else:
                out += "</p>\n"
            inBlock += 1
        else:
            out += line + "\n"

    return out

def parse_lists(test_str):
    regex = r"^[1-9][.)] .*$|- .*$"
    matches = re.finditer(regex, test_str, re.MULTILINE)
    offset = 0
    theFirstOne = True

    for match in matches:
        if theFirstOne:
            if match.group()[0].isdigit():
                listType = "ol"
                cutoff = 3
            else:
                listType = "ul"
                cutoff = 2
            replacement = "<%s>\n<li>%s</li>" % (listType, match.group()[cutoff:])
            theFirstOne = False
        else:
            if re.match(regex, [i for i in test_str[match.end()+offset:].split("\n") if i != ''][0]) is None:
                theFirstOne = True
                replacement = "<li>%s</li>\n</%s>" % (match.group()[cutoff:], listType)
            else:
                replacement = "<li>%s</li>" % match.group()[cutoff:]
        test_str = test_str[:match.start()+offset] + replacement + test_str[match.end()+offset:]
        offset += (len(replacement) - (match.end() - match.start()))

    return test_str

def add_linebreaks(test_str):
    return re.sub(r"^$", "<br><br>", test_str, 0, re.MULTILINE)

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
    p.add_argument(
        "markdown",
        help = "Path to a markdown file",
        type = str
    )
    p.add_argument(
        "-u", "--username",
        help = "Username to use for the database",
        required = True,
        type = str
    )
    p.add_argument(
        "-t", "--title",
        help = "Article title",
        required = True,
        type = str
    )
    p.add_argument(
        "-c", "--category",
        help = "Article category",
        required = True,
        type = str
    )
    g = p.add_mutually_exclusive_group(required = True)
    g.add_argument(
        "-p", "--preview",
        help = "Preview markdown rendering",
        action='store_true'
    )
    g.add_argument(
        "-s", "--save",
        help = "Save markdown to database",
        action='store_true'
    )
    g.add_argument(
        "-e", "--echo",
        help = "Print parsed markdown to stdout",
        action='store_true'
    )
    args = vars(p.parse_args())

    passwd = getpass.getpass("Enter password for %s@%s: " % (args["username"], app.CONFIG["mysql"]["host"]))

    with database.Database(
        safeLogin = False,
        user = args["username"],
        passwd = passwd
    ) as db:

        if args["preview"]:
            preview_markdown(args["markdown"], args["title"], args["category"])
        elif args["save"]:
            if db.add_category(args["category"]):
                print("Added category...")
            with open(args["markdown"], "r") as f:
                db.add_thought(args["category"], args["title"], f.read())
            print("Added thought...")
        else:
            print(parse_file(args["markdown"]))

if __name__ == "__main__":
    main()