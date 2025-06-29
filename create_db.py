import os
import psycopg2
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

def init_db():
    """إنشاء جميع الجداول المطلوبة"""
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    if not DATABASE_URL:
        print("❌ يجب تعيين DATABASE_URL في ملف .env")
        return
    
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    try:
        with conn.cursor() as cursor:
            # إنشاء جدول الأقسام
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    category_id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL UNIQUE,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ تم إنشاء جدول الأقسام بنجاح")
            
            # إنشاء جدول الإحالات
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS referrals (
                    user_id BIGINT PRIMARY KEY,
                    username VARCHAR(100),
                    referrer_id BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ تم إنشاء جدول الإحالات بنجاح")
            
            # إنشاء جدول الرسائل
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    message_id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ تم إنشاء جدول الرسائل بنجاح")
            
            # إضافة فهارس لتحسين الأداء
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_referrals_referrer 
                ON referrals(referrer_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_user 
                ON messages(user_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_categories_name 
                ON categories(name)
            """)
            
            print("✅ تم إنشاء الفهارس بنجاح")
            
        conn.commit()
        print("🎉 تم إعداد قاعدة البيانات بنجاح!")
        
    except Exception as e:
        print(f"❌ خطأ في إنشاء الجداول: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    init_db()