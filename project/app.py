from flask import Flask, render_template, request, flash
from extensions import extensions
from routes.routes import home
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123456@localhost:5432/fms_v3_db'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123456@db:5432/fms_v3_db'
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
