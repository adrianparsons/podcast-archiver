#! /usr/bin/env python3

import argparse
from datetime import datetime
import logging
import mimetypes
from pathlib import Path

from defusedxml.minidom import parseString
# NOTE: maybe use lxml or ElementTree instead?

from dateutil.parser import parse
import requests

DEFAULT_EXTENSION = ".mp3"
DEFAULT_MAX_EPISODES = -1
DOWNLOAD_CHUNK_SIZE = 128


def download_podcast(xml_url: str, limit: int, skip: int) -> None:
    r = requests.get(xml_url)
    dom = parseString(r.text)
    channel_titles = dom.getElementsByTagName("title")

    # TODO: catch index errors for all of these.
    directory_name = channel_titles[0].childNodes[0].data

    # TODO: Sanitize directory name.
    directory = Path(directory_name)
    directory.mkdir(exist_ok=True)

    episodes = dom.getElementsByTagName("item")
    count = 0

    for episode in episodes:
        enclosure = episode.getElementsByTagName("enclosure")[0]
        audio_url = enclosure.getAttribute("url")
        audio_type = enclosure.getAttribute("type")
        title = (
            episode.getElementsByTagName("title")[0]
            .childNodes[0]
            .data.replace("/", "_")
        )
        published_date_raw = (
            episode.getElementsByTagName("pubDate")[0].childNodes[0].data
        )
        published_date = parse(published_date_raw)

        count += 1

        if limit != -1 and limit == count:
            logging.info(f"hit limit of {limit} at count of {count}, episode {title}")
            break

        if skip != -1 and skip >= count:
            logging.info(f"skipping to #{limit}, count of {count}, episode {title}")
            continue

        download_episode(audio_url, audio_type, directory, title, published_date)


def download_episode(
    audio_url: str,
    audio_type: str,
    parent_directory: Path,
    title: str,
    published_date: datetime,
) -> None:
    extension = mimetypes.guess_extension(audio_type) or DEFAULT_EXTENSION
    published_date_iso = published_date.date().isoformat()
    path = Path(parent_directory, f"{published_date_iso} {title}").with_suffix(
        extension
    )

    logging.info(f"downloading {title} from {published_date.strftime('%B %d, %Y')} \n")

    response = requests.get(audio_url, stream=True)
    response.raise_for_status()

    with open(path, "wb") as fd:
        # WARN: This automatically unzips content, making us succeptible to zip bomb attacks.
        for chunk in response.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
            fd.write(chunk)


def main() -> None:
    parser = argparse.ArgumentParser(description="Podcast archiver")
    parser.add_argument("rss_url", type=str, help="URL of the RSS feed")
    parser.add_argument(
        "--limit",
        type=int,
        help="maximum number of episodes to download",
        default=DEFAULT_MAX_EPISODES,
    )
    parser.add_argument(
        "--skip",
        type=int,
        help="number of episodes to skip (starting with most recent)",
        default=-1,
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
    download_podcast(args.rss_url, args.limit, args.skip)


if __name__ == "__main__":
    main()
