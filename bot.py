import urllib
import pprint
import json
import random
import sys
import tweepy
import tempfile
import os.path
import re

from PIL import Image, ImageFont, ImageDraw

from secret import *
from config import *

emoji_re = re.compile(u'['
                      u'\U0001F300-\U0001F64F'
                      u'\U0001F680-\U0001F6FF'
                      u'\u2600-\u26FF\u2700-\u27BF]+', 
                      re.UNICODE)

def draw_word_wrap(draw, text,
                   xpos=0, ypos=0,
                   max_width=130,
                   fill=(250,0,0),
                   font=None):
    '''Draw the given ``text`` to the x and y position of the image, using
    the minimum length word-wrapping algorithm to restrict the text to
    a pixel width of ``max_width.``
    '''
    text_size_x, text_size_y = draw.textsize(text, font=font)
    remaining = max_width
    space_width, space_height = draw.textsize(' ', font=font)
    # use this list as a stack, push/popping each line
    output_text = []
    # split on whitespace...    
    for word in text.split(None):
        word_width, word_height = draw.textsize(word, font=font)
        if word_width + space_width > remaining:
            output_text.append(word)
            remaining = max_width - word_width
        else:
            if not output_text:
                output_text.append(word)
            else:
                output = output_text.pop()
                output += ' %s' % word
                output_text.append(output)
            remaining = remaining - (word_width + space_width)
    for text in output_text:
        draw.text((xpos, ypos), text, font=font, fill=fill)
        ypos += text_size_y
        
def _auth():
    """Authorize the service with Twitter"""
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.secure = True
    auth.set_access_token(access_token, access_token_secret)
    return tweepy.API(auth)

def post_tweet(tweet, card, author):
    """Post to twitter with the given tweet and card image as attachment"""
    byline = '—' + author['name']
    with tempfile.TemporaryFile() as fp:
        card.save(fp, format='PNG')

        print("Posting message {}".format(tweet))
        api.update_with_media('quote.png', status=tweet + byline, file=fp)

def filter_tweet(tweet):
    """Drop any which have characteristics we don't like: retweets, directed messages, or URLs. Returns 
    None for a tweet we don't want"""

    if '@' in tweet or 'RT' in tweet or 'http' in tweet or '#' in tweet:
        return False
    
    if len(tweet) > (140 - 23 - 23):
        return False
    
    # Check each word for badness; use startswith as a lazy way of matching verb tenses
    words = tweet.split(' ')
    for word in words:
        for bad in FILTER_WORDS:
            if word.startswith(bad):
                return False

    # Filter out emoji as we'll lose them in the output font anyway
    for word in tweet.split(' '):
        if emoji_re.match(word):
            return False

    return True

def search(term, api):
    res = set(tweet.text for tweet in tweepy.Cursor(api.search,
                                                    q=term,
                                                    rpp=NUM_TWEETS_TO_SEARCH,
                                                    result_type="recent",
                                                    include_entities=True,
                                                    lang="en").items(NUM_TWEETS_TO_SEARCH))
    r = set(filter(filter_tweet, res))
    if None in r:
        r.remove(None)
    if r:
        return random.choice(list(r)).replace('\n', ' ').replace('"', '')

def generate_image(tweet, author):
    """Given a tweet and a random author, generate a new twitter card"""
    im = Image.open('images/' + random.choice(author['images']))
    card = Image.new('RGB', (CARD_WIDTH, CARD_HEIGHT), color=(0,0,0))
    card.paste(im, (card.width - im.width, 0))
    draw = ImageDraw.Draw(card)

    # Take the base font size and make it smaller for larger tweets
    if len(tweet) < 20:
        font_size = int(FONT_SIZE * 1.25)
    elif len(tweet) > 200:
        font_size = int(FONT_SIZE * .75)
    else:
        font_size = FONT_SIZE
    
    font = ImageFont.truetype('fonts/' + random.choice(FONTS), size=font_size)
    max_width = CARD_WIDTH / 1.8
    draw_word_wrap(draw, tweet,
                   max_width=max_width,
                   xpos=CARD_MARGIN,
                   ypos=CARD_MARGIN,
                   fill=(255, 255, 255),
                   font=font)

    byline = '—' + author['name']
    draw_word_wrap(draw, byline,
                   max_width=CARD_WIDTH,
                   xpos=CARD_MARGIN,
                   ypos=CARD_HEIGHT - CARD_MARGIN - font.getsize("a")[1],
                   fill=(255,255,153),
                   font=font)
    return card
    
if __name__ == '__main__':
    api = _auth()
    word = random.choice(TERMS)
    tweet = search(word, api)
    if tweet:
        tweet = '“' + tweet + '”'
        author = random.choice(AUTHORS)
        card = generate_image(tweet, author)
        if card:
            post_tweet(tweet, card, author)
