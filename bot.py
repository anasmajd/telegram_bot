import sqlite3
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# ✅ التوكن (من BotFather)
TOKEN = '8028540649:AAF8bp_jvM8tibUUmzUzq1DBzwJdrNvAzRo'

# ✅ معرف الإدمن
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

# ✅ أمر /start
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

    cursor.execute("SELECT * FROM referrals WHERE user_id=?", (user_id,))
    result = cursor.fetchone()

    if not result:
        cursor.execute("INSERT INTO referrals (user_id, username, referrer_id) VALUES (?, ?, ?)",
                       (user_id, username, referrer_user_id))
        conn.commit()

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

    # ✅ إعداد لوحة الأزرار حسب الدور
    if user_id == ADMIN_USER_ID:
        keyboard = [
            [KeyboardButton("📋 عرض الإحالات")],
            [KeyboardButton("🛠️ لوحة الإدارة")],
        ]
    else:
        keyboard = [
            [KeyboardButton("🔗 رابط الإحالة")],
            [KeyboardButton("📊 عدد الإحالات")],
            [KeyboardButton("📩 تواصل مع الإدارة")],
        ]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "👋 أهلاً بك في المتجر!\nاختر من القائمة أدناه:",
        reply_markup=reply_markup
    )

# ✅ رابط الإحالة
async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    link = f"https://t.me/Janastoreiqbot?start=REP_{user_id}"
    await update.message.reply_text(f"🔗 رابط الإحالة الخاص بك:\n{link}")

# ✅ عدد الإحالات
async def my_sales(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cursor.execute("SELECT COUNT(*) FROM referrals WHERE referrer_id=?", (user_id,))
    count = cursor.fetchone()[0]
    await update.message.reply_text(f"📊 عدد الإحالات المسجلة لديك: {count}")

# ✅ عرض الإحالات
async def my_referrals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cursor.execute("SELECT user_id, username FROM referrals WHERE referrer_id=?", (user_id,))
    referrals = cursor.fetchall()

    if not referrals:
        await update.message.reply_text("❌ لا يوجد لديك إحالات حتى الآن.")
        return

    msg = "📋 قائمة الإحالات:\n"
    for r in referrals:
        uid = r[0]
        uname = r[1]
        uname = f"@{uname}" if uname else f"ID: {uid}"
        msg += f"- {uname}\n"

    await update.message.reply_text(msg)

# ✅ تواصل مع الإدارة
async def contact_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    await context.bot.send_message(chat_id=ADMIN_USER_ID,
        text=f"رسالة من @{update.effective_user.username or 'بدون يوزر'}:\n{message}")
    await update.message.reply_text("✅ تم إرسال رسالتك إلى الإدارة.")

# ✅ رد الإدمن على المستخدم
async def reply_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text("❗️ استخدم الصيغة: /reply <user_id> <الرسالة>")
        return

    target_id = int(args[0])
    message = " ".join(args[1:])
    await context.bot.send_message(chat_id=target_id, text=message)
    await update.message.reply_text("✅ تم إرسال الرسالة.")

# ✅ تعامل مع الأزرار
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🔗 رابط الإحالة":
        await get_link(update, context)
    elif text == "📊 عدد الإحالات":
        await my_sales(update, context)
    elif text == "📩 تواصل مع الإدارة":
        await update.message.reply_text("✍️ اكتب رسالتك الآن وسيتم إرسالها للإدارة.")
        context.user_data["awaiting_contact"] = True
    elif text == "📋 عرض الإحالات" and update.effective_user.id == ADMIN_USER_ID:
        await my_referrals(update, context)
    elif text == "🛠️ لوحة الإدارة" and update.effective_user.id == ADMIN_USER_ID:
        await update.message.reply_text("🛠️ استخدم الأمر /reply <id> <رسالة> للرد.")
    elif context.user_data.get("awaiting_contact"):
        context.user_data["awaiting_contact"] = False
        await contact_admin(update, context)

# ✅ تشغيل البوت
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("get_link", get_link))
    app.add_handler(CommandHandler("my_sales", my_sales))
    app.add_handler(CommandHandler("my_referrals", my_referrals))
    app.add_handler(CommandHandler("reply", reply_user))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))

    print("✅ البوت يعمل الآن ...")
    app.run_polling()
