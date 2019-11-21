import pymongo
import io

# default local port
mongo_url = "127.0.0.1:27017"

client = pymongo.MongoClient(mongo_url)

DATABASE = "twitter"
db = client[DATABASE]

COLLECTION = "twitter"

db_coll = db[COLLECTION]

filename = "follow.txt"
with io.open(filename, encoding='utf-8') as f:
    name_list = f.read().splitlines()
