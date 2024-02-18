from server import app, db, cursor, lock
from flask import request, jsonify
from flask_jwt_extended import jwt_required
import os, json, uuid

@app.route('/article', methods=['GET'])
def getArticles():
    username = request.args.get("username")
    urlName = request.args.get("urlName")

    if username and urlName:
        return jsonify({'status': 'incorrect usage of endpoint'})

    with lock:
        if username:
            cursor.execute(
                'SELECT * FROM Articles WHERE username = ? ORDER BY date DESC', (username,))
        elif urlName:
            cursor.execute(
                'SELECT * FROM Articles WHERE urlName = ?', (urlName,))
        else:
            cursor.execute(
                'SELECT * FROM Articles ORDER BY date DESC')

        articles = cursor.fetchall()

        response = []
        for article in articles:
            response.append({attr[0]: val for (attr, val)
                            in zip(cursor.description, article)})

    return jsonify(response)


@app.route('/article-meta', methods=['GET'])
def getArticleMetadata():
    urlName = request.args.get('urlName')
    getAll = request.args.get('getAll')
    with lock:
        if getAll:
            cursor.execute(
                'SELECT thumbnail, title, description, author, avatar FROM Articles WHERE urlName = ? ORDER BY date DESC', (urlName,))
            row = cursor.fetchone()
            response = {attr[0]: val for (
                attr, val) in zip(cursor.description, row)}
            return jsonify(response)
        cursor.execute(
            'SELECT thumbnail, title, description, author, avatar, urlName, audioUrl, published FROM Articles ORDER BY date DESC')
        rows = cursor.fetchall()
        articles = []
        for row in rows:
            articles.append({attr[0]: val for (
                attr, val) in zip(cursor.description, row)})
        response = articles
    return jsonify(response)
        

@jwt_required()
@app.route('/article', methods=['POST'])
def postArticle():
    data = request.form
    urlName = data["urlName"]
    title = data["title"]
    author = data["author"]
    description = data["description"]
    date = data["date"]
    username = data["username"]
    avatarName = data["avatarName"]
    thumbnailName = data["thumbnailName"]
    avatar = request.files['avatar']
    thumbnail = request.files['thumbnail']
    tags = request.form.getlist('tags')
    sections = request.form.getlist('sections')

    cursor.execute('SELECT * FROM Articles WHERE urlName = ?', (urlName,))

    if cursor.fetchone():
        return jsonify({'status': 'duplicate'})

    mediaDirectory = os.path.join('article-media', urlName)

    if not os.path.exists(mediaDirectory):
        os.mkdir(mediaDirectory)

    avatarFileExtension = avatarName.split('.')[1]
    avatarPath = os.path.join(mediaDirectory, 'avatar.' + avatarFileExtension)
    avatar.save(avatarPath)

    thumbnailFileExtension = thumbnailName.split('.')[1]
    thumbnailPath = os.path.join(mediaDirectory, 'thumbnail.' + thumbnailFileExtension)
    thumbnail.save(thumbnailPath)

    tagsText = ""
    if tags:
        tagsText = json.dumps(tags)

    sectionsText = []

    for (i, section) in enumerate(sections):
        sectionText = {'content': section, 'media': []}

        j = 0
        while True:
            field_name = "sections[" + str(i) + "][" + str(j) + "]"
            if field_name not in request.files:
                break
            media = request.files[field_name]
            name = data["names[" + str(i) + "][" + str(j) + "]"]
            text = data["texts[" + str(i) + "][" + str(j) + "]"]

            uuidHash = str(uuid.uuid4())[:8]
            split_ = name.split(".")

            path = os.path.join(mediaDirectory, split_[0] + uuidHash + "." + split_[1])
            media.save(path)

            sectionText['media'].append({
                'path': path,
                'text': text
            })

            j += 1

        sectionsText.append(sectionText)

    sectionText = json.dumps(sectionsText)
    audioUrl = None

    cursor.execute('INSERT INTO Articles VALUES(?,?,?,?,?,?,?,?,?,?,?,?)', (urlName, title, author,
                   date, description, 1, username, thumbnailPath, avatarPath, tagsText, sectionsText, audioUrl))

    db.commit()

    return jsonify({'status': 'success'})
