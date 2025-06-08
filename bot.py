import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import logging

# ✅ التوكن (حقيقي) انسخه من BotFather
TOKEN = '6703502189:AAHZ4F6UsPKNOpZMAuEKqC4S-5cvR9EpF0c'

# ✅ Admin User ID (رقمك انت بالتيليجرام)
ADMIN_USER_ID = 920325080

# ✅ إعداد قاعدة البيانات
conn = sqlite3.connect('referrals.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS referrals (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        referrer_id INTEGER
    )
''')
conn.commit()

# ✅ دالة start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or ""
    args = context.args
    referrer_user_id = None

    if args and args[0].startswith("REP_"):
        try:
            referrer_user_id = int(args[0][4:])
        except:
            referrer_user_id = None

    # ✅ تحقق هل المستخدم موجود
    cursor.execute("SELECT * FROM referrals WHERE user_id=?", (user_id,))
    result = cursor.fetchone()

    if not result:
        # ✅ سجّل المستخدم
        cursor.execute("INSERT INTO referrals (user_id, username, referrer_id) VALUES (?, ?, ?)",
                       (user_id, username, referrer_user_id))
        conn.commit()

        # ✅ ارسل اشعار للادمن
        if referrer_user_id:
            ref_cursor = conn.cursor()
            ref_cursor.execute("SELECT username FROM referrals WHERE user_id=?", (referrer_user_id,))
            ref_data = ref_cursor.fetchone()
            ref_username = ref_data[0] if ref_data and ref_data[0] else f"{referrer_user_id}"

            msg = f"""
📥 إحالة جديدة!
👤 المستخدم: {update.effective_user.full_name} (@{username})
🆔 ID: {user_id}
🎯 من مندوب: @{ref_username}
"""
            await context.bot.send_message(chat_id=ADMIN_USER_ID, text=msg)

    # ✅ رسالة الترحيب
    await update.message.reply_text(
        "👋 أهلاً بك في المتجر!\n✅ لو دخلت من رابط إحالة ستظهر لك رسالة تأكيد.\nلو لم تدخل من رابط إحالة — اضغط الزر أدناه للدخول من رابطك الخاص.\n\n🔵 بعد الضغط، يمكنك الضغط على زر ✅ لتأكيد تسجيل الإحالة.",
    )

# ✅ get_link
async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    link = f"https://t.me/Janastoreiqbot?start=REP_{user_id}"
    await update.message.reply_text(f"🔗 رابط الإحالة الخاص بك:\n{link}")

# ✅ my_referrals
async def my_referrals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cursor.execute("SELECT user_id, username FROM referrals WHERE referrer_id=?", (user_id,))
    referrals = cursor.fetchall()

    if not referrals:
        await update.message.reply_text("❌ لا يوجد لديك إحالات حتى الآن.")
        return

    msg = "📋 قائمة الإحالات:\n"
    for r in referrals:
        user_id_r = r[0]
        username_r = r[1]
        username_r = f"@{username_r}" if username_r else f"ID: {user_id_r}"
        msg += f"- {username_r}\n"

    await update.message.reply_text(msg)

# ✅ my_sales
async def my_sales(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cursor.execute("SELECT COUNT(*) FROM referrals WHERE referrer_id=?", (user_id,))
    count = cursor.fetchone()[0]
    await update.message.reply_text(f"📊 عدد الإحالات المسجلة لديك: {count}")

# ✅ Main app
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("get_link", get_link))
    app.add_handler(CommandHandler("my_referrals", my_referrals))
    app.add_handler(CommandHandler("my_sales", my_sales))

    print("✅ البوت يعمل الآن ...")
    app.run_polling()