import sqlite3, argparse, threading, logging, os
from datetime import timedelta
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO

DB_PATH = '/var/www/greatamericanyouth/server/db/greatamericanyouth.db'
LOG_PATH = '/var/www/greatamericanyouth/server/logs/api-server.log'
USER_MEDIA_PATH = '/var/www/greatamericanyouth/server/media/user'
USER_MEDIA_URL = 'https://greatamericanyouth.com/user-media/'
CHAT_MEDIA_PATH = '/var/www/greatamericanyouth/server/media/chat'
ARTICLE_MEDIA_PATH = '/var/www/greatamericanyouth/server/media/article'

db = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = db.cursor()

app = Flask(__name__)

parser = argparse.ArgumentParser(
                    prog='greatamericanyouth-api',
                    description='API Server for the greatamericanyouth')

parser.add_argument('-d', '--dev', action='store_true')
args = parser.parse_args()
devMode = args.dev

app.config['JWT_SECRET_KEY'] = os.environ['JWT_TOKEN']
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=90)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024 * 1024

jwtManager = JWTManager(app)

socketio = SocketIO(app, cors_allowed_origins='*')
socketio.init_app(app, message_queue=None,
                 cors_allowed_origins="*", max_http_buffer_size=1024*1024*1024)

lock = threading.Lock()

if not devMode: 
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s %(message)s',
                        handlers=[logging.FileHandler(LOG_PATH),
                                logging.StreamHandler()])
from api import *

if __name__ == "__main__":
    socketio.run(app, allow_unsafe_werkzeug=True)