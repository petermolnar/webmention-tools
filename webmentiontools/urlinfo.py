#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import calendar
import iso8601

class UrlInfo():

    def __init__(self, url, text = '' ):
        self.url = url
        self.error = False
        if text:
            self.soup =  BeautifulSoup( text, "html5lib" )
        else:
            self.fetchHTML()


    def fetchHTML(self):
        self.soup = None
        self.data = dict()
        self.data['links_to'] = []
        r = requests.get(self.url)
        if r.status_code != 200:
            self.error = True
            return
        # use apparent_encoding, seems to work better in the cases I tested.
        r.encoding = r.apparent_encoding
        self.soup = BeautifulSoup(r.text, "html5lib" )


    def __somethingOf( self, key = 'in-reply-to'):
        """ Generic function to collect relations to other URLs """
        if key in self.data:
            return self.data[ key ]
        # Identify first class="u-{{ key }}" or rel="{{ key }}" link
        rel = self.soup.find('a', attrs={'class':'u-%s' % key })
        if not rel:
            rel = self.soup.find('a', attrs={'rel':'%s' % key })
            if not rel:
                return None
        self.data[ key ] = rel['href']
        return rel['href']


    def inReplyTo(self):
        return self.__somethingOf( 'in-reply-to' )


    def repostOf(self):
        return self.__somethingOf( 'repost-of' )


    def likeOf(self):
        return self.__somethingOf( 'like-of' )


    def bookmarkOf(self):
        return self.__somethingOf( 'bookmark-of' )


    def relationType(self):
        if 'relation' in self.data:
            return self.data['relation']

        if self.inReplyTo() != None:
            self.data['relation'] = 'in-reply-to'
        elif self.repostOf() != None:
            self.data['relation'] = 'repost-of'
        elif self.likeOf() != None:
            self.data['relation'] = 'like-of'
        elif self.bookmarkOf() != None:
            self.data['relation'] = 'bookmark-of'
        else:
            self.data['relation'] = 'webmention'

        return self.data['relation']


    def pubDate(self, form = 'text'):
        k = 'pubDate_%s' % form
        # Get the time of the reply, if possible
        if k in self.data:
            return self.data[ k ]

        ir2_time = self.soup.find(True, attrs={'class':'dt-published'})

        if ir2_time  and ir2_time.has_attr('datetime') :
            # pubdate _should_ be in iso8601... in theory
            if form == 'datetime':
                self.data[k] = iso8601.parse_date( ir2_time['datetime'] )
            elif form == 'time':
                d = iso8601.parse_date( ir2_time['datetime'] )
                self.data[k] = calendar.timegm( d.timetuple() )
            else:
                self.data[k] = ir2_time['datetime']

            return self.data[k]


    def title(self):
        if 'title' in self.data:
            return self.data['title']
        # try getting the title from a h-entry
        hentry = self.soup.find(True,attrs={'class':'h-entry'} )
        if hentry:
            title = hentry.find(True,attrs={'class':'p-name'})
            if title:
                self.data['title'] = title
                return self.data['title']
        # fall back to page title, if h-entry failed
        title = self.soup.find('title').string.strip()
        self.data['title'] = title
        return title


    def content(self):
        if 'content' in self.data:
            return self.data['content']
        # try to get content from e-content
        content = self.soup.find(True, attrs={'class':'e-content'})
        # or from e-summary
        if not content:
            content = self.soup.find(True, attrs={'class':'e-summary'})
        # or from the first article
        if not content:
            content = self.soup.find('article')

        if content:
            self.data['content'] = content
            return self.data['content']


    def author(self):
        if 'author' in self.data:
            return self.data['author']

        #Try using p-author
        author = self.soup.find(True, attrs={'class':'p-author'})
        #Try using h-card
        if not author:
            author = self.soup.find(True, attrs={'class':'h-card'})

        if author:
            self.data['author'] = {}

            image = author.find('img')
            if image:
                image_src = image['src']
                self.data['author']['img'] = urljoin(self.url, image_src)

            name = author.find(True, attrs={'class':'p-name'})
            if name:
                self.data['author']['name'] = name.string.strip()

            url = author.find(True, attrs={'class':'u-url'})
            if url:
                self.data['author']['url'] = url['href']

            email = author.find(True, attrs={'class':'u-email'})
            if email:
                self.data['author']['email'] = email.string.strip()

            return self.data['author']


    def image(self):
        if 'image' in self.data:
            return self.data['image']

        #Try using p-author
        author = self.soup.find(True, attrs={'class':'p-author'})
        if author:
            image = author.find('img')
            if image:
                image_src = image['src']
                self.data['image'] = urljoin(self.url, image_src)
                return self.data['image']

        # Try using h-card
        hcard = self.soup.find(True, attrs={'class':'h-card'})
        if hcard:
            image = hcard.find('img', attrs={'class':'u-photo'})
            if image:
                self.data['image'] = urljoin(self.url, image['src'])
                return self.data['image']

        # Last resort: try using rel="apple-touch-icon-precomposed"
        apple_icon = self.soup.find('link', attrs={'rel':'apple-touch-icon-precomposed'})
        if apple_icon:
            image = apple_icon['href']
            if image:
                self.data['image'] = urljoin(self.url, image)
                return self.data['image']


    def snippetWithLink(self, url):
        """ This method will try to return the first
        <p> or <div> that contains an <a> tag linking to
        the given URL.
        """
        link = self.soup.find("a", attrs={'href': url})
        if link:
            for p in link.parents:
                if p.name in ('p','div'):
                    return ' '.join(p.text.split()[0:30])
        return None


    def linksTo(self, url):
        # Check if page links to a specific URL.
        # please note that the test is done on the *exact* URL. If
        # you want to ignore ?parameters, please remove them in advance
        if url in self.data['links_to']:
            return True
        r = self.soup.find("a", attrs={'href': url})
        if r:
            self.data['links_to'].append(url)
            return True
        else:
            return False

if __name__ == '__main__':
   pass
