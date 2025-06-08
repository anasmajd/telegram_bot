from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import sqlite3
import datetime

# ✅ توكن البوت الخاص بك
BOT_TOKEN = "8028540649:AAF8bp_jvM8tibUUmzUzq1DBzwJdrNvAzRo"

# حفظ الإحالة
def save_referral(user_id, rep_id, username):
    conn = sqlite3.connect("referrals.db")
    c = conn.cursor()

    c.execute("SELECT * FROM referrals WHERE user_id=?", (user_id,))
    result = c.fetchone()

    if not result:
        date_joined = datetime.datetime.now().strftime("%Y-%m-%d")
        c.execute("INSERT INTO referrals (user_id, username, rep_id, date_joined) VALUES (?, ?, ?, ?)",
                  (user_id, username, rep_id, date_joined))
        conn.commit()

    conn.close()

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "بدون اسم مستخدم"
    args = context.args

    print(f"User {user_id} sent: {update.message.text}")

    rep_id = None
    if args:
        rep_id = args[0]

    if rep_id:
        save_referral(user_id, rep_id, username)
        await update.message.reply_text(f"✅ تم تسجيلك مع المندوب: {rep_id}")
    else:
        # تحسين: زر خاص لتأكيد تسجيل الإحالة
        bot_username = "Janastoreiqbot"
        rep_id_button = f"REP_{update.message.from_user.id}"

        referral_link = f"https://t.me/{bot_username}?start={rep_id_button}"

        keyboard = [
            [InlineKeyboardButton("🔗 اضغط هنا للدخول من رابط الإحالة (خارج تيليجرام)", url=referral_link)],
            [InlineKeyboardButton("✅ تم الدخول من رابط الإحالة", callback_data=f"referral_{rep_id_button}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "👋 أهلاً بك في المتجر!\n\n"
            "✅ لو دخلت من رابط إحالة ستظهر لك رسالة تأكيد.\n"
            "لو لم تدخل من رابط إحالة — اضغط الزر أدناه للدخول من رابطك الخاص.\n"
            "🔹 بعد الضغط، يمكنك الضغط على زر ✅ لتأكيد تسجيل الإحالة.",
            reply_markup=reply_markup
        )

# /my_referrals
async def my_referrals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rep_id = f"REP_{update.message.from_user.id}"
    conn = sqlite3.connect("referrals.db")
    c = conn.cursor()

    six_months_ago = (datetime.datetime.now() - datetime.timedelta(days=180)).strftime("%Y-%m-%d")
    c.execute("DELETE FROM referrals WHERE date_joined <= ?", (six_months_ago,))
    conn.commit()

    c.execute("SELECT user_id, username, date_joined FROM referrals WHERE rep_id=?", (rep_id,))
    rows = c.fetchall()

    if rows:
        message = f"📋 قائمة الإحالات الحالية:\n"
        for row in rows:
            username_display = f"@{row[1]}" if row[1] != "بدون اسم مستخدم" else f"User ID: {row[0]}"
            message += f"- {username_display} | منذ: {row[2]}\n"
    else:
        message = "❌ لا توجد إحالات حالياً."

    await update.message.reply_text(message)
    conn.close()

# /my_sales
async def my_sales(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rep_id = f"REP_{update.message.from_user.id}"
    conn = sqlite3.connect("referrals.db")
    c = conn.cursor()

    six_months_ago = (datetime.datetime.now() - datetime.timedelta(days=180)).strftime("%Y-%m-%d")
    c.execute("DELETE FROM referrals WHERE date_joined <= ?", (six_months_ago,))
    conn.commit()

    c.execute("SELECT COUNT(*) FROM referrals WHERE rep_id=?", (rep_id,))
    count = c.fetchone()[0]

    message = f"📊 عدد الإحالات الخاصة بك: {count}"

    await update.message.reply_text(message)
    conn.close()

# /get_link
async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_username = "Janastoreiqbot"
    rep_id = f"REP_{update.message.from_user.id}"

    referral_link = f"https://t.me/{bot_username}?start={rep_id}"

    keyboard = [
        [InlineKeyboardButton("🔗 رابط الإحالة الخاص بك", url=referral_link)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = f"🔗 رابط الإحالة الخاص بك:\n{referral_link}"

    await update.message.reply_text(message, reply_markup=reply_markup)

# 🎁 Callback Query (لما يضغط ✅ تم الدخول)
async def referral_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    username = query.from_user.username or "بدون اسم مستخدم"

    # نستخرج rep_id من callback_data
    rep_id = query.data.replace("referral_", "")

    save_referral(user_id, rep_id, username)

    await query.edit_message_text("✅ تم تسجيلك مع المندوب بنجاح!")

# إعداد البوت
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("my_referrals", my_referrals))
    app.add_handler(CommandHandler("my_sales", my_sales))
    app.add_handler(CommandHandler("get_link", get_link))
    app.add_handler(CallbackQueryHandler(referral_callback, pattern=r"^referral_"))

    print("✅ البوت يعمل كنظام إحالة احترافي.")
    app.run_polling()