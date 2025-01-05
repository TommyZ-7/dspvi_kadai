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
    try:
        db = dataset.connect('sqlite:///chat.db')
        room_table = db['room']
        roomdata = room_table.find_one(roomid=roomid)
        db.executable.invalidate()
        db.executable.engine.dispose()
        db.close()
        returnData = {
            "roomid": roomid,
            "name": roomdata["name"],
            "comment": roomdata["comment"],
        }
        return render_template("/entry/page.html", roomdata=returnData)
    except:
        return "404 Not Found"

@app.route('/entry/<roomid>/playarea/')
def playarea(roomid):
    try:
        db = dataset.connect('sqlite:///chat.db')
        room_table = db['room']
        roomdata = room_table.find_one(roomid=roomid)
        db.executable.invalidate()
        db.executable.engine.dispose()
        db.close()
        returnData = {
            "roomid": roomid,
            "name": roomdata["name"],
            "comment": roomdata["comment"],
        }
        return render_template("/entry/playarea/page.html", roomdata=returnData)
    except:
        return "404 Not Found"


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
def on_join(joinData):
    print("received id: " + joinData["roomid"])
    print("received id: " + joinData["userid"])
    db = dataset.connect('sqlite:///chat.db')
    text_db = dataset.connect('sqlite:///textid.db')    
    room_table = db[joinData["roomid"]]
    data = []
    isLike = []
    for row in room_table:
        data.append(row)
        if text_db[row["textid"]].find_one(userid=joinData["userid"]) != None:
            isLike.append(True) 
        else:
            isLike.append(False)
    
    print(isLike)
    
    returnData = {
        "data": data,
        "isLike": isLike
    }
    text_db.executable.invalidate()
    text_db.executable.engine.dispose()
    text_db.close()
    db.executable.invalidate()
    db.executable.engine.dispose()
    db.close()
    emit("message_history", returnData, broadcast=False)

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
    text_db = dataset.connect('sqlite:///textid.db')
    text_table = text_db[message["textid"]]
    text_table.insert(dict(userid=message["userid"]))
    text_db.executable.invalidate()
    text_db.executable.engine.dispose()
    text_db.close()
    
    returnData = { "text": message["text"], "textid": message["textid"], "userid": message["userid"], "likes": 0, "isAnswerd": False }
    emit("new_message", returnData, broadcast=True)

@socketio.on('like_plus')
def handle_like_plus(data):
    print('received textid: ' + data["textid"])
    print('received roomid: ' + data["roomid"])
    print('received userid: ' + data["userid"])
    text_db = dataset.connect('sqlite:///textid.db')
    text_table = text_db[data["textid"]]
    #text_tableにtextidが存在するか確認
    


    if text_table.find_one(userid=data["userid"]) == None:
        text_table.insert(dict(userid=data["userid"]))
        db = dataset.connect('sqlite:///chat.db')
        chat_table = db[data["roomid"]]
        chatdata = chat_table.find_one(textid=data["textid"])
        chatdata["likes"] += 1
        chat_table.update(chatdata, ['textid'])
        db.executable.invalidate()
        db.executable.engine.dispose()
        db.close()
        text_db.executable.invalidate()
        text_db.executable.engine.dispose()
        text_db.close()
        returnData = { 
            "textid": data["textid"] ,
            "userid": data["userid"],
            "index" : data["index"]
        }
        emit("like_plus_return", returnData, broadcast=True)
    else:
        pass

    

if __name__ == '__main__':
    socketio.run(app, debug=False, host="0.0.0.0")
