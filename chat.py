from server import db, cursor, socketio, lock
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

            sender_dir = os.path.join('chat-media', sender)
            if not os.path.exists(sender_dir):
                os.mkdir(sender_dir)

            chat_media_dir = os.path.join(sender_dir, month)
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