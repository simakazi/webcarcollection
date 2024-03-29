# -*- coding: utf-8 -*-
from webcarcollection import app,oid
from flask import render_template, g, session, request, flash, redirect, url_for, abort
from flaskext.openid import OpenID
#from webcarcollection.database import db_session
from webcarcollection.model import *
from webcarcollection.decorators import *
from google.appengine.api.users import *
from google.appengine.api import memcache
from werkzeug.contrib.atom import AtomFeed

import datetime
from flaskext import wtf
from flaskext.wtf import validators

class Form(wtf.Form):
    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        super(Form, self).__init__(*args, **kwargs)

class CompanyForm(Form):
    title=wtf.TextField(u'Наименование', validators=[validators.Required()])
    description=wtf.TextAreaField(u'Описание',validators=[validators.Optional()])
    country=wtf.TextField(u'Страна',validators=[validators.Optional()])
    site=wtf.TextField(u'Сайт',validators=[validators.Optional()])

class PostForm(Form):
    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        super(PostForm, self).__init__(*args, **kwargs)
    title=wtf.TextField(u'Заголовок', validators=[validators.Required()])
    content=wtf.TextAreaField(u'Содержимое',validators=[validators.Optional()])
    when=wtf.DateField(u'Дата поста',validators=[validators.Optional()])
    #tags=wtf.TextField(u'Теги', validators=[validators.Optional()])
    
class SeriaForm(Form):
    title=wtf.TextField(u'Наименование', validators=[validators.Required()])
    description=wtf.TextAreaField(u'Описание',validators=[validators.Optional()])
    country=wtf.TextField(u'Страна',validators=[validators.Optional()])
    period=wtf.TextField(u'Период выпуска',validators=[validators.Optional()])
    numbers=wtf.IntegerField(u'Количество номеров',validators=[validators.Optional()])
    
class ModelForm(Form):
    title=wtf.TextField(u'Наименование', validators=[validators.Required()])
    description=wtf.TextAreaField(u'Описание',validators=[validators.Optional()])
    scale_onbox=wtf.IntegerField(u'Масштаб заявленный',validators=[validators.Optional()])
    scale_real=wtf.IntegerField(u'Масштаб реальный',validators=[validators.Optional()])
    when=wtf.DateField(u'Дата',validators=[validators.Optional()])
    number=wtf.IntegerField(u'Номер',validators=[validators.Optional()])    
    made_by=wtf.TextField(u'Производитель')
    seria=wtf.TextField(u'Серия')
    
    def validate_made_by(form, field):
        if field.data:
            field.data = Company.get(field.data).key()
        else:
            field.data=None
            
    def validate_seria(form, field):
        if field.data:
            field.data = Seria.get(field.data).key()
        else:
            field.data=None
    

class PostForm(wtf.Form):
    title = wtf.TextField('Title', validators=[validators.Required()])
    content = wtf.TextAreaField('Content', validators=[validators.Required()])

def clearCacheCompany():
    memcache.delete("menu_list_company")
    memcache.delete("dict_company")
    memcache.delete("sitemap")
    
def clearCacheSeria():
    memcache.delete("menu_list_seria")
    memcache.delete("dict_seria")
    memcache.delete("sitemap")
    
def clearCacheMain():
    memcache.delete("main")  
    memcache.delete("sitemap")
    memcache.delete("dict_post")
    memcache.delete("feed")
    
def clearCacheModel():
    memcache.delete("dict_model")
    
def clearCachePhoto():
    memcache.delete("dict_photo")
    
@app.route("/admin/clear_cache")
def clear_cache():
    clearCacheCompany()
    clearCacheMain()
    clearCacheModel()
    clearCacheSeria()
    clearCachePhoto()
    
def dictCompany():
    L=memcache.get("dict_company")
    if L is None:
        L={}
        for company in Company.all():
            L[company.key()]=company 
        memcache.set("dict_company",L)
    return L

def dictModel():
    L=memcache.get("dict_model")
    if L is None:
        L={}
        for model in AutoModel.all():
            L[model.key()]=model
        memcache.set("dict_model",L)
    return L

def dictPhoto():
    L=memcache.get("dict_photo")
    if L is None:
        L={}
        for photo in Photo.all():
            if not L.has_key(photo._auto):
                L[photo._auto]=[]
            L[photo._auto]+=[photo]
        memcache.set("dict_photo",L)
    return L
    
def dictPost():
    L=memcache.get("dict_post")
    if L is None:
        L={}
        for post in Post.all():
            L[post.key()]=post
        memcache.set("dict_post",L)
    return L
    
def getSeriaModel(seria_key):
    L=[]
    for model in dictModel().values():        
        if model._seria==seria_key:
            L.append(model)
    return L
    
def getCompanyModel(company_key):
    L=[]
    for model in dictModel().values():
        if model._made_by==company_key:
            L.append(model)
    return L
    
def dictSeria():
    L=memcache.get("dict_seria")
    if L is None:
        L={}
        for seria in Seria.all():
            L[seria.key()]=seria
        memcache.set("dict_seria",L)
    return L
    
