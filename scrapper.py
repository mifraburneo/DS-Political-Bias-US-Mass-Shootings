#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import csv
import warnings
from typing import List, Tuple
from urllib import request
import pandas as pd
from pandas import DataFrame as df

from dataclasses import dataclass

import cv2
import numpy as np
from requests import get
from requests.exceptions import HTTPError
from contextlib import closing
from bs4 import BeautifulSoup


# In[ ]:


@dataclass
class Source(object):
    name: str
    site_url: str
    country: str
    bias: str
    factual: str
    press_freedom: str
    media_type: str
    popularity: str
    MBFC_credibility: str
    image_url: str
    page_url: str
    biaser: str


# In[ ]:


def get_website_name(url):
    website_name = url.split('/')[2]
    return website_name
    
def is_good_response(resp):
    """
    Returns True if the response seems to be HTML, False otherwise.
    """
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200
            and content_type is not None
            and content_type.find('html') > -1)

def simple_get(url):
    """
    Attempts to get the content at `url` by making an HTTP GET request.
    If the content-type of response is some kind of HTML/XML, return the
    text content, otherwise raise Exception.
    """
    with closing(get(url, stream=True)) as resp:
        if is_good_response(resp):
            return resp.content
        else:
            resp.raise_for_status()

def get_pages(sources) -> List[str]:
    """
    Gets all known media pages from the category pages specified in the function.
    :return: The media pages to be scraped.
    """
    
    pages: List[str] = []

    for source in sources:
        print('# # # # # # # # # # # # # #')
        print('Gathering pages in this category/site:')
        print(source)
        raw_html = simple_get(source)
        bs = BeautifulSoup(raw_html, 'html.parser')
        links = bs.find_all('td')
        for a in links:
            try:
                #print(a.find('a')['href'])
                pages.append(a.find('a')['href'])
            except:
                pass
        print()

    return pages

def get_allsides_pages(file) -> List[str]:
    """
    Gets all known media pages from the AllSides website.
    :return: The media pages to be scraped.
    """
    pages: List[str] = []
    print('# # # # # # # # # # # # # #')
    print('Gathering pages in this category/site:')
    print('https://allsides.com/')
    print('THIS FILE HAS BEEN MANUALLY DOWNLOADED.')
    bs = BeautifulSoup(open(file, 'r').read(), 'html.parser')
    links = bs.find_all('td', attrs={'class', 'views-field views-field-title source-title'})
    for a in links:
        try:
            #print(a.find('a')['href'])
            pages.append("https://allsides.com"+a.find('a')['href'])
        except:
            pass
    
    return pages


# In[ ]:


