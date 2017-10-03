"""
Grab seeds from facebook
"""
import json
import os
import click
import facebook
import requests
from classifier.utilities import confs

def fetch_page(pagename, total_posts, graph):
    """
    Grab a selection of posts by page
    """
    try:
        posts = graph.request('/'+pagename+'/posts')
    except facebook.GraphAPIError as err:
        print("%s" % err)
        return []
    page_count = 0
    post_bodies = []
    while posts:
        for post in posts['data']:
            if 'message' in post:
                post_bodies.append(post['message'])
                if len(post_bodies) >= total_posts:
                    break
        if 'paging' in posts and len(post_bodies) < total_posts:
            if 'next' in posts['paging']:
                posts = requests.get(posts['paging']['next']).json()
                page_count += 1
            else:
                break
        else:
            break
    print(pagename + '  ' + str(len(post_bodies)))
    return post_bodies

def fetch(pages, per_page, graph):
    """
    Get a list of posts from facebook
    """
    return [x.replace('\n', '')
            for name in pages
            for x in fetch_page(name, per_page, graph)]

@click.command("seed")
@click.pass_context
@click.argument("language")
def seed(ctx, language):
    """
    Create a list of seed posts for our classifier by language
    """
    for directory, conf in confs(ctx.obj["base"]):
        if conf["language"] == language:
            options = conf
            conf_dir = directory
            break

    if options is None:
        print("Couldn't find a config for {}".format(language))
        exit()

    with open(os.path.join(conf_dir, 'seeds_config.json'), 'rb') as seeds_file:
        seeds_config = json.load(seeds_file)

    graph_token_url = 'https://graph.facebook.com/oauth/access_token?' \
                      'client_id={}&client_secret={}' \
                      '&grant_type=client_credentials'
    res = requests.get(graph_token_url.format(
        os.environ['FACEBOOK_APP_ID'],
        os.environ['FACEBOOK_APP_SECRET']))

    access_token = json.loads(res.text)['access_token']
    graph = facebook.GraphAPI(access_token, version=2.7)

    messages = {
        'political': fetch(seeds_config["political"], 400, graph),
        'not_political': fetch(seeds_config["not_political"], 400, graph)
    }

    with open(os.path.join(conf_dir, 'seeds.json'), 'w') as out:
        json.dump(messages, out)
