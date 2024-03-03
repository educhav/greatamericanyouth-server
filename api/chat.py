from server import db, cursor, socketio, lock, CHAT_MEDIA_PATH
from flask_socketio import send
import os, uuid

@socketio.on('message')
def sendMessage(data):
    match data['type']:
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
            send(data, broadcast=True)

    with lock:
        cursor.execute('INSERT INTO ChatMessages VALUES(?,?,?,?)',
                       (sender, time, content, media))
        db.commit()