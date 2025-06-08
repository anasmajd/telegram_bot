import logging
import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ✅ ضع هنا التوكن الخاص بك:
TOKEN = "8028540649:AAF8bp_jvM8tibUUmzUzq1DBzwJdrNvAzRo"

# ✅ ضع هنا Admin ID (رقم معرفك الشخصي - يمكنك الحصول عليه من @userinfobot)
ADMIN_ID = 5746473556

# إعداد اللوج
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# قاعدة البيانات
conn = sqlite3.connect('referral.db')
cursor = conn.cursor()

# إنشاء جدول
cursor.execute('''
    CREATE TABLE IF NOT EXISTS referrals (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        referred_by TEXT
    )
''')
conn.commit()

# دالة start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args
    rep_id = args[0] if args else None

    # تحقق إن كان المستخدم مسجلا سابقاً
    cursor.execute('SELECT * FROM referrals WHERE user_id = ?', (user.id,))
    user_record = cursor.fetchone()

    if not user_record:
        cursor.execute('INSERT INTO referrals (user_id, username, referred_by) VALUES (?, ?, ?)',
                       (user.id, user.username, rep_id))
        conn.commit()

        # إرسال إشعار للإدارة في حال الإحالة
        if rep_id and rep_id.startswith("REP_"):
            # استخراج اسم المستخدم الخاص بالمندوب
            referrer_username = ""
            cursor.execute('SELECT username FROM referrals WHERE user_id = ?', (rep_id.replace("REP_", ""),))
            row = cursor.fetchone()
            if row:
                referrer_username = f"@{row[0]}" if row[0] else f"ID: {rep_id.replace('REP_', '')}"
            else:
                referrer_username = f"ID: {rep_id.replace('REP_', '')}"

            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"📥 إحالة جديدة!\n👤 المستخدم: {user.full_name} (@{user.username})\n🆔 ID: {user.id}\n🎯 من مندوب: {referrer_username}"
            )

    # رسالة الترحيب
    welcome_text = (
        "👋 أهلاً بك في المتجر!\n\n"
        "✅ لو دخلت من رابط إحالة ستظهر لك رسالة تأكيد.\n"
        "لو لم تدخل من رابط إحالة — اضغط الزر أدناه للدخول من رابطك الخاص.\n\n"
        "🔷 بعد الضغط، يمكنك الضغط على زر ✅ لتأكيد تسجيل الإحالة."
    )

    referral_link = f"https://t.me/{context.bot.username}?start=REP_{user.id}"

    await update.message.reply_text(welcome_text)
    await update.message.reply_text(f"🔗 اضغط هنا للدخول من رابط الإحالة: {referral_link}")

# /get_link
async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    referral_link = f"https://t.me/{context.bot.username}?start=REP_{user.id}"
    await update.message.reply_text(f"🔗 رابط الإحالة الخاص بك:\n{referral_link}")

# /my_referrals
async def my_referrals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    cursor.execute('SELECT user_id, username FROM referrals WHERE referred_by = ?', (f"REP_{user.id}",))
    referrals = cursor.fetchall()

    if referrals:
        message = "📋 إحالاتك:\n\n"
        for ref in referrals:
            username_display = f"@{ref[1]}" if ref[1] else f"ID: {ref[0]}"
            message += f"👤 {username_display}\n🆔 ID: {ref[0]}\n\n"
    else:
        message = "❌ لا يوجد لديك إحالات حتى الآن."

    await update.message.reply_text(message)

# /my_sales
async def my_sales(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    cursor.execute('SELECT COUNT(*) FROM referrals WHERE referred_by = ?', (f"REP_{user.id}",))
    count = cursor.fetchone()[0]
    await update.message.reply_text(f"📊 عدد الإحالات المسجلة لديك: {count}")

# Main
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('get_link', get_link))
    app.add_handler(CommandHandler('my_referrals', my_referrals))
    app.add_handler(CommandHandler('my_sales', my_sales))

    print("✅ Bot is running...")
    app.run_polling()