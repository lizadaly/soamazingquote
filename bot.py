import urllib
import pprint
import json
import random
import sys
import tweepy
import tempfile
import os.path
import re


from secret import *
from config import *

emoji_re = re.compile(u'['
                      u'\U0001F300-\U0001F64F'
                      u'\U0001F680-\U0001F6FF'
                      u'\u2600-\u26FF\u2700-\u27BF]+', 
                      re.UNICODE)

def _auth():

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.secure = True
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)

    return api

def post_tweet(recipe, message):
    print("Posting message {}".format(message))
    
    tfile = os.path.join(tempfile.mkdtemp(), filename)
    with open(tfile, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024): 
            if chunk: 
                f.write(chunk)
                f.flush()
        api.update_with_media(tfile, status=message)

def filter_tweet(tweet):
    """Drop any which have characteristics we don't like: retweets, directed messages, or URLs. Returns 
    None for a tweet we don't want"""
    
    if '@' in tweet or 'RT' in tweet or 'http' in tweet or '#' in tweet:
        return None
    
    # Check each word for badness; use startswith as a lazy way of matching verb tenses
    words = tweet.split(' ')
    for word in words:
        for bad in FILTER_WORDS:
            if word.startswith(bad):
                return None

    # Filter out emoji as we'll lose them in the output font anyway
    for word in tweet.split(' '):
        if emoji_re.match(word):
            return None

    # Remove newlines from tweets
    tweet = tweet.replace('\n', ' ')
    return tweet

def search(term, api):
    res = set(tweet.text for tweet in tweepy.Cursor(api.search,
                                                    q=term,
                                                    rpp=100,
                                                    result_type="recent",
                                                    include_entities=True,
                                                    lang="en").items(100))
    r = set(map(filter_tweet, res))
    if None in r:
        r.remove(None)

    
if __name__ == '__main__':
    api = _auth()
    search("disrupt", api)
    
