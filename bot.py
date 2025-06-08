import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import logging

# ✅ ضع التوكن الخاص بك هنا 👇
BOT_TOKEN = '8028540649:AAF8bp_jvM8tibUUmzUzq1DBzwJdrNvAzRo'

# ✅ ضع معرفك كأدمن 👇
ADMIN_ID = 920325080  # ضع هنا user_id الخاص بك

# تفعيل اللوج
logging.basicConfig(level=logging.INFO)

# دالة إنشاء اتصال قاعدة بيانات
def get_db_connection():
    conn = sqlite3.connect('referral.db')
    conn.row_factory = sqlite3.Row
    return conn

# دالة start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = update.message.from_user.username or ""
    full_name = update.message.from_user.full_name
    args = context.args
    referrer_id = None
    referrer_username = None

    if args and args[0].startswith("REP_"):
        referrer_id = int(args[0].split("_")[1])

    conn = get_db_connection()
    c = conn.cursor()

    # فحص هل المستخدم موجود أصلا
    c.execute('SELECT * FROM referrals WHERE user_id = ?', (user_id,))
    if not c.fetchone():
        # لو referrer_id موجود — محاولة جلب username المندوب
        if referrer_id:
            c.execute('SELECT username FROM referrals WHERE user_id = ?', (referrer_id,))
            row = c.fetchone()
            if row and row['username']:
                referrer_username = row['username']
            else:
                referrer_username = ""

        # إدخال المستخدم
        c.execute('''
            INSERT INTO referrals (user_id, username, full_name, referrer_id, referrer_username)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username, full_name, referrer_id, referrer_username))

        conn.commit()

        # إشعار الأدمن
        message = (
            f"📥 إحالة جديدة!\n"
            f"👤 المستخدم: {full_name} (@{username})\n"
            f"🆔 ID: {user_id}\n"
        )
        if referrer_id:
            message += f"🎯 من مندوب: @{referrer_username} (ID: {referrer_id})"
        else:
            message += f"🎯 لا يوجد مندوب"

        await context.bot.send_message(chat_id=ADMIN_ID, text=message)

    conn.close()

    await update.message.reply_text("👋 أهلاً بك في المتجر!\n✅ لو دخلت من رابط إحالة ستظهر لك رسالة تأكيد.\n📌 لو لم تدخل من رابط إحالة — اضغط الزر أدناه للدخول من رابطك الخاص.")

# أمر /get_link
async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    referral_link = f"https://t.me/{context.bot.username}?start=REP_{user_id}"
    await update.message.reply_text(f"🔗 رابط الإحالة الخاص بك:\n{referral_link}")

# أمر /my_sales
async def my_sales(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM referrals WHERE referrer_id = ?', (user_id,))
    count = c.fetchone()[0]
    conn.close()
    await update.message.reply_text(f"📊 عدد الإحالات المسجلة لديك: {count}")

# أمر /my_referrals
async def my_referrals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT username, full_name FROM referrals WHERE referrer_id = ?', (user_id,))
    rows = c.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("❌ لا يوجد لديك إحالات حتى الآن.")
    else:
        message = "📋 قائمة الإحالات:\n\n"
        for row in rows:
            username = row['username'] or "No Username"
            full_name = row['full_name']
            message += f"👤 {full_name} (@{username})\n"
        await update.message.reply_text(message)

# الدالة الرئيسية
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("get_link", get_link))
    app.add_handler(CommandHandler("my_sales", my_sales))
    app.add_handler(CommandHandler("my_referrals", my_referrals))

    print("✅ البوت يعمل الآن ...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())