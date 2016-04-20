#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import cgi
import datetime
import webapp2
import logging

from google.appengine.ext import ndb
from google.appengine.api import users

from urllib2 import urlopen
import sys
import urlparse
from bs4 import BeautifulSoup



guestbook_key = ndb.Key('Guestbook', 'default_guestbook')

class Greeting(ndb.Model):
  author = ndb.UserProperty()
  content = ndb.TextProperty()
  date = ndb.DateTimeProperty(auto_now_add=True)

  
# we will use this to store a reference to the self object
# that we got when we first loaded the page. This contains a
# a reference to allow us to print back to the main page
localref = None

# This is used as a counter
# to check how many cycles of the recursive function we would like
maxNumberOfRecursion = 0;

# whenever we have visited a page,
# we will store a reference to that page
# to make sure that we never visit the same page twice!
visitedPages = list()

class MainPage(webapp2.RequestHandler):
  def recursiveFunction(self, url):
    global localref, maxNumberOfRecursion, visitedPages
    
    # every time we loop, we will add 1 onto this 
    maxNumberOfRecursion = maxNumberOfRecursion + 1
    
    # print out to the google app engine console what cycle we are on
    logging.info('current cycle: ' + str(maxNumberOfRecursion))

    # once we go above 10 cycles this will prevent the recursive
    # function from going any further    
    if maxNumberOfRecursion > 10:
        return None
      
    # print out to the screen the url we are visiting  
    localref.response.out.write(url)

    r = urlopen(url)    # download the page
    html_doc = str(r.read()) # put the content into a variable
    
    soup = BeautifulSoup(html_doc, 'html.parser')
    
    # counter used to count how many links for each cycle we have visited
    linkCounter = 0

    # find all the links on the page
    for tag in soup.findAll('a', href=True):
        
        tag['href'] = urlparse.urljoin(url, tag['href'])
        # if we have not visited the page before, then starts
        # the recursive search for more pages
        if tag['href'] not in visitedPages:        
            linkCounter = linkCounter + 1    
            localref.response.out.write(tag['href'] + '<br>')
            logging.info(tag['href'])
            
            localref.recursiveFunction(tag['href'])
            visitedPages.append(tag['href'])
            # after we have visited 10 links on the page, stop
            # the current cycle going any further
            if linkCounter == 10:
                break;
  
    
    
  def get(self):
 
    global localref
    
    self.response.out.write('<html>hello there<body>')
    # store a reference to the self object, to allow us to use
    # it to print in the future
    localref = self
    url = 'https://ie.yahoo.com/'
    # start the recursion process by passing
    # a website we want to start from
    self.recursiveFunction(url)

class Guestbook(webapp2.RequestHandler):

  def post(self):
    greeting = Greeting(parent=guestbook_key)

    if users.get_current_user():
      greeting.author = users.get_current_user()

    greeting.content = self.request.get('content')
    greeting.put()
    self.redirect('/')


app = webapp2.WSGIApplication([
  ('/', MainPage),
  ('/sign', Guestbook)
], debug=True)
