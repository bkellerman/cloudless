import requests
import json
from collections import Counter
import pandas as pd
import numpy as np

## SETUP ##

def setup_session():
    print "Setting up session with https://www.planet.com...",
    session = requests.Session()
    session.auth = ('user06@swxhack.com', 'User06SofwerxHack')
    print "done."
    return session

def build_search_params():
    
    print "Building query params...",
    geo_json_geometry_ship_path = {
        "type": "Polygon",
        "coordinates": [
            [
                [
                    122.2119140625,
                    36.87962060502676
                ],
                [
                    126.2548828125,
                    33.091541548655215
                ],
                [
                    126.32080078124999,
                    33.696922692957685
                ],
                [
                    122.55249023437501,
                    37.1165261849112
                ],
                [
                    122.2119140625,
                    36.87962060502676
                ]
            ]
        ]
    }
    
    # filter for items that overlap with our chosen geometry
    geometry_filter = {
        "type": "GeometryFilter",
        "field_name": "geometry",
        "config": geo_json_geometry_ship_path
    }
    
    # filter images acquired in a certain date range
    date_range_filter = {
        "type": "DateRangeFilter",
        "field_name": "acquired",
        "config": {
            "gte": "2017-04-27T00:00:00.000Z",
            "lte": "2017-04-30T00:00:00.000Z"
        }
    }
    
    cloud_cover_filter = {
        "type": "RangeFilter",
        "field_name": "cloud_cover",
        "config": {
            "lte": 1
        }
    }
    
    # add all the filters together
    filters = {
        "type": "AndFilter",
        "config": [geometry_filter, date_range_filter]
    }
    
    print "done."
    return filters

def build_endpoint_request(search_params):
    print "Building the REST endpoint request...",
    req = {
        "item_types": ["PSScene4Band", "PSScene3Band"],
        "filter": search_params
    }
    print "done."
    return req

def quick_search(request, session):
    print "Executing query...",
    resp = session.post('https://api.planet.com/data/v1/quick-search', json=request)
    print "done."
    return resp

def get_activation_links(resp, asset_type, session):
    print "Getting activation links for the items...",
    activation_links = []
    for res in resp:
        try:
            tmp = session.get(
                ("https://api.planet.com/data/v1/item-types/" +
                "{}/items/{}/assets/").format(res['properties']['item_type'], res['id'])).json()
            for a_type in tmp:
                activation_links.append(tmp[asset_type]["_links"]["activate"])
        except KeyError:
            continue
    print "done."
    return list(set(activation_links))
    
def activate_assets(activation_links, s):
    print "Activating the items for download...",
    for link in activation_links:
        s.post(link)
    print "done."

def get_download_links(results, asset_type, s):
    print "Getting download links to imgs...",
    download_links = []
    for res in results:
        try:
            tmp = s.get(
                ("https://api.planet.com/data/v1/item-types/" +
                "{}/items/{}/assets/").format(res['properties']['item_type'], res['id'])).json()
            for a_type in tmp:
                link = tmp[asset_type]["location"]
                download_links.append(link)
        except KeyError, e:
            continue
    print "done."
    return list(set(download_links))

def get_images(download_links, asset_type, s):
    print "Downloading images...",
    i = 0
    for link in download_links:
        i += 1
        response = s.get(link, stream=True)
        with open(asset_type + str(i) + '.tif', 'wb') as handle:
             for block in response.iter_content(1024):
                 handle.write(block)
    print "done."

asset_types = ["visual", "analytic", "analytic_dn"]




sess = setup_session()
params = build_search_params()
req = build_endpoint_request(params)
results = json.loads(quick_search(req, sess).content)['features']

item_ids = []
item_types = []
activation_links = []
for res in results:
    item_ids.append(res['id'])
    item_types.append(res['properties']['item_type'])
    item = sess.get(("https://api.planet.com/data/v1/item-types/" +
        "{}/items/{}/assets/").format(res['properties']['item_type'], res['id']))
    try:
        url = item.json()[asset_types[0]]['_links']['activate']
        sess.post(url)
    except KeyError:
        continue

download_links = get_download_links(results, asset_types[0], sess)
get_images(download_links, asset_types[0], sess)

