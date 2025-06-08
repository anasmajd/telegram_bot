import sqlite3

# فتح الاتصال بقاعدة البيانات
conn = sqlite3.connect("referrals.db")
c = conn.cursor()

# إنشاء الجدول (لو لم يكن موجودًا)
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