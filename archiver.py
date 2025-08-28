#! /usr/bin/env python3

import argparse
import mimetypes
import os

from defusedxml.minidom import parseString
# NOTE: maybe use lxml or ElementTree instead?

import requests

DEFAULT_EXTENSION = ".mp3"
DOWNLOAD_CHUNK_SIZE = 128

def download_podcast(xml_url, limit):
    r = requests.get(xml_url)
    dom = parseString(r.text)
    channel_titles = dom.getElementsByTagName("title")

    # TODO: catch index errors for all of these.
    directory = channel_titles[0].childNodes[0].data

    # TODO: Handle case where the directory already exists.
    # TODO: Sanitize directory name.
    os.mkdir(directory)

    episodes = dom.getElementsByTagName("item")
    count = 1
    for episode in episodes:
        enclosure = episode.getElementsByTagName("enclosure")[0]
        audio_url = enclosure.getAttribute("url")
        audio_type = enclosure.getAttribute("type")
        published_date = episode.getElementsByTagName("pubDate")[0].childNodes[0].data
        title = episode.getElementsByTagName("title")[0].childNodes[0].data

        download_episode(audio_url, audio_type, directory + "/" + title, published_date)

        if limit:
            if count == limit:
                break

        count += 1


def download_episode(audio_url, audio_type, title, published_date):
    extension = mimetypes.guess_extension(audio_type) or DEFAULT_EXTENSION

    print(f"downloading {title} from {published_date} \n")

    file_request = requests.get(audio_url)

    with open(title + extension, "wb") as fd:
        # WARN: This automatically unzips content, making us succeptible to zip bomb attacks.
        for chunk in file_request.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
            fd.write(chunk)


def main():
    parser = argparse.ArgumentParser(description="Podcast archiver")
    parser.add_argument("rss_url", type=str, help="URL of the RSS feed")
    parser.add_argument("--limit", type=str, help="maximum number of episodes to download", default=2)
    args = parser.parse_args()

    download_podcast(args.rss_url, args.limit)


if __name__ == "__main__":
    main()
