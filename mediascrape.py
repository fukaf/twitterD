# Thanks the author of mediascrape
import TwitterMediaSearch
import os
import urllib.request
import argparse
import requests
import re
from pathlib import Path
from bs4 import BeautifulSoup as bs
import numpy as np

def mediascrape(user, output):
    print('Fetching user media...')

    TwitterPageIterator = TwitterMediaSearch.TwitterPager(title = user).get_iterator(user)

    twitter_media = []
    for page in TwitterPageIterator:
        for media in page['media']:
            twitter_media.append(media)
        print('Fetched {} media tweets..'.format(len(twitter_media)))

    path = os.path.dirname(os.path.realpath(__file__))
    default_output = path + '/media'

    dump_dir = '{0}/{1}'.format(output or default_output, user)
    if not os.path.exists(dump_dir):
        os.makedirs(dump_dir)

    # extract all nested media
    img_urls = []
    vid_urls = []
    for m in twitter_media:
        media = m.get('entities', {}).get('media', [])
        videos = [x for x in media if x.get('type') == 'video']
        for idx, vid in enumerate(videos):
            vid_urls.append({
                'url': vid.get('media_url'),
                'filename': '{}_{}_{}.mp4'.format(user, m.get('id_str'), idx),
            })
        imgs = [x for x in media if x.get('type') == 'photo']
        for idx, img in enumerate(imgs):
            img_urls.append({
                'url': img.get('media_url'),
                'filename': '{}_{}_{}.jpg'.format(user, m.get('id_str'), idx),
            })

    # fetch + save images
    total = len(img_urls)
    print('')
    print('Found {} images!'.format(total))
    print('')
    for idx, img in enumerate(img_urls):
        url = img.get('url')
        filename = img.get('filename')
        # only save the photo if it does not already exist
        photo_already_exists = Path(dump_dir + "/" + filename).is_file()
        if photo_already_exists:
            print('Skipping image {} - already exists!'.format(idx + 1))
        else:
            print('Fetching image {}/{} - {}'.format(idx + 1, total, url))
            try:
                urllib.request.urlretrieve(url, '{0}/{1}'.format(dump_dir, filename))
            except Exception as e:
                print(e)

    print('')
    # fetch + save videos
    total = len(vid_urls)
    print('')
    print('Found {} videos!'.format(total))
    print('')
    for idx, vid in enumerate(vid_urls):
        url = vid.get('url')
        filename = vid.get('filename')
        exists = Path(dump_dir + "/" + filename).is_file()
        if exists:
            print('Skip video {} - already exists!'.format(idx + 1))
        else:
            print('Fetch video {}/{} - {}'.format(idx + 1, total, url))
            try:
                download_vid(url, dump_dir, filename)
            except Exception as e:
                print(e)

    print('')
    print('Done scraping media!')

def download_vid(url, dump_dir, filename):
    root_url = "https://downloadtwittervideo.net/download"
    headers = {"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36",
    }
    data = {'twitter_url': url}

    r = requests.post(root_url, data=data, headers=headers)
    soup = bs(r.text, 'html.parser')
    divs = soup.find_all("div", class_="btn-row")[1:]
    size_list = []
    for d in divs:
        s = d.span.string
        sizes = re.findall(r"(\d+)", s)
        size = int(sizes[0])*int(sizes[1])
        # format
        # f = re.findall("")
        size_list.append(size)
    durl = divs[np.argmax(size_list)].a.attrs['onclick'][len('play_video(')+1:-2]

    with open(dump_dir+"/"+filename, 'wb') as f:
        f.write(requests.get(durl, headers=headers).content)
    


if __name__ == '__main__':
    # parse cli arguments
    ap = argparse.ArgumentParser()
    ap.add_argument('-u', '--user', help = 'user to scrape')
    ap.add_argument('-o', '--output', help = 'directory to save media to')
    args = vars(ap.parse_args())
    user = args['user']
    output = args['output']
    mediascrape(user, output)
