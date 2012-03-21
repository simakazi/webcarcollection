# -*- coding: utf-8 -*-
from google.appengine.ext import db
from google.appengine.ext import blobstore

class Post(db.Model):
    title = db.TextProperty(required = True)
    content = db.TextProperty()
    when = db.DateTimeProperty(auto_now_add = True)    
    tags = db.StringListProperty()

class Company(db.Model):
    title = db.StringProperty(required = True)
    description = db.TextProperty()
    country = db.StringProperty()
    site = db.StringProperty()
    
class Seria(db.Model):
    title = db.StringProperty(required = True)
    description = db.TextProperty()
    country = db.StringProperty()
    period = db.StringProperty()
    numbers = db.IntegerProperty()

class AutoModel(db.Model):
    title = db.StringProperty(required = True)
    description = db.TextProperty()
    scale_onbox = db.IntegerProperty()
    scale_real = db.IntegerProperty()
    when = db.DateProperty()
    made_by = db.ReferenceProperty(Company,collection_name='models')
    seria = db.ReferenceProperty(Seria,collection_name='models')
    number = db.IntegerProperty()
   
class Photo(db.Model):
    auto = db.ReferenceProperty(AutoModel, collection_name='photos')    
    file_url = db.StringProperty(required = True)
    thumbnail_url = db.StringProperty(required = True)
    description = db.TextProperty()
    