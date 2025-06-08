import logging
import sqlite3
import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ✅ ضع التوكن الخاص بك هنا:
BOT_TOKEN = "8028540649:AAF8bp_jvM8tibUUmzUzq1DBzwJdrNvAzRo"

# إعدادات اللوق
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ✅ إنشاء قاعدة البيانات إن لم تكن موجودة
conn = sqlite3.connect('referrals.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS referrals (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        rep_id TEXT,
        date_joined TEXT
    )
''')
conn.commit()
conn.close()

# ✅ دالة /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args
    conn = sqlite3.connect('referrals.db')
    cursor = conn.cursor()

    rep_id = args[0] if args else None

    cursor.execute('SELECT * FROM referrals WHERE user_id = ?', (user.id,))
    existing_user = cursor.fetchone()

    if not existing_user:
        cursor.execute('''
            INSERT INTO referrals (user_id, username, rep_id, date_joined)
            VALUES (?, ?, ?, ?)
        ''', (
            user.id,
            user.username if user.username else "",
            rep_id if rep_id else "",
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()

        if rep_id:
            await update.message.reply_text(
                "✅ تم الدخول من رابط الإحالة ✅"
            )

    # رسالة ترحيب
    welcome_text = (
        "👋 أهلاً بك في المتجر!\n\n"
        "✅ لو دخلت من رابط إحالة ستظهر لك رسالة تأكيد.\n"
        "لو لم تدخل من رابط إحالة — اضغط الزر أدناه للدخول من رابطك الخاص.\n"
        "🔷 بعد الضغط، يمكنك الضغط على زر ✅ لتأكيد تسجيل الإحالة."
    )
    referral_link = f"https://t.me/{context.bot.username}?start=REP_{user.id}"

    await update.message.reply_text(welcome_text)
    await update.message.reply_text(
        f"🔗 [اضغط هنا للدخول من رابط الإحالة](https://t.me/{context.bot.username}?start=REP_{user.id})",
        parse_mode='Markdown'
    )

    conn.close()

# ✅ دالة /get_link
async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    referral_link = f"https://t.me/{context.bot.username}?start=REP_{user.id}"
    await update.message.reply_text(
        f"🔗 رابط الإحالة الخاص بك:\n{referral_link}"
    )

# ✅ دالة /my_referrals
async def my_referrals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    conn = sqlite3.connect('referrals.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT user_id, username, date_joined
        FROM referrals
        WHERE rep_id = ?
    ''', (f'REP_{user.id}',))
    rows = cursor.fetchall()
    conn.close()

    if rows:
        text = "📋 قائمة الإحالات:\n"
        for ref_user_id, ref_username, date_joined in rows:
            user_display = f"@{ref_username}" if ref_username else f"ID: {ref_user_id}"
            text += f"\n👤 {user_display} 📅 {date_joined}"
    else:
        text = "❌ لا يوجد لديك إحالات حتى الآن."

    await update.message.reply_text(text)

# ✅ دالة /my_sales
async def my_sales(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    conn = sqlite3.connect('referrals.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT user_id, username, date_joined
        FROM referrals
        WHERE rep_id = ?
    ''', (f'REP_{user.id}',))
    rows = cursor.fetchall()
    conn.close()

    text = f"📊 عدد الإحالات المسجلة لديك: {len(rows)}"
    if rows:
        for ref_user_id, ref_username, date_joined in rows:
            user_display = f"@{ref_username}" if ref_username else f"ID: {ref_user_id}"
            text += f"\n👤 {user_display} 📅 {date_joined}"

    await update.message.reply_text(text)

# ✅ Main
if __name__ == '__main__':
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("get_link", get_link))
    app.add_handler(CommandHandler("my_referrals", my_referrals))
    app.add_handler(CommandHandler("my_sales", my_sales))

    print("✅ Bot started...")
    app.run_polling()