#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import pywikibot
import requests
import json
from datetime import datetime, timedelta

site = pywikibot.Site('wikidata', 'wikidata')

blacklist = ['Q4115189', 'Q13406268', 'Q15397819', 'Q16943273', 'Q17339402', 'Q85409596', 'Q85409446', 'Q85409310', 'Q85409163', 'Q85408938', 'Q85408509'] # sandbox, tour items
blacklist2 = ['Q4167410', 'Q11266439', 'Q4167836'] # disambiguation, template, category items

text = ''
i = 0
img = None
rcend = (datetime.now() - timedelta(days=4)).strftime('%Y%m%d%H%M%S')
allrevisions = {}
revisioncount = {}
rccontinue = '|'

while True:
    payload = {
        'action': 'query',
        'list': 'recentchanges',
        'rcshow': '!bot|!anon',
        'rctype': 'edit',
        'rcprop': 'user|sizes|title|tags',
        'rcnamespace': 0,
        'rcend': rcend,
        'rclimit': 'max',
        'format': 'json',
        'rccontinue': rccontinue
    }
    r = requests.get('https://www.wikidata.org/w/api.php', params=payload)
    data = r.json()
    for revision in data['query']['recentchanges']:
        if revision['newlen'] > revision['oldlen'] and len(revision['tags']) == 0 and 'user' in revision:
            allrevisions.setdefault(revision['title'],[]).append(revision['user'])
    if not 'continue' in data:
        break
    rccontinue = data['continue']['rccontinue']

for item in allrevisions:
    if len(set(allrevisions[item])) >= 3: #require at least 3 distinct users
        revisioncount[item] = len(allrevisions[item])

sorted = [k for k, _ in sorted(revisioncount.items(), key=lambda item: item[1], reverse=True)] # sort by number of edits
for q in sorted:

    # check if item is not in blacklist
    if q in blacklist:
        continue

    # check if item is not currently on [[Wikidata:Main Page/Popular]]
    previousItems = []
    r = requests.get('https://www.wikidata.org/w/api.php?action=query&prop=links&titles=Wikidata:Main%20Page/Popular&format=json')
    data = r.json()
    for m in data['query']['pages']['26001882']['links']:
        previousItems.append(m['title'])
    if q in previousItems:
        continue

    # check if item is not linked to an element of blacklist2
    r = requests.get('https://www.wikidata.org/w/api.php?action=wbgetclaims&entity={}&format=json'.format(q))
    data = r.json()
    if 'error' in data:
        continue
    if 'claims' in data:
        if 'P31' in data['claims']:
            if data['claims']['P31'][0]['mainsnak']['snaktype'] == 'value':
                if data['claims']['P31'][0]['mainsnak']['datavalue']['value']['id'] in blacklist2:
                    continue

    # if everything is fine, add item
    text += '* {{Q|'+q+'}}'

    # add image
    if not img:
        if 'claims' in data:
            if 'P18' in data['claims']:
                if data['claims']['P18'][0]['mainsnak']['snaktype'] == 'value':
                    img = data['claims']['P18'][0]['mainsnak']['datavalue']['value']
                    text = '<span style="float:right; padding-top:0.5em; padding-left:0.5em;">[[File:{}|100px]]</span>\n{} ({{{{I18n|pictured}}}})'.format(img, text)
    i += 1
    if i == 7:
        break
    text += '\n'

if not img:
    text = '<nowiki></nowiki>\n' + text
text += '<span style="clear:right;"></span>'

page = pywikibot.Page(site, 'Wikidata:Main Page/Popular')
page.put(text, summary='upd', minorEdit=False)
