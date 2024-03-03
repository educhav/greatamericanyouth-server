from server import app, db, cursor, logger, USER_MEDIA_PATH, USER_MEDIA_URL
from flask import request, jsonify
from werkzeug.exceptions import UnprocessableEntity
from flask_jwt_extended import get_jwt_identity, jwt_required, create_access_token
import os, uuid, hashlib

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data["username"]
    password = data["password"]
    hashed_password = hash(password)
    params = (username, hashed_password)
    cursor.execute(
        'SELECT * FROM Users WHERE username = ? AND password = ?', params)
    user = cursor.fetchone()
    logger.info(user[3])
    if user:
        return jsonify({'status': 'success', 
                        'role': user[2], 
                        'token': create_access_token(identity={"username": username, "role": user[2], "profilePhoto": user[3]})})

    return jsonify({'status': 'error'})


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data["username"]
    password = data["password"]
    role = "normie"
    hashedPassword = hash(password)
    cursor.execute('SELECT * FROM Users WHERE username = ?', (username,))
    account = cursor.fetchone()
    # Username already exists
    if account:
        return jsonify({'status': 'error'})

    params = (username, hashedPassword, role, None)

    cursor.execute('INSERT INTO Users (username, password, role, profilePhoto) VALUES (?, ?, ?, ?)',
                   params)
    db.commit()
    return jsonify({'status': 'success', 'role': "normie", 'token': create_access_token(identity={"username": username, "role": "normie"})})

@app.route('/profile-photo', methods=['POST'])
@jwt_required()
def uploadProfilePhoto():
    if not request.files or 'image' not in request.files:
        return jsonify({'status': 'error', 'profilePhoto': None})

    profilePhoto = request.files['image']
    username = get_jwt_identity()['username']
    mediaDirectory = os.path.join(USER_MEDIA_PATH, username)

    if not os.path.exists(mediaDirectory):
        os.mkdir(mediaDirectory)
    
    uuidHash = str(uuid.uuid4())[:8]
    profilePhotoFileName = profilePhoto.filename.split(".")[0] + "_" +  uuidHash + "." + profilePhoto.filename.split(".")[1]
    profilePhotoUrl = USER_MEDIA_URL + username + "/" + profilePhotoFileName
    profilePhotoPath = os.path.join(mediaDirectory, profilePhotoFileName)
    profilePhoto.save(profilePhotoPath)

    cursor.execute('UPDATE Users SET profilePhoto = ? WHERE username = ?', (profilePhotoUrl, username))
    db.commit()

    return jsonify({'status': 'success', 'profilePhoto': profilePhotoUrl})

def hash(password):
    return hashlib.sha256(password.encode()).hexdigest()