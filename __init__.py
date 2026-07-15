from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import cloudinary

app = Flask(__name__)
app.config['SECRET_KEY']="12345678"
app.config["SQLALCHEMY_DATABASE_URI"] ="mysql+pymysql://root:root@127.0.0.1:3306/nhakhoadb?charset=utf8mb4"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True

cloudinary.config(cloud_name='du0quuvbl',
                  api_key='385618194935568',
                  api_secret='9jKqT5pDtyli3_ory4-jy8fkjTo')

db = SQLAlchemy(app)
login_manager = LoginManager(app)