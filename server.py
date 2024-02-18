import sqlite3, argparse, threading, logging, os
from datetime import timedelta
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO

db = sqlite3.connect('greatamericanyouth.db', check_same_thread=False)
cursor = db.cursor()

app = Flask(__name__)

parser = argparse.ArgumentParser(
                    prog='greatamericanyouth-server',
                    description='API Server for the greatamericanyouth')

parser.add_argument('-d', '--dev', action='store_true')
args = parser.parse_args()
devMode = args.dev

app.config['JWT_SECRET_KEY'] = "120iqjwtkeyorsomething_" if devMode else hash(os.environ['JWT_TOKEN'])
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
                        handlers=[logging.FileHandler('/var/www/greatamericanyouth/server/gay_server.log'),
                                logging.StreamHandler()])
from api import *

if __name__ == "__main__":
    socketio.run(app)