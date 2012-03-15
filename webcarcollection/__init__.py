# -*- coding: utf-8 -*-
from flask import Flask
from flask import render_template
from flaskext.openid import OpenID

app = Flask(__name__)
app.debug=True

app.config.from_pyfile('application.cfg', silent=True)

oid = OpenID(app)

import webcarcollection.views

if __name__ == '__main__':
    app.run(debug=True)