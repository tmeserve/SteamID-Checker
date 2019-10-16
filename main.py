import requests
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from urllib.parse import urlparse
from threading import Thread
from queue import Queue
from lxml.html import fromstring
from itertools import cycle
import sys, os
from http.client import HTTPConnection
from urllib import request
import json
import re
import time

def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    session = session or requests.Session()

    adapter = HTTPAdapter(max_retries=5)
    if proxies:
        session.proxies = proxies
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def do_work():
    while True:
        username = queue.get()
        url = ret_url(username)
        handleResult(url, username)
        queue.task_done()

def handleResult(url, username):
    if proxies:
        proxy = next(proxy_pool)
        data = Id(url, proxy=proxy)
    else:
        data = Id(url)

    if data.exist:
        valid_file.write(username + '\n')
    else:
        invalid_file.write(username + '\n')

def get_proxies():
    url = 'https://free-proxy-list.net/'
    response = requests.get(url)
    parser = fromstring(response.text)
    proxies = set()
    for i in parser.xpath('//tbody/tr')[:10]:
        if i.xpath('.//td[7][contains(text(),"yes")]'):
            proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
            proxies.add(proxy)
    return proxies

class Id:
    def __init__(self, url, proxy=None):
        s = requests_retry_session(proxies)
        r = s.get(url)
        self.exist = not 'The specified profile could not be found.' in r.text

def ret_url(sid):
    return 'https://steamcommunity.com/id/{0}'.format(sid)

with open('settings.json', 'r') as settingsf:
    settingsj = json.load(settingsf)
    if 'use_proxies' in settingsj:
        proxy_usage = settingsj['use_proxies']
        if proxy_usage in ['true', '1', 't', 'y', 'yes', 'yeah', 'yup', 'certainly', 'uh-huh']:
            proxy_usage = True
        else:
            proxy_usage = False
    if 'proxy_file' in settingsj:
        proxy_file = settingsj['proxy_file']
    if 'id_file' in settingsj:
        id_file = settingsj['id_file']
    if 'threads' in settingsj:
        threads = int(settingsj['threads'])
    if 'valid_file' in settingsj:
        validf = settingsj['valid_file']
        if os.path.isfile(os.path.join(os.getcwd(), validf)):
            valid_file = open(validf, 'a')
        else:
            valid_file = open(validf, 'a+')
    if 'bad_file' in settingsj:
        invalidf = settingsj['bad_file']
        if os.path.isfile(os.path.join(os.getcwd(), invalidf)):
            invalid_file = open(invalidf, 'a')
        else:
            invalid_file = open(invalidf, 'a+')

queue = Queue(threads*2)
for i in range(threads):
    t = Thread(target=do_work)
    t.daemon = True
    t.start()

if proxy_usage:
    if proxy_file:
        with open(proxy_file) as proxf:
            lines = proxf.readlines()
            proxies = set()
            for line in lines:
                proxies.add(line.strip())
    else:
        proxies = get_proxies()
    
    proxy_pool = cycle(proxies)
else:
    proxies = None

try:
    for name in open(id_file):
        queue.put(name.strip())
    queue.join()
    invalid_file.close()
    valid_file.close()
except KeyboardInterrupt:
    valid_file.close()
    invalid_file.close()
    sys.exit(1)