def menu_list_company(companies=None):
    L=memcache.get("menu_list_company")
    if L is not None:
        return L
    L=[u"Производители"]    
    for (key,company) in sorted((companies or dictCompany()).items(),key=lambda x:x[1].title):
        L.append((company.title,url_for('company',key=key,_external=True)))    
    L.append((u"Прочие",url_for('company_models',key="Other",_external=True)))
    memcache.set("menu_list_company",L)
    return L

def menu_list_seria(serias=None):
    L=memcache.get("menu_list_seria")
    if L is not None:
        return L
    L=[u"Серии"]
    for (key,seria) in sorted((serias or dictSeria()).items(),key=lambda x:x[1].title):
        L.append((seria.title,url_for('seria',key=key,_external=True)))    
    L.append((u"Регулярки",url_for('seria_models',key="Other",_external=True)))
    memcache.set("menu_list_seria",L)
    return L
    
def menu_list_admin():
    L=[u"Админка"]    
    L.append((u"Модели",url_for("models")))
    L.append((u"Компании",url_for("companies")))
    L.append((u"Серии",url_for("serias")))    
    L.append((u"Посты",url_for("post")))    
    return L
    
def make_menu(companies=None,serias=None):
    L=[]
    if not users.get_current_user():
        L.append(("Login",create_login_url('')))
    else:
        L.append(("Logout",create_logout_url('')))
    if users.is_current_user_admin():
        L+=menu_list_admin()    
    L+=menu_list_company(companies)
    L+=menu_list_seria(serias)    
    return L
    
@app.route('/admin/photo/delete/')
@app.route('/admin/photo/delete/<key>')
def photo_delete(key):
    if users.is_current_user_admin():        
        photo=Photo.get(key)
        model=photo.auto
        photo.delete()
        clearCachePhoto()
        return redirect(url_for('model',key=model.key()))
    else:
        return render_not_found('')

@app.route('/admin/model/<key>/photo',methods=['GET','POST'])
def model_add_photo(key):
    if request.method == 'POST':
        photo = Photo(file_url=request.form['file'],thumbnail_url=request.form['thumb'],description=request.form['description'],auto=db.Key(key))
        photo.save()        
        return redirect(url_for('model',key=db.Key(key)))        
    else:        
        return render_template('photos.html',menu=make_menu())   

@app.route('/model/<key>',methods=['GET','POST'])
def model(key):
    model=dictModel()[db.Key(key)]#AutoModel.get(key)    
    if not model:
        return render_not_found('')
    edit=users.is_current_user_admin()
    if request.method == 'POST' and edit:
            form = ModelForm()
            if form.validate():
                form.populate_obj(model)                               
                model.save()        
                clearCacheModel()
            else:
                flash(form.errors)                
    #companies=None
    #serias=None
    #if edit:
    serias=dictSeria()
    companies=dictCompany()
    return render_template('model.html',edit=edit,model=model,photos=dictPhoto(),companies=companies,serias=serias,menu=make_menu(companies,serias))

@app.route('/sitemap.xml')
def sitemap():
    resp=memcache.get('sitemap')
    if resp is None:
        resp=render_template('sitemap.xml',companies=dictCompany(),serias=dictSeria(),models=dictModel(),posts=dictPost())
        memcache.set('sitemap',resp)
    return resp
    
@app.route('/seria/<key>/models')
def seria_models(key):    
    if (key=="Other"):
        models=getSeriaModel(None)#AutoModel.all().filter('seria = ',None)
    else:        
        models=getSeriaModel(key)#AutoModel.all.filter('seria = ',db.Key(key))
    return render_template('models.html',models=models,edit=False,menu=make_menu(),serias=dictSeria(),companies=dictCompany(),photos=dictPhoto())
    
@app.route('/company/<key>/models')
def company_models(key):
    if (key=="Other"):
        models=getCompanyModel(None)#AutoModel.all().filter('made_by = ',None)
    else:        
        models=getCompanyModel(key)#AutoModel.all().filter('made_by = ',db.Key(key))
    return render_template('models.html',models=models,edit=False,menu=make_menu(),serias=dictSeria(),companies=dictCompany(),photos=dictPhoto())
    
@app.route('/company/<key>',methods=['GET','POST'])
def company(key):    
    company=dictCompany()[db.Key(key)]
    if not company:
        return render_not_found('')
    if request.method == 'POST' and users.is_current_user_admin():
        form=CompanyForm()
        if form.validate():
            form.populate_obj(company)
            company.save()
            clearCacheCompany()
        else:
            flash(form.errors)                
    return render_template('company.html',company=company,models=getCompanyModel(company.key()),edit=users.is_current_user_admin(),menu=make_menu(),serias=dictSeria(),companies=dictCompany(),photos=dictPhoto())    
    
