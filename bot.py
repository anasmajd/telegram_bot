from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import sqlite3
import datetime

# ✅ هنا توكن البوت الخاص بك
BOT_TOKEN = "8028540649:AAF8bp_jvM8tibUUmzUzq1DBzwJdrNvAzRo"

# تسجيل إحالة جديدة
def save_referral(user_id, rep_id):
    conn = sqlite3.connect("referrals.db")
    c = conn.cursor()

    # هل المستخدم مسجّل سابقًا؟
    c.execute("SELECT * FROM referrals WHERE user_id=?", (user_id,))
    result = c.fetchone()

    if not result:
        # تسجيل جديد
        date_joined = datetime.datetime.now().strftime("%Y-%m-%d")
        c.execute("INSERT INTO referrals (user_id, rep_id, date_joined) VALUES (?, ?, ?)",
                  (user_id, rep_id, date_joined))
        conn.commit()

    conn.close()

# /start — تسجيل إحالة أو ترحيب عادي
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    args = context.args

    # هل هناك كود إحالة؟
    rep_id = None
    if args:
        rep_id = args[0]

    # نحاول تسجيل الإحالة دائمًا لو فيه rep_id
    if rep_id:
        save_referral(user_id, rep_id)
        await update.message.reply_text(f"✅ تم تسجيلك مع المندوب: {rep_id}")
    else:
        await update.message.reply_text("👋 أهلاً بك في المتجر!")

# /my_referrals — عرض قائمة الإحالات
async def my_referrals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rep_id = f"REP_{update.message.from_user.id}"  # مندوب id = REP_<chat_id>
    conn = sqlite3.connect("referrals.db")
    c = conn.cursor()

    # حذف الإحالات القديمة (أكثر من 6 أشهر)
    six_months_ago = (datetime.datetime.now() - datetime.timedelta(days=180)).strftime("%Y-%m-%d")
    c.execute("DELETE FROM referrals WHERE date_joined <= ?", (six_months_ago,))
    conn.commit()

    # جلب الإحالات الحالية
    c.execute("SELECT user_id, date_joined FROM referrals WHERE rep_id=?", (rep_id,))
    rows = c.fetchall()

    if rows:
        message = f"📋 قائمة الإحالات الحالية:\n"
        for row in rows:
            message += f"- User ID: {row[0]} | منذ: {row[1]}\n"
    else:
        message = "❌ لا توجد إحالات حالياً."

    await update.message.reply_text(message)
    conn.close()

# /my_sales — عرض عدد الإحالات
async def my_sales(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rep_id = f"REP_{update.message.from_user.id}"  # مندوب id = REP_<chat_id>
    conn = sqlite3.connect("referrals.db")
    c = conn.cursor()

    # حذف الإحالات القديمة (أكثر من 6 أشهر)
    six_months_ago = (datetime.datetime.now() - datetime.timedelta(days=180)).strftime("%Y-%m-%d")
    c.execute("DELETE FROM referrals WHERE date_joined <= ?", (six_months_ago,))
    conn.commit()

    # حساب عدد الإحالات الحالية
    c.execute("SELECT COUNT(*) FROM referrals WHERE rep_id=?", (rep_id,))
    count = c.fetchone()[0]

    message = f"📊 عدد الإحالات الخاصة بك: {count}"

    await update.message.reply_text(message)
    conn.close()

# /get_link — توليد رابط إحالة
async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_username = "Janastoreiqbot"  # ✅ اكتب هنا اسم البوت بدون @
    rep_id = f"REP_{update.message.from_user.id}"

    referral_link = f"https://t.me/{bot_username}?start={rep_id}"

    message = f"🔗 رابط الإحالة الخاص بك:\n{referral_link}"

    await update.message.reply_text(message)

# إعداد البوت
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("my_referrals", my_referrals))
    app.add_handler(CommandHandler("my_sales", my_sales))
    app.add_handler(CommandHandler("get_link", get_link))

    print("✅ البوت يعمل كنظام إحالة احترافي.")
    app.run_polling()