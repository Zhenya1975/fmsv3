from flask import Flask, render_template, request, flash
from extensions import extensions
from routes.routes import home
from flask_socketio import SocketIO
import os

db_dir = os.path.abspath(os.path.dirname(__file__)) + "/database"

app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123456@localhost:5432/fms_v3_db'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123456@db:5432/postgres'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(db_dir, 'datab.db')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = 'secret string'


db = extensions.db

migrate = extensions.migrate
socketio = extensions.socketio

socketio.init_app(app)

db.init_app(app)
migrate.init_app(app, db, render_as_batch=True)

app.register_blueprint(home)

if __name__ == '__main__':
    app.run(debug=True)
