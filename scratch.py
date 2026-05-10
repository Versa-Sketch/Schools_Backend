import sqlite3
conn = sqlite3.connect('db.sqlite3')
cur = conn.cursor()
cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='core_user';")
row = cur.fetchone()
print('core_user:')
print(row[0] if row else 'Not found')
