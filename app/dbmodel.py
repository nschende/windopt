from mongoengine import *
import json
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired
from flask.ext.httpauth import HTTPBasicAuth
from flask import Flask, abort, request, jsonify, g, url_for
from app import app
import cPickle
from config import DB_URI, DB_USER, DB_PWD, ENV_NAME

if ENV_NAME == 'local':
    # If local, assume that there is a local mongo instance
    conn = connect('windops', host = 'localhost', port = 27017)
else:
    # Otherwise, use env variables to connect
    conn = connect('windops', host='mongodb://'+ DB_USER + ':' + DB_PWD + '@' + DB_URI)


auth = HTTPBasicAuth(scheme = 'FormBased')

app.config['SECRET_KEY'] = 'die luft der freiheit weht'
class User(Document):
    username = StringField(unique=True)
    password = StringField()
    
    def hash_password(self, password):
        self.password = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password)
    
    def generate_auth_token(self, expiration = 600):
        s = Serializer(app.config['SECRET_KEY'], expires_in = expiration)
        return s.dumps({ 'username': self.username })

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None # valid token, but expired
        except BadSignature:
            return None # invalid token
        user = User.objects(username=data['username'])[0]
        return user

class Role(Document):
    name = StringField(unique = True)
    description = StringField()


@auth.verify_password
def verify_password(username_or_token, password):
    # first try to authenticate by token
    user = User.verify_auth_token(username_or_token)
    if not user:
        # try to authenticate with username/password
        try:
            user = User.objects(username=username_or_token)[0]
            if not user.verify_password(password): return False
        except (User.DoesNotExist, IndexError):
            return False
    g.user = user
    return True

@app.route('/api/auth/login', methods=['POST'])
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token()
    return jsonify({ 'token': token.decode('ascii') })

# Create admin account
@app.before_first_request
def create_admin():
    try:
        User.objects.get(username = 'admin')
    except User.DoesNotExist:
        admin = User(username = 'admin')
        admin.hash_password('admin')
        admin.save()
    return

class Project(Document):
    name = StringField(unique=True)
    user = ReferenceField(User)
    windHeight = IntField()
    windTMatrix = BinaryField()
    windSeasonality = BinaryField()
    
    def save_TMatrix(self,tmat):
        #convert transition matrix to binary and assign
        self.windTMatrix = cPickle.dumps(tmat, protocol=2)
    
    def get_TMatrix(self):
        if self.windTMatrix:
            return cPickle.loads(self.windTMatrix)
        else: return None

    def save_Seasonality(self,matrix):
        #convert transition matrix to binary and assign
        self.windSeasonality = cPickle.dumps(matrix, protocol=2)
    
    def get_Seasonality(self):
        if self.windSeasonality:
            return cPickle.loads(self.windSeasonality)
        else: return None
        
    def save_Stationary(self,matrix):
        #convert transition matrix to binary and assign
        self.windStationary = cPickle.dumps(matrix, protocol=2)
    
    def get_Stationary(self):
        if self.windStationary:
            return cPickle.loads(self.windStationary)
        else: return None
    
    
        
        
        
        
        
        
    
    
    
