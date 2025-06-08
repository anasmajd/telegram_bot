import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.constants import ParseMode

# ✅ توكن البوت
TOKEN = "8028540649:AAF8bp_jvM8tibUUmzUzq1DBzwJdrNvAzRo"

# ✅ رقم معرفك الشخصي كـ Admin ID (يمكنك معرفته من بوت @userinfobot)
ADMIN_ID = 920325080  # مثال — غيره إلى رقم معرفك

# إعداد اللوجات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# إنشاء قاعدة البيانات
conn = sqlite3.connect('referral.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS referrals (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        referrer_id TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS referral_sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        referrer_id TEXT,
        user_id INTEGER
    )
''')

conn.commit()
conn.close()


# دالة /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    username = update.effective_user.username
    args = context.args

    rep_id = None
    if args:
        rep_id = args[0]

    conn = sqlite3.connect('referral.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM referrals WHERE user_id = ?', (user_id,))
    existing_user = cursor.fetchone()

    if not existing_user:
        cursor.execute(
            'INSERT INTO referrals (user_id, username, referrer_id) VALUES (?, ?, ?)',
            (user_id, username, rep_id)
        )
        conn.commit()

        # إرسال إشعار للإدارة في حال الإحالة
        if rep_id and rep_id.startswith("REP_"):
            referrer_user_id = rep_id.replace("REP_", "")
            cursor.execute('SELECT username FROM referrals WHERE user_id = ?', (referrer_user_id,))
            row = cursor.fetchone()

            if row and row[0]:
                referrer_username = f"@{row[0]}"
            else:
                referrer_username = f"REP_{referrer_user_id}"

            message = f"""
📢 إحالة جديدة!
👤 المستخدم: {update.effective_user.full_name} (@{username})  
🆔 ID: {user_id}  
🎯 من مندوب: {referrer_username}
"""
            await context.bot.send_message(chat_id=ADMIN_ID, text=message, parse_mode=ParseMode.HTML)

    conn.close()

    # إرسال رسالة ترحيب مع زر دخول من رابط الإحالة
    keyboard = [
        [InlineKeyboardButton("🔗 اضغط هنا للدخول من رابط الإحالة", callback_data='confirm_referral')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 أهلاً بك في المتجر!\n✅ لو دخلت من رابط إحالة ستظهر لك رسالة تأكيد.\nلو لم تدخل من رابط إحالة — اضغط الزر أدناه للدخول من رابطك الخاص.\n\n🔷 بعد الضغط، يمكنك الضغط على زر ✅ لتأكيد تسجيل الإحالة.",
        reply_markup=reply_markup
    )


# زر الضغط على رابط الإحالة
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    username = query.from_user.username

    conn = sqlite3.connect('referral.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM referrals WHERE user_id = ?', (user_id,))
    user_data = cursor.fetchone()

    if user_data and user_data[2]:
        text = "✅ تم الدخول من رابط الإحالة ✅"
    else:
        text = "❌ لم يتم تسجيل إحالة لهذا المستخدم."

    await query.answer()
    await query.edit_message_text(text=text)

    conn.close()


# /get_link
async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    referral_link = f"https://t.me/Janastoreiqbot?start=REP_{user_id}"

    await update.message.reply_text(
        f"🔗 رابط الإحالة الخاص بك:\n{referral_link}"
    )


# /my_referrals
async def my_referrals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id

    conn = sqlite3.connect('referral.db')
    cursor = conn.cursor()

    cursor.execute('SELECT user_id, username FROM referrals WHERE referrer_id = ?', (f"REP_{user_id}",))
    referrals = cursor.fetchall()

    conn.close()

    if referrals:
        message = "📋 الإحالات الخاصة بك:\n"
        for referral in referrals:
            referral_id, referral_username = referral
            referral_username = f"@{referral_username}" if referral_username else f"ID: {referral_id}"
            message += f"👤 {referral_username} - ID: {referral_id}\n"
    else:
        message = "❌ لا يوجد لديك إحالات حتى الآن."

    await update.message.reply_text(message)


# /my_sales
async def my_sales(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id

    conn = sqlite3.connect('referral.db')
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM referral_sales WHERE referrer_id = ?', (f"REP_{user_id}",))
    sales_count = cursor.fetchone()[0]

    conn.close()

    await update.message.reply_text(f"📊 عدد الإحالات المسجلة لديك: {sales_count}")


# تشغيل البوت
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("get_link", get_link))
    app.add_handler(CommandHandler("my_referrals", my_referrals))
    app.add_handler(CommandHandler("my_sales", my_sales))

    app.add_handler(CommandHandler("help", get_link))  # فقط مثال

    app.add_handler(CommandHandler("my_link", get_link))  # يمكنك استخدام my_link أيضا

    from telegram.ext import CallbackQueryHandler
    app.add_handler(CallbackQueryHandler(button_handler))

    print("✅ Bot is running...")
    app.run_polling()