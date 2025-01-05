import dataset

db = dataset.connect('sqlite:///chat.db')
room_table = db['room']
room_table.insert(dict(roomid="abc", name="データサイエンスプログラミングX", comment="データサイエンスプログラミングXのエントリーページです。"))
room_table.insert(dict(roomid="efg", name="データサイエンスプログラミングY", comment="データサイエンスプログラミングYのエントリーページです。"))

chat_table = db['abc']
chat_table.insert(dict(text="こんにちは", textid="1", userid="1", likes=0, isAnswerd=False))

db.executable.invalidate()
db.executable.engine.dispose()
db.close()
