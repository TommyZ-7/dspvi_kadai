from flask import Flask, render_template , request, jsonify
from flask_socketio import SocketIO, emit

global messages

app = Flask(__name__)
socketio = SocketIO(app)

messages = ["sdasd", "asdasd", "asdasd"]

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

@app.route('/test/realtime/')
def test_data_realtime():
    return render_template("/test/realtime/page.html")

@socketio.on('join')
def on_join(data):
    print(data)
    emit("message_history", messages)

@socketio.on('message')
def handle_message(message):
    print('received message: ' + message)
    messages.append(message)
    print(messages)
    emit("new_message", messages , broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)
