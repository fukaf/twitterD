import argparse
import os
import io
import json
import sys
from mediascrape import mediascrape
from mediascrape_mongo import mediascrape_mongo

# set base path
path = os.path.dirname(os.path.realpath(__file__))
dump_path = path + '/media'

# parse cli arguments
ap = argparse.ArgumentParser()
ap.add_argument('-f', '--file', help = 'file of names to grab')
ap.add_argument('-o', '--output', help = 'directory to save media to')
ap.add_argument('-l', '--length', help = 'first l account to scrape, -1 to scrape all', default = 50, type = int)
ap.add_argument('-t', '--time', help = 'time lag for update (days)', default = 1, type = int)
ap.add_argument('-m', '--mongo', help = 'disable mongo by 0', default = 1, type = int)
args = vars(ap.parse_args())
filename = args['file']
output = args['output']
length = args['length']
delta_t = args['time'] * 86400
mongo = args['mongo']

with io.open(filename, encoding='utf-8') as f:
    name_list = f.read().splitlines()

count = 1
for name in name_list:
    if count > length and length > 0:
        print("First {} users scraped!".format(length))
        break
    try:
        if mongo == 1:
            mediascrape_mongo(name, output, delta_t=delta_t)
        else:
            mediascrape(name, output, delta_t=delta_t)
    except Exception as e:
        print(e)
    count += 1

print("All {} users scraped!".format(count-1))