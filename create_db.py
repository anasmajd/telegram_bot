import sqlite3

# إنشاء الاتصال بقاعدة البيانات (لو مش موجودة سيتم إنشاؤها)
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

# حفظ التغييرات وإغلاق الاتصال
conn.commit()
conn.close()

print("✅ تم إنشاء قاعدة البيانات referrals.db والجدول بنجاح.")