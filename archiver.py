#! /usr/bin/env python3

import argparse
import logging
import mimetypes
from pathlib import Path

from defusedxml.minidom import parseString
# NOTE: maybe use lxml or ElementTree instead?

import requests

DEFAULT_EXTENSION = ".mp3"
DEFAULT_MAX_EPISODES = 2
DOWNLOAD_CHUNK_SIZE = 128


def download_podcast(xml_url: str, limit: int | None = None) -> None:
    r = requests.get(xml_url)
    dom = parseString(r.text)
    channel_titles = dom.getElementsByTagName("title")

    # TODO: catch index errors for all of these.
    directory_name = channel_titles[0].childNodes[0].data

    # TODO: Sanitize directory name.
    directory = Path(directory_name)
    directory.mkdir(exist_ok=True)

    episodes = dom.getElementsByTagName("item")
    count = 1
    for episode in episodes:
        enclosure = episode.getElementsByTagName("enclosure")[0]
        audio_url = enclosure.getAttribute("url")
        audio_type = enclosure.getAttribute("type")
        published_date = episode.getElementsByTagName("pubDate")[0].childNodes[0].data
        title = episode.getElementsByTagName("title")[0].childNodes[0].data

        download_episode(audio_url, audio_type, directory, title, published_date)

        if limit:
            if count == limit:
                break

        count += 1


def download_episode(
    audio_url: str,
    audio_type: str,
    parent_directory: Path,
    title: str,
    published_date: str,
) -> None:
    extension = mimetypes.guess_extension(audio_type) or DEFAULT_EXTENSION
    path = Path(parent_directory, title).with_suffix(extension)

    logging.info(f"downloading {title} from {published_date} \n")

    file_request = requests.get(audio_url)

    with open(path, "wb") as fd:
        # WARN: This automatically unzips content, making us succeptible to zip bomb attacks.
        for chunk in file_request.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
            fd.write(chunk)


def main() -> None:
    parser = argparse.ArgumentParser(description="Podcast archiver")
    parser.add_argument("rss_url", type=str, help="URL of the RSS feed")
    parser.add_argument(
        "--limit",
        type=str,
        help="maximum number of episodes to download",
        default=DEFAULT_MAX_EPISODES,
    )
    parser.add_argument(
        "--verbose",
        type=str,
        help="verbose logging",
        default=logging.WARNING,
        nargs="?",
        const=logging.INFO,
    )
    args = parser.parse_args()

    logging.basicConfig(level=args.verbose)
    download_podcast(args.rss_url, args.limit)


if __name__ == "__main__":
    main()
