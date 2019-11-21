import pymongo
from pathlib import Path
import argparse
import os

mongo_url = "127.0.0.1:27017"

client = pymongo.MongoClient(mongo_url)

DATABASE = "twitter"
db = client[DATABASE]

COLLECTION = "twitter"

db_coll = db[COLLECTION]

def updatemongo(path):
    current_users = os.listdir(path)

    for u in current_users:
        sdir = os.path.join(path, u)
        if os.path.isdir(sdir):
            r = db_coll.find_one({"user":u})
            if r is not None:
                continue
            filesname = os.listdir(sdir)
            imgs = []
            vids = []
            for f in filesname:
                if f[-3:] == "mp4":
                    vids.append(f)
                else:
                    imgs.append(f)

            document = {
                "user": u,
                "imgs": imgs,
                "vids": vids,
                "complete": True,
            }
            db_coll.insert_one(document)
            print("Done update for {}".format(u))

    print("Done all update.")   

    

    
    


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument('-d', '--dir', help = 'dir to update mongo')
    args = vars(ap.parse_args())
    dump_dir = args['dir']
    updatemongo(dump_dir)