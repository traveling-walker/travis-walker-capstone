import requests
from time import sleep
import random
from common import cache


parameters = {
        'token': 'APYOBXqWIdcxaqcIXocdhBXRNsJmDWuudziElTej',
        'per_page': 100
}

headers = {
    'user-agent': 'whatsNext/0.1'
}

release_dict = {}


def rate_limit(response):
    """
    Designed for compliance with Discogs' API Rate Limiting Rules.
    Takes as parameter an http requests.response object
    Every API response from Discogs lets you know the number of remaining
    API calls that your application can make in the next minute.
    If that count is depleted, calls time.sleep() for 5 seconds.
    """
    if int(response.headers['X-Discogs-Ratelimit-Remaining']) < 1:
        print("Rate Limiting API Calls for 5 Seconds")
        sleep(5)


def get_collection(username, sort):
    # Clear any  existing releases from a previous sync
    release_dict.clear()

    print('Getting collection for ' + username)

    get_url = 'https://api.discogs.com/users/' + username + '/collection/folders/0/releases'

    if sort == 'added':
        parameters['sort'] = 'added'
        parameters['sort_order'] = 'desc'
    elif sort == 'artist':
        parameters['sort'] = 'artist'
        parameters['sort_order'] = 'asc'

    response = requests.get(get_url, params=parameters, headers=headers)

    rate_limit(response)

    if response.status_code != 200:
        return False
    else:
        parse_collection(response)
        return True


def parse_collection(response):
    # Iterate through every release (r) in the API's response
    for r in response.json()['releases']:
        release_id = r['id']
        # Drill to the release's 'basic_information' field
        r = r['basic_information']

        format_list = [i['name'] for i in r['formats']]

        if 'Vinyl' in format_list:
            release_name = r['title']
            artist_name = r['artists'][0]['name']
            artist_id = r['artists'][0]['id']
            resource_url = r['resource_url']
            year = r['year']

            genre_list = [i for i in r['genres']]
            style_list = [i for i in r['styles']]

            release_dict[release_id] = {
                "release_name": release_name,
                "artist_id": artist_id,
                "artist_name": artist_name,
                "year": year,
                "genres": genre_list,
                "styles": style_list,
                "resource_url": resource_url,
            }

    pagination = response.json()['pagination']

    # If there are more pages to be read, print the sync status,
    # then recursively call parse_list, passing in the "next url" already generate by Discogs' API
    if pagination['page'] < pagination['pages']:
        print(str(len(release_dict)) + ' of ' + str(pagination['items']) + ' items synced...')

        rate_limit(response)

        parse_collection(requests.get(pagination['urls']['next'], headers=headers))

    cache.set("release_dict", release_dict)


def get_dict():
    return cache.get("release_dict")


def reset_dict():
    release_dict.clear()
    cache.set("release_dict", None)


def get_random():
    random_id, random_album = random.choice(list(get_dict().items()))
    return random_id
