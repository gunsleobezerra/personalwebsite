from genericpath import exists
from flask import Flask,render_template,flash,request,abort,Response,session,redirect,url_for,jsonify
from flask_login import LoginManager, current_user, login_required, logout_user
import flask_login
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import urlparse,urljoin
from datetime import datetime
from markupsafe import escape
import sqlite3
import json
import os
from sqlalchemy import false, true
import forms as LT

config_json = json.load(open('config.json'))
app = Flask(__name__)
app.secret_key = config_json['secret_key']
login_manager = LoginManager()
login_manager.init_app(app)



app.config['SQLALCHEMY_DATABASE_URI'] = config_json['database_uri']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
login_manager.login_view = "login"

db = SQLAlchemy(app)


number=0

#This function is used to check if the url is safe
def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc

#generate response function
def get_redirect_target():
    for target in request.values.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return target

#redirect back to the page
def redirect_back(endpoint, **values):
    target = request.args['next']
    if not target or not is_safe_url(target):
        print(f"Redirecting......{target}")
        target = url_for(endpoint, **values)
    print(f"Redirecting......{target}")
    return redirect(target)

    
#Parameters is Instance of User  class
def login_user_check(user,password):
    if(user.check_password(password)):
        return true
    return false
        
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@app.route('/manage', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    
   
    form = LT.LoginForm()
    
    if form.validate_on_submit():
        print("Validating...")
        current =User.query.filter_by(username=form.username.data).first()
        
        if login_user_check(current,password=form.password.data):
            flask_login.login_user(current)
            print("Logging in...",current.username)
            current.is_authenticated = True
            session['current_user_id'] = current.id
            current_user=current
            
            flash('Logged in successfully.')
            
            next = get_redirect_target()
            print(next)
            if not is_safe_url(next):
                return abort(400)
            return redirect(url_for('index'))
        else:
            
            return redirect(url_for('login'))
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

#classe User que representa o usuário
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    is_authenticated = False
    is_active = False
    is_anonymous = False
    
    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password
        self.is_active = True
        self.is_anonymous = False
    
    def __repr__(self):
        return '<User %r>' % self.username
    
    
    #Precisa ter esses métodos para funcionar a autenticação (Sobrescreve os métodos do flask_login)
    def is_authenticated(self):
        return self.is_authenticated
    def is_active(self):
        return self.is_active
    def is_anonymous(self):
        return self.is_anonymous
    
        
    def get(id):
        thisuser = User.query.filter_by(id=id).first()
        if thisuser is None:
            return gera_response(404, 'User not found', None)
        return thisuser
    
    def to_json(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'password': self.password,
            'is_active': self.is_active,
            'is_anonymous': self.is_anonymous
        }
    def check_password(self, password):
        return (self.password == password)
    
    #get str of id
    def get_id(self):
        return str(self.id)
    
#classe que representa o post
class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80))
    content = db.Column(db.Text)
    pub_date = db.Column(db.DateTime)
    category = db.Column(db.String(80))
    author=db.Column(db.String(80), db.ForeignKey('user.username'))
    def __init__(self, title, content, category, author):
        self.title = title
        self.content= content
        self.category = category
        self.pub_date = datetime.utcnow()
        self.author = author
    def __repr__(self):
        return '<Post %r>' % self.title
    
    def to_json(self):
        return {"id": self.id, "title": self.title, "content": self.content, "pub_date": self.pub_date.strftime("%m/%d/%Y, %H:%M:%S"), "category": self.category}

    

@app.route("/<name>/")
@app.route("/")
def index(name=None):
    print(current_user)
    posts = Posts.query.all()
    
    return render_template("./index.html",name="MY HOME",day=get_day(),posts=posts)


@app.route("/about-me/")
def about(name=None):
    
    posts = Posts.query.all()
    mylogos=os.listdir(os.path.realpath("./static/img/mylogos"))    
    return render_template("./about-me.html",name="Sobre mim",day=get_day(),posts=posts,mylogos=mylogos)
    
@app.route("/contact/")
def contact(name=None):
    return render_template("./contact.html",name="Contato",day=get_day())


@app.route("/timer/")
def timer(name=None):
    return render_template("./timer.html",name="Timer",day=get_day())

def get_day():
    today = datetime.today()
    day_name=today.strftime("%A  - %D")
    return day_name


    

#Explicação detalhada do metodo abaixo:
#a função abaixo é responsável por gerar um json com os dados para cada função POST, GET, PUT, DELETE
def gera_response(status_code, message, data, error=None):
    
    response = {}
    response['message'] = message
    response['data'] = data
    response['error'] = error
    return Response(json.dumps(response), status=status_code, mimetype='application/json')

  

#my CRUD
#create
@app.route("/create/", methods=["POST"])
@login_required
def create():
    try:
        body = request.get_json()
        
        title = body["title"]
        content = body["content"]
        category = body["category"]
        author=body["author"]
        post = Posts(title, content, category, author)
        db.session.add(post)
        db.session.commit()
        return gera_response(201, "post", post.to_json(), "Criado com sucesso")
    except Exception as e:
        print('Erro', e)
        return gera_response(400, "post", {}, "Erro ao cadastrar")
    
@app.route("/create_user/", methods=["POST"])
@login_required
def create_user():
    try:
        body = request.get_json()
        username = body["username"]
        email = body["email"]
        password = body["password"]
        user = User(username, email, password)
        db.session.add(user)
        db.session.commit()
        return gera_response(201, "user", user.to_json(), "Criado com sucesso")
    except Exception as e:
        print('Erro', e)
        return gera_response(400, "user", {}, "Erro ao cadastrar")

#read
@app.route("/read/<int:id>/", methods=["GET"])
@login_required
def read(id):
    try:
        post = Posts.query.get(id)
        print(post.to_json())
        return gera_response(200, "post", post.to_json(), "Lido com sucesso")
    except Exception as e:
        print('Erro', e)
        return gera_response(400, "post", {}, e)

#update
@app.route("/update", methods=["PUT"])
@login_required
def update():
    try:
        body = request.get_json()
        post = Posts.query.filter_by(id=body["id"]).first()
       
        post.title = body["title"]
        post.content = body["content"]
        post.category = body["category"]
        db.session.commit()
        return gera_response(200, "post", post.to_json(), "Atualizado com sucesso")
    except Exception as e:
        print('Erro', e)
        return gera_response(400, "post", {}, e)

#delete  
@app.route("/delete/<int:id>", methods=["DELETE"])
@login_required
def delete(id):
    try:
        post = Posts.query.get(id)
        db.session.delete(post)
        db.session.commit()
        return gera_response(200, "post", post.to_json(), "Deletado com sucesso")
    except Exception as e:
        print('Erro', e)
        return gera_response(400, "post", {}, e)


#if __name__ == "__main__":
    #app.run(host="0.0.0.0",port=8080)
