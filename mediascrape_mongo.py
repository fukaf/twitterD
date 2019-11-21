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
from datetime import datetime as dt
import pymongo

mongo_url = "127.0.0.1:27017"

client = pymongo.MongoClient(mongo_url)

DATABASE = "twitter"
db = client[DATABASE]

COLLECTION = "twitter"

db_coll = db[COLLECTION]

def mediascrape_mongo(user, output, delta_t=86400, ignore = False):
    # check if enough space left
    if not check_memory():
        return
    # check if user in mongo and initialize it
    q = {"user": user}
    results = db_coll.find_one(q)
    if results is None:
        document = {
            "user": user,
            "imgs": [],
            "vids": [],
            "complete": False,
            }   
        db_coll.insert_one(document)

        results = db_coll.find_one(q)


        # check if exists usr_dir
        path = os.path.dirname(os.path.realpath(__file__))
        default_output = path + '/media'

        dump_dir = '{0}/{1}'.format(output or default_output, user)
        if not os.path.exists(dump_dir):
            os.makedirs(dump_dir)
            ignore = True

    # if not first time, check last modify time of usr_dir
    if not ignore:
        if not check_modified(dump_dir, delta_t) and results["complete"]:
            # do not update
            print("{} is recently updated. Skipping...".format(user))
            return

    print('Fetching user media...')
    print(user)
    try:
        TwitterPageIterator = TwitterMediaSearch.TwitterPager(title = user).get_iterator(user)

        twitter_media = []
        for page in TwitterPageIterator:
            for media in page['media']:
                twitter_media.append(media)
            print('Fetched {} media tweets..'.format(len(twitter_media)))
    except Exception:
        print("=========Fetching error!============")

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
        mongo_imgs = results["imgs"]
        if filename in mongo_imgs:
            print('Skipping image {} - already exists!'.format(idx + 1))
        else:
            print('Fetching image {}/{} - {}'.format(idx + 1, total, url))
            try:
                urllib.request.urlretrieve(url, '{0}/{1}'.format(dump_dir, filename))
                mongo_imgs.append(filename)
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
        mongo_vids = results['vids']
        if filename in mongo_vids:
            print('Skip video {} - already exists!'.format(idx + 1))
        else:
            print('Fetch video {}/{} - {}'.format(idx + 1, total, url))
            try:
                download_vid(url, dump_dir, filename)
                mongo_vids.append(filename)
            except Exception as e:
                print(e)

    # update mongodb
    db_coll.update_one({"user": user},{"$set":{"imgs": mongo_imgs}})
    db_coll.update_one({"user": user},{"$set":{"vids": mongo_vids}})
    db_coll.update_one({"user": user},{"$set":{"complete": True}})
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
    # print(divs)
    size_list = []
    if len(divs) > 1:
        for d in divs:
            s = d.span.string
            sizes = re.findall(r"(\d+)", s)
            if len(sizes) == 0:
                size_list.append(0)
            else:
                size = int(sizes[0])*int(sizes[1])
                # format
                # f = re.findall("")
                size_list.append(size)
        durl = divs[np.argmax(size_list)].a.attrs['onclick'][len('play_video(')+1:-2]
    else:
        durl = divs[0].a.attrs['onclick'][len('play_video(')+1:-2]
        

    with open(dump_dir+"/"+filename, 'wb') as f:
        f.write(requests.get(durl, headers=headers).content)
    
def check_modified(dump_dir, delta_t):
    now = dt.now()
    cmd = "stat -x " + dump_dir
    res = os.popen(cmd).read().splitlines()[-2][len('Modify: '):]
    dir_t = dt.strptime(res, "%a %b %d %H:%M:%S %Y")
    need_update = False
    if (now - dir_t).seconds > delta_t:
        need_update = True
    return need_update

def check_memory():
    m = os.popen('df -h').read().splitlines()[1]
    rest = re.findall(r'(\d+.?\d+)Gi', m)[-1]
    if float(rest) < 1:
        print("Low memory! Stop scraping!")
        print("Last scraped is {}.".format(user))
        return False
    return True
    

if __name__ == '__main__':
    # parse cli arguments
    ap = argparse.ArgumentParser()
    ap.add_argument('-u', '--user', help = 'user to scrape')
    ap.add_argument('-o', '--output', help = 'directory to save media to')
    ap.add_argument('-i', '--ignore', help = 'ignore time difference', default = True, type = bool)
    args = vars(ap.parse_args())
    user = args['user']
    output = args['output']
    ignore = args['ignore']
    mediascrape_mongo(user, output, ignore=ignore)
