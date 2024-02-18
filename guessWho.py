from server import app, db, cursor
from flask import request, jsonify

@app.route('/messages', methods=['GET'])
def getMessages():
    senders = request.args.get("senders").split(",")
    quantity = request.args.get("quantity")
    length = request.args.get("length")
    token = request.args.get("token")
    if token is None:
        return jsonify({'status': 'unauthorized'})

    messages = []
    for sender in senders:
        cursor.execute(
            'SELECT * FROM Messages WHERE sender = ? AND LENGTH(content) >= 15 ORDER BY RANDOM() LIMIT ?', (sender, quantity))
        messages.append(cursor.fetchall())

    if messages:
        return jsonify(messages)

    return jsonify({'status': 'error'})


@app.route('/leaderboards', methods=['POST'])
def postScore():
    data = request.get_json()
    username = data["username"]
    score = data["score"]
    game = data["game"]

    cursor.execute(
        "SELECT * FROM Scores WHERE username = ? AND game = ?", (username, game))

    entry = cursor.fetchone()
    # update the score if the user already has an entry
    if entry:
        if score > int(entry[1]):
            cursor.execute("UPDATE Scores SET score = ? WHERE username = ? AND game = ?",
                           (score, username, game))
    else:
        cursor.execute("INSERT INTO Scores VALUES(?,?,?)",
                       (username, score, game))
    db.commit()

    return jsonify({'status': 'success'})


@app.route('/leaderboards', methods=['GET'])
def getLeaderboard():
    games = request.args.get("games").split(",")

    scores = {}
    for game in games:
        cursor.execute(
            'SELECT * FROM Scores WHERE game = ? ORDER BY score DESC', (game,))
        scores[game] = cursor.fetchall()

    if scores:
        return jsonify(scores)
    return jsonify({'status': 'error'})