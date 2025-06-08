import sqlite3

conn = sqlite3.connect("referrals.db")
c = conn.cursor()

c.execute('''
    CREATE TABLE IF NOT EXISTS referrals (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        rep_id TEXT,
        date_joined TEXT
    )
''')

conn.commit()
conn.close()

print("✅ تم إنشاء قاعدة البيانات بنجاح.")