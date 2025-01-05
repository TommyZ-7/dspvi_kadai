from flask import Flask, render_template , request, jsonify
from flask_socketio import SocketIO, emit
import dataset
import json as JSON

global messages

app = Flask(__name__)
socketio = SocketIO(app)


@app.route('/')
def index():
    return render_template('page.html')

@app.route('/test/data/')
def test_data():
    data = {
        'name': 'John Doe',
        'age': 25,
    }
    return render_template("/test/data/page.html", data=data)

@app.route("/entry/<roomid>/")
def entry(roomid):
    roomdata = {
        "roomid": roomid,
        "name": "データサイエンスプログラミングX",
        "comment": "データサイエンスプログラミングXのエントリーページです。",
    }
    return render_template("/entry/page.html", roomdata=roomdata)

@app.route('/entry/<roomid>/playarea/')
def playarea(roomid):
    roomdata = {
        "roomid": roomid,
        "name": "データサイエンスプログラミングX",
        "comment": "データサイエンスプログラミングXのエントリーページです。",
    }
    return render_template("/entry/playarea/page.html", roomdata=roomdata)


@app.route('/test/realtime/')
def test_data_realtime():
    return render_template("/test/realtime/page.html")

@app.route('/api/roomdata/<roomid>/')
def get_roomdata(roomid):
    db = dataset.connect('sqlite:///chat.db')
    room_table = db['room']
    roomdata = room_table.find_one(roomid=roomid)
    db.executable.invalidate()
    db.executable.engine.dispose()
    db.close()
    
    return jsonify(roomdata)

@socketio.on('join')
def on_join(roomid):
    print(roomid)
    db = dataset.connect('sqlite:///chat.db')
    room_table = db[roomid]
    data = []
    for row in room_table:
        data.append(row)
    db.executable.invalidate()
    db.executable.engine.dispose()
    db.close()
    emit("message_history", data, broadcast=False)

@socketio.on('message')
def handle_message(message, roomid):
    print("received id: " + roomid)
    print('received message: ' + message["text"])
    db = dataset.connect('sqlite:///chat.db')
    chat_table = db[roomid]
    chat_table.insert(dict(text=message["text"], textid=message["textid"], userid=message["userid"], likes=0, isAnswerd=False))
    db.executable.invalidate()
    db.executable.engine.dispose()
    db.close()
    
    returnData = { "text": message["text"], "textid": message["textid"], "userid": message["userid"], "likes": 0, "isAnswerd": False }
    emit("new_message", returnData, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)
