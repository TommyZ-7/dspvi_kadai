from flask import Flask, render_template , request, jsonify
from flask_socketio import SocketIO, emit, send
import dataset
import json as JSON
import uuid

global messages

app = Flask(__name__)
socketio = SocketIO(app)

ACCESS_TOKEN = "abcdx"
DEBUG = False
if DEBUG:
    API_KEY = "a"
else:
    API_KEY = uuid.uuid4()
    



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

@app.route('/create/')
def create():
    return render_template("/create/page.html")

@app.route('/create/<roomid>/playarea', methods=['GET'])
def create_playarea(roomid):
    try:
        key = request.args.get('api_key', default=None, type=str)
        key = key.format(key)
        if key != str(API_KEY):
            return "invalid apiKey"
    except:
        return "invalid apiKey"
    try:
        db = dataset.connect('sqlite:///chat.db')
        room_table = db['room']
        roomdata = room_table.find_one(roomid=roomid)
        users = len(roomdata["joinedUser"])
        db.executable.invalidate()
        db.executable.engine.dispose()
        db.close()
        returnData = {
            "roomid": roomid,
            "name": roomdata["name"],
            "comment": roomdata["comment"],
            "nowAnswering": roomdata["nowAnswering"],
            "nowAnsweringTextid": roomdata["nowAnsweringTextid"],
            "api_key": API_KEY,
            "answerdCount": roomdata["answerdCount"],
            "users": users
        }
        return render_template("/create/playarea/page.html", roomdata=returnData)
    except:
        return "404 Not Found"

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
            "nowAnswering": roomdata["nowAnswering"],
            "nowAnsweringTextid": roomdata["nowAnsweringTextid"],
            
        }
        return render_template("/entry/playarea/page.html", roomdata=returnData)
    except:
        return "404 Not Found"

@app.route('/create/api/checkID', methods=['POST'])
def checkID():

    data = str(request.data.decode('utf-8'))
    data = JSON.loads(data)
    if data["id"] == ACCESS_TOKEN:
        return jsonify({"status": "ok", "api_key": API_KEY})
    else:
        return jsonify({"status": "ng"})


@app.route('/api/createroom', methods=['POST'])
def create_room():
    data = str(request.data.decode('utf-8'))
    data = JSON.loads(data)
    if data["api_key"] == str(API_KEY):
        db = dataset.connect('sqlite:///chat.db')
        room_table = db['room']
        room_uuid = "tbl-" + str(uuid.uuid4())
        room_table.insert(dict(roomid= room_uuid, name=data["name"], comment=data["comment"], nowAnswering="", nowAnsweringTextid="", answerdCount=0, joinedUser=[]))
        db.executable.invalidate()
        db.executable.engine.dispose()
        db.close()
        return jsonify({ "status": "ok", "roomid": room_uuid })
    else:
        return jsonify({"status": "ng"})

@app.route('/api/answering', methods=['POST'])
def answering():
    data = str(request.data.decode('utf-8'))
    data = JSON.loads(data)
    if data["api_key"] == str(API_KEY):
        emitData = {
            "text": data["text"],
            "status": "start",
            "textid" : data["textid"]
        }
        db = dataset.connect('sqlite:///chat.db')
        room_table = db['room']
        roomdata = room_table.find_one(roomid=data["roomid"])
        roomdata["nowAnswering"] = data["text"]
        roomdata["nowAnsweringTextid"] = data["textid"]
        room_table.update(roomdata, ['roomid'])
        db.executable.invalidate()
        db.executable.engine.dispose()
        db.close()
        emit("answering/" + data["roomid"], emitData, broadcast=True, namespace=None)
        return jsonify({"status": "ok"})
    else:
        return jsonify({"status": "invalid api_key"})
    
@app.route('/api/answercompleted', methods=['POST'])
def answercompleted():
    data = str(request.data.decode('utf-8'))
    data = JSON.loads(data)
    if data["api_key"] == str(API_KEY):
        emitData = {
            "status": "end",
            "textid": data["textid"]
        }
        db = dataset.connect('sqlite:///chat.db')
        room_table = db['room']
        roomdata = room_table.find_one(roomid=data["roomid"])
        roomdata["nowAnswering"] = ""
        roomdata["nowAnsweringTextid"] = ""
        roomdata["answerdCount"] += 1
        room_table.update(roomdata, ['roomid'])
        table = db[data["roomid"]]
        chatdata = table.find_one(textid=data["textid"])
        chatdata["isAnswerd"] = True    
        table.update(chatdata, ['textid'])
        db.executable.invalidate()
        db.executable.engine.dispose()
        db.close()
        
        emit("answering/" + data["roomid"], emitData, broadcast=True, namespace=None)
        return jsonify({"status": "ok"})
    else:
        return jsonify({"status": "invalid api_key"})
    



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
    table = db['room']
    roomdata = table.find_one(roomid=joinData["roomid"])
    #joinedUserにjoinData["userid"]が見つからない場合追加する
    if joinData["userid"] not in roomdata["joinedUser"]:
        roomdata["joinedUser"].append(joinData["userid"])
        table.update(roomdata, ['roomid'])
    else:
        pass
    userCount = {
        "users":len(roomdata["joinedUser"])
    }


    db.executable.invalidate()
    db.executable.engine.dispose()
    db.close()
    emit("user_join/" + joinData["roomid"], userCount, broadcast=True)
    emit("message_history/" + joinData["roomid"], returnData, broadcast=False)

@socketio.on('hostJoin')
def on_host_join(joinData):

    db = dataset.connect('sqlite:///chat.db')
    room_table = db[joinData["roomid"]]
    data = []
    isLike = []
    for row in room_table:
        data.append(row)

    
    print(isLike)
    
    returnData = {
        "data": data,
    }

    db.executable.invalidate()
    db.executable.engine.dispose()
    db.close()
    emit("message_history/" + joinData["roomid"], returnData, broadcast=False)

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
    emit("new_message/" + roomid, returnData, broadcast=True)

@socketio.on('like_plus')
def handle_like_plus(data):
    print('received textid: ' + data["textid"])
    print('received roomid: ' + data["roomid"])
    print('received userid: ' + data["userid"])
    text_db = dataset.connect('sqlite:///textid.db')
    text_table = text_db[data["textid"]]
    
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
        emit("like_plus_return/" + data["roomid"], returnData, broadcast=True)
    else:
        pass

    

if __name__ == '__main__':
    socketio.run(app, debug=False, host="0.0.0.0")
