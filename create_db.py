import sqlite3
import datetime

# إنشاء قاعدة البيانات
conn = sqlite3.connect("referrals.db")
c = conn.cursor()

# إنشاء جدول الإحالات
c.execute("""
CREATE TABLE IF NOT EXISTS referrals (
    user_id INTEGER PRIMARY KEY,
    rep_id TEXT,
    date_joined TEXT
)
""")

conn.commit()
conn.close()

print("✅ تم إنشاء قاعدة البيانات.")