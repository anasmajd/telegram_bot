import sqlite3

# إنشاء أو فتح قاعدة بيانات
conn = sqlite3.connect('referrals.db')
cursor = conn.cursor()

# إنشاء جدول referrals
cursor.execute('''
    CREATE TABLE IF NOT EXISTS referrals (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        rep_id TEXT,
        date_joined TEXT
    )
''')

conn.commit()
conn.close()

print("✅ قاعدة البيانات referrals.db تم إنشاؤها بنجاح!")