import argparse
from urllib.parse import urlparse
import webbrowser
import app
import re
import os

HEADER_INCREMENTER = 1
IMAGE_TYPES = [".png", ".jpg"]

def parse_file(path):
    with open(path, "r") as f:
        unformatted = f.read()

    formatted = parse_headers(unformatted)
    formatted = parse_asteriscs(formatted)
    formatted = parse_links(formatted)
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

def add_linebreaks(test_str):
    return re.sub(r"^$", "<br><br>", test_str, 0, re.MULTILINE)

def preview_markdown(path, title):
    def startBrowser():
        webbrowser.get("firefox").open("http://localhost:5000/preview")
        del os.environ["PREVIEW"]
        del os.environ["PREVIEW_TITLE"]

    os.environ["PREVIEW"] = parse_file(path)
    os.environ["PREVIEW_TITLE"] = title

    import threading
    threading.Timer(1.25, startBrowser ).start()
    
    app.app.run(host = "0.0.0.0", debug = True)

def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        "-m", "--markdown",
        help = "Path to a markdown file",
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
        "-p", "--preview",
        help = "Preview markdown rendering",
        action='store_true'
    )
    args = vars(p.parse_args())
    if args["preview"]:
        preview_markdown(args["markdown"], args["title"])
    else:
        print(parse_file(args["markdown"]))

if __name__ == "__main__":
    main()