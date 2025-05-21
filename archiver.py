import argparse
import mimetypes

from defusedxml.minidom import parse, parseString
import requests



DEFAULT_EXTENSION = ".mp3"

def download_podcasts(xml_url, limit):
    r = requests.get(xml_url)
    dom = parseString(r.text)
    count = 0

    episodes = dom.getElementsByTagName("item")

    for episode in episodes:
        enclosure = episode.getElementsByTagName("enclosure")[0]
        audio_url = enclosure.getAttribute("url")
        audio_type = enclosure.getAttribute("type")

        title = episode.getElementsByTagName("title")[0].childNodes[0].data

        get_podcast_file(audio_url, audio_type, title)

        if limit:
            if count == limit:
                break
            else:
                count += 1

def get_podcast_file(audio_url, audio_type, title):
    extension = mimetypes.guess_extension(audio_type) or DEFAULT_EXTENSION
    file_request = requests.get(audio_url)

    with open(title + extension, 'wb') as fd:
        # NOTE: Hmm, this automatically unzips content, I think. Worth reconsidering.
        for chunk in file_request.iter_content(chunk_size=128):
            fd.write(chunk)


def main():
    parser = argparse.ArgumentParser(description='Podcast archiver')
    parser.add_argument('rss_url', type=str, help='URL of the RSS feed')
    parser.add_argument('--limit', type=str, help='maximum number of episodes to download', default=2)
    args = parser.parse_args()

    download_podcasts(args.rss_url, args.limit)

if __name__ == '__main__':
    main()