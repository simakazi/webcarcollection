# -*- coding: utf-8 -*-
from webcarcollection import app,oid
from flask import render_template, g, session, request, flash, redirect, url_for, abort
from flaskext.openid import OpenID
#from webcarcollection.database import db_session
from webcarcollection.model import *
from webcarcollection.decorators import *
from google.appengine.api.users import *
from google.appengine.api import memcache

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
    
def clearCacheSeria():
    memcache.delete("menu_list_seria")
    memcache.delete("dict_seria")
    
def dictCompany():
    L=memcache.get("dict_company")
    if L is  not None:
        return L
    L=[]
    for company in Company.all():
        L.append((company.title,company.key()))
    memcache.set("dict_company",L)
    return L

def dictSeria():
    L=memcache.get("dict_seria")
    if L is  not None:
        return L
    L=[]
    for seria in Seria.all():
        L.append((seria.title,seria.key()))
    memcache.set("dict_seria",L)
    return L
    
def menu_list_company(companies=None):
    L=memcache.get("menu_list_company")
    if L is not None:
        return L
    L=[u"Производители"]
    for company in (companies or dictCompany()):
        L.append((company[0],url_for('company',key=company[1])))    
    L.append((u"Прочие",url_for('company_models',key="Other")))
    memcache.set("menu_list_company",L)
    return L

def menu_list_seria(serias=None):
    L=memcache.get("menu_list_seria")
    if L is not None:
        return L
    L=[u"Серии"]
    for seria in (serias or dictSeria()):
        L.append((seria[0],url_for('seria',key=seria[1])))    
    L.append((u"Регулярки",url_for('seria_models',key="Other")))
    memcache.set("menu_list_seria",L)
    return L
    
def menu_list_admin():
    L=[u"Админка"]    
    L.append((u"Модели",url_for("models")))
    L.append((u"Компании",url_for("companies")))
    L.append((u"Серии",url_for("serias")))    
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
    model=AutoModel.get(key)    
    if not model:
        return render_not_found('')
    edit=users.is_current_user_admin()
    if request.method == 'POST' and edit:
            form = ModelForm()
            if form.validate():
                form.populate_obj(model)                               
                model.save()                
            else:
                flash(form.errors)                
    companies=None
    serias=None
    if edit:
        serias=dictSeria()
        companies=dictCompany()
    return render_template('model.html',edit=edit,model=model,companies=companies,serias=serias,menu=make_menu(companies,serias))

@app.route('/seria/<key>/models')
def seria_models(key):    
    if (key=="Other"):
        models=AutoModel.all().filter('seria = ',None)
    else:        
        models=AutoModel.all.filter('seria = ',db.Key(key))
    return render_template('models.html',models=models,edit=False,menu=make_menu())
    
@app.route('/company/<key>/models')
def company_models(key):
    if (key=="Other"):
        models=AutoModel.all().filter('made_by = ',None)
    else:        
        models=AutoModel.all().filter('made_by = ',db.Key(key))
    return render_template('models.html',models=models,edit=False,menu=make_menu())
    
@app.route('/company/<key>',methods=['GET','POST'])
def company(key):    
    company=Company.get(key)
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
    return render_template('company.html',company=company,edit=users.is_current_user_admin(),menu=make_menu())    
    
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
    seria=Seria.get(key)
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
    return render_template('seria.html',seria=seria,edit=users.is_current_user_admin(),menu=make_menu())    
    
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
            return redirect(url_for('model',key=model.key()))
        else:
            flash(form.errors)                
    #models=AutoModel.all()
    companies=dictCompany()
    serias=dictSeria()
    return render_template('models.html',companies=companies,serias=serias,edit=True,menu=make_menu())#,models=models)    
    
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
    elif key:
        photo=Photo.get(key)
        photos=[photo]
    else:
        photo=None
        photos=Photo.all()        
    return render_template('photos.html',photos=photos,menu=make_menu(),photo=photo)
    
@app.route('/')
def index():    
    posts=Post.all()    
    menu=make_menu()
    return render_template('index.html',menu=menu,posts=posts)

@app.errorhandler(404)
def render_not_found(error):
    return render_template('404.html'),404
    
@app.route('/posts/new', methods = ['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title = form.title.data,
                    content = form.content.data,
                    author = users.get_current_user())
        post.put()
        flash('Post saved on database.')
        return redirect(url_for('index'))
    return render_template('new_post.html', form=form,menu=make_menu())
"""
@app.before_request
def before_request():
    g.user = None
    if 'openid' in session:
        g.user = User.query.filter_by(openid=session['openid']).first()


@app.after_request
def after_request(response):
    db_session.remove()
    return response
    
@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
    if g.user is not None:
        return redirect(oid.get_next_url())
    if request.method == 'POST':
        openid = request.form.get('openid')
        if openid:
            return oid.try_login(openid, ask_for=['email', 'fullname',
                                                  'nickname'])
    return render_template('login.html', next=oid.get_next_url(),
                           error=oid.fetch_error())


@oid.after_login
def create_or_login(resp):
    session['openid'] = resp.identity_url
    user = User.query.filter_by(openid=resp.identity_url).first()
    if user is not None:
        flash(u'Successfully signed in')
        g.user = user
        return redirect(oid.get_next_url())
    return redirect(url_for('create_profile', next=oid.get_next_url(),
                            name=resp.fullname or resp.nickname,
                            email=resp.email))


@app.route('/create-profile', methods=['GET', 'POST'])
def create_profile():
    if g.user is not None or 'openid' not in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        if not name:
            flash(u'Error: you have to provide a name')
        elif '@' not in email:
            flash(u'Error: you have to enter a valid email address')
        else:
            flash(u'Profile successfully created')
            db_session.add(User(name, email, session['openid']))
            db_session.commit()
            return redirect(oid.get_next_url())
    return render_template('create_profile.html', next_url=oid.get_next_url())


@app.route('/profile', methods=['GET', 'POST'])
def edit_profile():    
    if g.user is None:
        abort(401)
    form = dict(name=g.user.name, email=g.user.email)
    if request.method == 'POST':
        if 'delete' in request.form:
            db_session.delete(g.user)
            db_session.commit()
            session['openid'] = None
            flash(u'Profile deleted')
            return redirect(url_for('index'))
        form['name'] = request.form['name']
        form['email'] = request.form['email']
        if not form['name']:
            flash(u'Error: you have to provide a name')
        elif '@' not in form['email']:
            flash(u'Error: you have to enter a valid email address')
        else:
            flash(u'Profile successfully created')
            g.user.name = form['name']
            g.user.email = form['email']
            db_session.commit()
            return redirect(url_for('edit_profile'))
    return render_template('edit_profile.html', form=form)

@app.route('/logout')
def logout():
    session.pop('openid', None)
    flash(u'You have been signed out')
    return redirect(oid.get_next_url())
"""