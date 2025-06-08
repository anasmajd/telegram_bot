from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import sqlite3
import datetime

# ✅ هنا ضع التوكن الخاص بك
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

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    args = context.args

    if args:
        rep_id = args[0]  # كود المندوب
        save_referral(user_id, rep_id)
        await update.message.reply_text(f"✅ تم تسجيلك مع المندوب: {rep_id}")
    else:
        await update.message.reply_text("👋 أهلاً بك في المتجر!")

# /my_referrals
async def my_referrals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rep_id = f"REP_{update.message.from_user.id}"  # فرضًا مندوب id = REP_<chat_id>
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

# إعداد البوت
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("my_referrals", my_referrals))

    print("✅ البوت يعمل كنظام إحالة.")
    app.run_polling()