def scrape_source(url: str) -> Source:
    biaser = get_website_name(url)
    rich_data = {}

    try:
        raw_html = simple_get(url)
        bs = BeautifulSoup(raw_html, 'html.parser')
    except:
        print(f'The page "{url}" did not contain valid content.')
        pass

    if biaser == 'mediabiasfactcheck.com':
        try:
            source_name = bs.find('h1', attrs={'class', 'entry-title page-title'}).text.replace('\n', '').replace('\t', '')
        except:
            print(f'The page "{url}" does not have a name')
            source_name = "N/A"
            site_url = "N/A"
            pass
        try:
            site_url = bs.find('p', attrs={'class':'post-modified-info'}).find_previous('a').text
        except:
            site_url = "N/A"
            pass

        try:
            headings = bs.find_all('h1')
            for heading in headings:
                image = heading.find_next('img')
            image_url: str = image["src"]
            image_url = image_url[:image_url.find('?')]
        except Exception as e:
            print(f'The source "{source_name}" with url "{url}" does not contain a left-right bias image.')
            image_url = "N/A"
            pass
        
        try:
            rich_data['Bias Rating'] = bs.find('h2').find_next('span').text.split(' ')[0]
        except: 
            pass
        try:
            body = bs.find('h3').find_next('p').text.replace(': ', ':').split('\n')
            for item in body:
                rich_data[item.split(':')[0]] = item.split(':')[1]
        except:
            try:
                body = bs.find('h3').find_next('h5').text.replace(': ', ':').split('\n')
                for item in body:
                    rich_data[item.split(':')[0]] = item.split(':')[1]
            except:
                try:
                    body = bs.find('h2').find_next('p').find_next('p').text.replace(': ', ':').split('\n')
                    for item in body:
                        rich_data[item.split(':')[0]] = item.split(':')[1]
                except:
                    print(f'The source "{source_name}" with url "{url}" does not contain rich data or not in regular place.')
                    print(f'Ommiting source after 3 format tries...')
                    pass

    
    elif biaser == 'allsides.com':
        try:
            raw_html = simple_get(url)
        except HTTPError as e:
            raise print(f'The page "{url}" did not contain valid content.')
        bs = BeautifulSoup(raw_html, 'html.parser')

        try:
            source_name = bs.find('h1').text.replace('\n', '').replace('\t', '')
        except Exception as e:
            print(f'The page "{url}" does not have a name')
            source_name = "N/A"
            pass

        try:
            image = bs.find('div', attrs={'class', 'news-source-full-area'}).find_next('img')
            image_url: str = image["src"]
            image_url = image_url[:image_url.find('?')]
        except Exception as e:
            print(f'The source "{source_name}" with url "{url}" does not contain a left-right bias image.')
            image_url = "N/A"
            pass

        try:
            allsbias = bs.find('div',attrs={'class', 'source-page-bias-area source-page-bias-block'}).find_next('a').text.capitalize()
            replacer = {'Lean left':'Left-Center', 'Lean right':'Right-Center'}
            rich_data['Bias Rating'] = replacer.get(allsbias, allsbias)
            site_url = bs.find('div',attrs={'class', 'span4'}).find_next('a')['href']
            if "http" not in site_url:
                site_url = "N/A"
        except:
            print(f'The source "{source_name}" with url "{url}" does not contain rich data or not in regular place.')
            print(f'Lazy ommiting...')
            site_url = "N/A"
            pass

    else: site_url = "N/A"; source_name = "N/A"; image_url = "N/A"; 

    try:
        # if there's text between parentheses in country, remove it
        rich_data['Country'] = rich_data['Country'].split(' (')[0]
        country = rich_data['Country'].strip().capitalize()
    except:
        country = "N/A"
    try:
        bias = rich_data['Bias Rating'].strip().capitalize()
        if 'Least' in bias: bias = 'Center'
    except:
        bias = "N/A"
    try:
        factual = rich_data['Factual Reporting'].strip().capitalize().replace('\xa0', ' ').replace('-', ' ')
    except:
        factual = "N/A"
    try:
        press_freedom = rich_data['Press Freedom Rating'].strip().capitalize()
    except:
        press_freedom = "N/A"
    try:
        media_type = rich_data['Media Type'].strip().capitalize()
    except:
        media_type = "N/A"
    try:
        popularity = rich_data['Traffic/Popularity'].strip().split('\xa0')[0].split(' ')[0].capitalize()
    except:
        popularity = "N/A"
    try:
        MBFC_credibility = rich_data['MBFC Credibility Rating'].strip().split('\xa0')[0].split(' ')[0].capitalize()
    except:
        MBFC_credibility = "N/A"


    print("--------------------------")
    print("Fully gathered:", source_name)
    print()
    return Source(name=source_name, site_url=site_url, country=country, bias=bias, factual=factual, press_freedom=press_freedom, media_type=media_type, popularity=popularity, MBFC_credibility=MBFC_credibility, image_url=image_url, page_url=url, biaser=biaser)


# In[ ]:


def scrape_sources(urls: List[str]) -> Tuple[List[Source]]:
    sources = []
    for url in urls:
            sources.append(scrape_source(url))
    return sources


# In[ ]:


sources = ['https://mediabiasfactcheck.com/left/', 'https://mediabiasfactcheck.com/leftcenter/', 'https://mediabiasfactcheck.com/center/','https://mediabiasfactcheck.com/right-center/', 'https://mediabiasfactcheck.com/right/']

fullPagesList = get_pages(sources) + get_allsides_pages('allsides.com.html')
data = scrape_sources(fullPagesList)


# In[ ]:


data = pd.DataFrame(data)
data.to_csv('FullData.csv')

