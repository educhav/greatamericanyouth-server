from server import db, cursor, socketio, lock, CHAT_MEDIA_PATH, CHAT_MEDIA_URL, logger, app, jsonify 
from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required 
from flask_socketio import send
import os, uuid, json 
from datetime import datetime

@jwt_required()
@app.route('/party-profile-photos', methods=['GET'])
def getPartyInfo():
    role = get_jwt_identity()['role']
    if role != 'party':
        return jsonify({'status': 'Unauthorized'})

    cursor.execute('SELECT username, profilePhoto FROM Users WHERE role = ?', ('party',))
    rows = cursor.fetchall()
    map = {}
    for row in rows:
        username, profilePhoto = row
        map[username] = profilePhoto
    return jsonify(map)

@jwt_required()
@app.route('/chat-media-gallery', methods=['GET'])
def getMediaGallery():
    startTimestamp = request.args.get("startTimestamp")
    endTimestamp = request.args.get("endTimestamp")

    if startTimestamp and endTimestamp:
        cursor.execute('SELECT * FROM ChatMessages WHERE media IS NOT NULL AND time BETWEEN ? AND ?', (startTimestamp, endTimestamp))
    else:
        cursor.execute('SELECT * FROM ChatMessages WHERE media IS NOT NULL')
    media = cursor.fetchall()
    return jsonify(media)

@jwt_required()
@app.route('/chat-search', methods=['GET'])
def searchChat():
    searchString = request.args.get("searchString")
    if not searchString:
        return jsonify({'status': 'error'})
    cursor.execute('SELECT * FROM ')

@jwt_required()
@app.route('/chat-messages', methods=['GET'])
def getChatMessages():
    role = get_jwt_identity()['role']
    if role != 'party':
        return jsonify({'status': 'Unauthorized'})
    size = request.args.get("size")
    startingIndex = request.args.get("startingIndex")
    cursor.execute('SELECT * FROM ChatMessages WHERE index BETWEEN ? AND ? ORDER BY index', (startingIndex, startingIndex + size))
    messages = cursor.fetchall()
    return jsonify({'status': 'success', 'messages': messages})

@socketio.on('message')
def sendMessage(data):
    # For some reason mobile request is registered as string and not dict
    if type(data).__name__ == 'str':
        data = json.loads(data)
    
    if 'type' not in data:
        return jsonify({'status': 'error'})
    
    messageType = data['type']
    sender = None
    time = None
    content = None
    mediaUrl = None

    match messageType:
        case 'sql':
            sender = data['sender']
            time = data['time']
            content = data['content']
            cursor.execute(content)
            response = cursor.fetchall()
            send({'type': messageType, 
                  'sender': sender, 
                  'media': None,
                  'time': time, 
                  'content': str(response)}, broadcast=True)
        case 'mobile-photo' | 'mobile-video':
            sender = data['sender']
            time = data['time']
            media = data['media']
            fileType = data['fileType']
            monthYear = convertUnixTimestampToMonthYear(time)
            mediaDirectory = os.path.join(CHAT_MEDIA_PATH, sender)

            if not os.path.exists(mediaDirectory):
                os.mkdir(mediaDirectory)

            chatMediaDirectory = os.path.join(mediaDirectory, monthYear)

            if not os.path.exists(chatMediaDirectory):
                os.mkdir(chatMediaDirectory)

            uuidHash = str(uuid.uuid4())[:18]
            filePath = os.path.join(chatMediaDirectory, f"{uuidHash}.{fileType}")
            with open(filePath, "wb") as file:
                file.write(signedBytesArrayToBytes(media))

            mediaUrl = f"{CHAT_MEDIA_URL}{sender}/{monthYear}/{uuidHash}.{fileType}"
            send({'sender': sender, 
                  'time': time, 
                  'content': None, 
                  'type': messageType,
                  'media': mediaUrl}, broadcast=True)
            
        case 'media':
            sender = data['sender']
            time = data['time']
            month = data['month']
            buffer = data['buffer']
            name = data['name']
            fileType = data['fileType']

            mediaDirectory = os.path.join(CHAT_MEDIA_PATH, sender)
            if not os.path.exists(mediaDirectory):
                os.mkdir(mediaDirectory)

            chat_media_dir = os.path.join(mediaDirectory, month)
            if not os.path.exists(chat_media_dir):
                os.mkdir(chat_media_dir)

            hash_ = str(uuid.uuid4())[:8]
            split_ = name.split(".")
            hashed_name = split_[0] + '_' + hash_ + '.' + split_[1]

            path = os.path.join(chat_media_dir, hashed_name)
            with open(path, "wb") as file:
                file.write(buffer)

            send({'type': data['type'], 'sender': sender,
                 'time': time, 'name': hashed_name, 'path': path,
                  'fileType': fileType}, broadcast=True)

        case 'user-message':
            send({'type': data['type'], 
                  'sender': data['sender'], 
                  'time': data['time'], 
                  'content': data['content'],
                  'media': None
                  }, broadcast=True)

    if 'type' in data and 'sender' in data and 'time' in data:
        with lock:
            cursor.execute('INSERT INTO ChatMessages VALUES(?,?,?,?,?)',
                        (messageType, sender, time, content, mediaUrl))
            db.commit()

def signedBytesArrayToBytes(arr):
    return bytes([(byte + 256) % 256 if byte < 0 else byte for byte in arr])

def convertUnixTimestampToMonthYear(unixTimestamp):
    dt = datetime.fromtimestamp(unixTimestamp // 1000)
    month = dt.strftime('%b')
    year = dt.strftime('%Y')
    return month + year