#!/usr/bin/python3

from bs4 import BeautifulSoup
from multiprocessing import Pool
from sys import stdout
from urllib.parse import urljoin, quote
from urllib.request import urlopen
import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument('cc', help='Country code for your Wikipedia (e.g. en, de)')
parser.add_argument('start', metavar='from', help='Name of the article you start with')
parser.add_argument('end', metavar='to', help='Name of the destination article')
args = parser.parse_args()

wikiurl = 'https://'+args.cc+'.wikipedia.org/wiki/'

# TODO: testen ob start und zielartikel existieren (BEIDE!)

def urlencode(text):
    return quote(text.replace(" ", "_"))


class Page:
    def __init__(self, url):
        self.url = url
        self.fetched = False
        self.children = []
        self.title = "?"+url.rsplit("/", 1)[-1]
        self.processed = False
        self.route = []

    def fetch(self) -> None:
        if self.fetched:
            return
        self.fetched = True

        html = urlopen(self.url).read()
        document = BeautifulSoup(html, features="lxml")

        self.title = str(document.find_all(id="firstHeading")[0].contents[0])
        article = document.find_all(id="mw-content-text")[0]
        body = document.find_all(id="mw-content-text")[0]
        self.children = [get_page_cached(urljoin(self.url, x["href"].rsplit("#",1)[0])) for x in body.find_all("a") if x.has_attr("href") and x["href"].startswith("/wiki/") and not ':' in x["href"]]


# # We need this because Pool.map does not take lambdas for whatever reason
# class Fetcher(object):
    # def __init__(self):
        # self.page = page
    # def __call__(self, page: Page):
        # page.fetch()


known_pages = {}


def get_page_cached(url: str) -> Page:
    if url in known_pages:
        return known_pages[url]
    else:
        return Page(url)


def print_line(text: str) -> None:
    termwidth = os.get_terminal_size().columns
    if len(text) > termwidth:
        ext = "... "+str(len(text))
        text = text[:termwidth-len(ext)] + ext
    print(text)


def route_to_str(path: []) -> str:
    first = True
    result = ""
    for elem in path:
        if not first:
            result += " -> "
        else:
            first = False
        result += elem
    return result


surl = wikiurl+urlencode(args.start)
queue = [get_page_cached(surl)]
known_pages[surl] = queue[0]
qend = urlencode(args.end)
shortest = []
count = 0
while len(queue) > 0:
    count += 1
    page = queue[0]
    queue = queue[1:]

    if page.processed:
        continue
    page.processed = True
    page.fetch()

    route = page.route + [page.title]

    ctitles = [child.title for child in page.children]
    if "?"+qend in ctitles:
        print("Possible hit!")
        child = [c for c in page.children if c.title == "?"+qend][0]
        print("> "+child.title)
        child.fetch()
        if child.title == args.end:
            shortest = route + [child.title]
            break

    if page.title == args.end:
        shortest = route
        break
    old = len(queue)
    for child in page.children:
        if not child.url in known_pages:
            child.route = route
            known_pages[child.url] = child
            queue += [child]
    print_line(str(count) + " | "+ str(len(queue)) + " | " + str(len(queue)-old) + "/" + str(len(page.children)) + " ("+ "%.f" % (0 if old == 0 else 100*(len(queue)-old)/len(page.children)) +"%) | " + route_to_str(route) + " -> "+str(ctitles))

print("\n")

if shortest == []:
    print("No route found")
    exit(1)

print(route_to_str(shortest))

