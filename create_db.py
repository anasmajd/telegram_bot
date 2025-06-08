import sqlite3

# إنشاء قاعدة البيانات وجداولها
conn = sqlite3.connect("referral.db")
c = conn.cursor()

# جدول المستخدمين
c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        full_name TEXT,
        referred_by TEXT
    )
""")

# جدول الإحالات
c.execute("""
    CREATE TABLE IF NOT EXISTS referrals (
        referrer_id INTEGER,
        referred_id INTEGER,
        referred_username TEXT
    )
""")

conn.commit()
conn.close()

print("✅ تم إنشاء قاعدة البيانات بنجاح.")