@app.route('/admin/companies',methods=['GET','POST'])
def companies():
    if request.method == 'POST' and users.is_current_user_admin():
        company=Company(title='none')
        form=CompanyForm()
        if form.validate():
            form.populate_obj(company)
            company.save()
            clearCacheCompany()
        else:
            flash(form.errors)                            
    return render_template('companies.html',menu=make_menu())#,companies=Company.all())

@app.route('/admin/company/<key>/delete',methods=['GET'])
def company_delete(key):
    if users.is_current_user_admin():
        company=Company.get(key)
        company.delete()
        clearCacheCompany()
        return redirect(url_for('companies'))
    else:
        return render_not_found("")
    
@app.route('/admin/seria/<key>/delete',methods=['GET'])
def seria_delete(key):
    if users.is_current_user_admin():
        seria=Seria.get(key)
        seria.delete()
        clearCacheSeria()
        return redirect(url_for('serias'))
    else:
        return render_not_found("")
    
@app.route('/seria/<key>',methods=['GET','POST'])
def seria(key):    
    seria=dictSeria()[db.Key(key)]
    if not seria:
        return render_not_found('')
    if request.method == 'POST' and users.is_current_user_admin():
        form=SeriaForm()
        if form.validate():
            form.populate_obj(seria)
            seria.save()
            clearCacheSeria()
        else:
            flash(form.errors)       
    return render_template('seria.html',seria=seria,models=getSeriaModel(seria.key()),edit=users.is_current_user_admin(),menu=make_menu(),serias=dictSeria(),companies=dictCompany(),photos=dictPhoto())    
    
@app.route('/admin/serias',methods=['GET','POST'])
def serias():
    if request.method == 'POST' and users.is_current_user_admin():        
        seria=Seria(title="none")        
        form=SeriaForm()
        if form.validate():
            form.populate_obj(seria)
            seria.save()
            clearCacheSeria()
        else:
            flash(form.errors)       
        seria.save()
    return render_template('serias.html',menu=make_menu())#,serias=Seria.all())

    
@app.route('/admin/models',methods=['GET','POST'])
def models():
    if request.method == 'POST':
        form=ModelForm()
        if form.validate():
            model=AutoModel(title='title')
            form.populate_obj(model)
            model.save()
            clearCacheModel()
            return redirect(url_for('model',key=model.key()))
        else:
            flash(form.errors)                    
    return render_template('models.html',companies=dictCompany(),serias=dictSeria(),edit=True,menu=make_menu())#,models=models)    
    
@app.route('/admin/photo',methods=['GET','POST'])
@app.route('/admin/photo/<key>',methods=['GET','POST'])
def photo(key=None):
    if request.method == 'POST':
        if key:
            photo=Photo.get(key)
            photo.file_url=request.form['file']
            photo.thumbnail_url=request.form['thumb']
            photo.description=request.form['description']
            photo.save()                      
            return redirect(url_for('model',key=photo.auto.key()))
        else:
            photo = Photo(file_url=request.form['file'],thumbnail_url=request.form['thumb'],description=request.form['description'])
            photos=Photo.all()
            photo.save()          
        clearCachePhoto()
    elif key:
        photo=Photo.get(key)
        photos=[photo]
    else:
        photo=None
        photos=Photo.all()        
    return render_template('photos.html',photos=photos,menu=make_menu(),photo=photo)
    
@app.route('/')
def index():    
    posts=dictPost().values()
    posts.sort(key=lambda x:x.when,reverse=True)
    menu=make_menu()
    return render_template('index.html',menu=menu,posts=posts)

@app.errorhandler(404)
def render_not_found(error):
    return render_template('404.html'),404
    
@app.route('/post', methods = ['GET', 'POST'])
@app.route('/post/<key>', methods = ['GET', 'POST'])
def post(key=None):
    post=None
    if key:
        post=dictPost()[db.Key(key)]
        if not post:
            return render_not_found('')
    elif request.method == 'POST' and users.is_current_user_admin():
        post=Post(title='q')
    if request.method == 'POST' and users.is_current_user_admin():
        post.title=request.form['title']
        post.content=request.form['content']
        if (request.form["when"]!=""):
            post.when=datetime.datetime.strptime(request.form["when"], "%Y-%m-%d %H:%M:%S")
        post.tags=filter(lambda x: x!="",map(unicode.strip,request.form['tags'].split(',')))
        post.save()            
        clearCacheMain()
    return render_template('post.html',post=post,edit=users.is_current_user_admin(),menu=make_menu())    
    
@app.route('/feed.atom')
def feed():
    resp=memcache.get("feed")
    if resp is None:
        feed = AtomFeed(u'Коллекция автомоделей Simakazi',
                        feed_url=request.url, url=request.url_root)
        posts = sorted(dictPost().values(),key=lambda x:x.when,reverse=True)[:15]
        
        for post in posts:
            feed.add(unicode(post.title), unicode(post.content),
                    content_type='html',
                    author='Simakazi',
                    url=url_for('post',key=post.key(),_external=True),
                    updated=post.when,
                    published=post.when)
        resp=feed.get_response()
    memcache.set("feed",resp)
    return resp