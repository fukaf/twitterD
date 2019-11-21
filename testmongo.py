import pymongo
import io

# default local port
mongo_url = "127.0.0.1:27017"

client = pymongo.MongoClient(mongo_url)

DATABASE = "test"
db = client[DATABASE]

COLLECTION = "test"

db_coll = db[COLLECTION]

q = {"user": "aaa"}
r = db_coll.find_one(q)
print(r)