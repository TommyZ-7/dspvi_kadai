import dataset

db = dataset.connect('sqlite:///chat.db')
room_table = db['room']
room_table.insert(dict(roomid="lll", name="データサイエンスプログラミング2", comment="データサイエンスプログラミングXのエントリーページです。"))


db.executable.invalidate()
db.executable.engine.dispose()
db.close()
