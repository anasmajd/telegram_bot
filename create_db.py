import sqlite3

# إنشاء الاتصال بقاعدة البيانات
conn = sqlite3.connect('referral.db')
c = conn.cursor()

# إنشاء جدول الإحالات
c.execute('''
    CREATE TABLE IF NOT EXISTS referrals (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        full_name TEXT,
        referrer_id INTEGER,
        referrer_username TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')

# حفظ التغييرات
conn.commit()
conn.close()

print("✅ تم إنشاء قاعدة البيانات بنجاح.")