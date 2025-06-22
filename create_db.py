import os
import psycopg2
from psycopg2 import sql

def init_db():
    # الاتصال بقاعدة البيانات
    conn = psycopg2.connect(os.getenv('DATABASE_URL'), sslmode='require')
    try:
        with conn.cursor() as cursor:
            # إنشاء جدول الأقسام
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    category_id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ تم إنشاء جدول الأقسام بنجاح")
            
        conn.commit()
    except Exception as e:
        print(f"❌ خطأ في إنشاء الجداول: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    init_db()
