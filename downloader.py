import os
import re
import shutil

from bs4 import BeautifulSoup as bs
import requests

VICE_BASE_URL = 'https://www.vice.com'
GALLERY_BASE_URL = VICE_BASE_URL + '/en_us/topic/habits?page='
GALLERY_NUM_PAGES = 3
DOWNLOADS_FOLDER = './downloads/'

def get_gallery_soups():
    gallery_soups = []
    # I could have this script dynamically get the number of pages for the 
    # vice tag 'habits' and then keep going til it's scraped all pages.
    for i in range(1,4):
        r = requests.get(GALLERY_BASE_URL + str(i))
        gallery_soups.append(bs(r.text, 'html.parser'))
    return gallery_soups

def is_link_to_article(tag):
    return tag.has_attr('class') and 'grid__wrapper__card' in tag['class'] 

def scrape_links_to_articles(gallery_page_soup):
    processed_links = []
    raw_links = gallery_page_soup.find_all(is_link_to_article)
    for link in raw_links:
        is_habits_comic = False
        for child in link.descendants:
            # this if check is a little clever... so every box that links to a
            # habits comic has a span containing the text "Habits". In
            # beautiful soup, that text itself is then a child of that span. So
            # if one of the descendents is this exact text, we've found what
            # we're looking for.
            if child == 'Habits':
                is_habits_comic = True
        if is_habits_comic:
            processed_links.append(link['href'])

    return processed_links

def is_habits_comic_image(tag):
    return tag.has_attr('class') and 'article__image' in tag['class']

def find_comic_images(comic_url):
    image_urls = []
    r = requests.get(VICE_BASE_URL + comic_url)
    soup = bs(r.text, 'html.parser')
    pictures = soup.find_all(is_habits_comic_image)
    for picture in pictures:
        for child in picture.children:
            if child.name == 'img':
                direct_image_link = child['src']
                m = re.search(r'.*\.jpg', direct_image_link)
                direct_image_link = m.group()
                image_urls.append(direct_image_link)
    return image_urls

# def download_image(image_url, file_name):
def download_image(image_url):
    try:
        os.makedirs(DOWNLOADS_FOLDER)
    except FileExistsError:
        # nothing to do, just making sure to create it if it doesn't exist
        pass

    m = re.search(r'/(20.*\.jpg)', image_url)
    file_name = m.group(1)
    file_name = file_name.replace('/', '-')

    # file_name=image_url.split('/')[-1]):
    r = requests.get(image_url, stream=True)
    if r.status_code == 200:
        with open(DOWNLOADS_FOLDER + file_name, 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)

def main():
    soups = get_gallery_soups()

    article_links = []
    for soup in soups:
        current_article_links = scrape_links_to_articles(soup)
        for link in current_article_links:
            article_links.append(link)
    # articles are in reverse chronological order, so we reverse them
    # article_links.reverse()

    image_links = []
    for article_link in article_links:
        current_image_links = find_comic_images(article_link)
        for link in current_image_links:
            image_links.append(link)

    # i = 0
    for image_link in image_links:
        download_image(image_link)
        # download_image(image_link, str(i).zfill(3))
        # i += 1

if __name__ == '__main__':
    main()
