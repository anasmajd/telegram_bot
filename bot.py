import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import logging

# 🔹 التوكن الخاص بالبوت:
BOT_TOKEN = "ضع_التوكن_هنا"

# 🔹 ID الادمن:
ADMIN_ID = 123456789  # استبدله بالـ user_id الخاص بك

# إعداد اللوج
logging.basicConfig(level=logging.INFO)

# دالة get_username_by_id
def get_username_by_id(user_id):
    conn = sqlite3.connect("referral.db")
    c = conn.cursor()

    c.execute("SELECT username FROM users WHERE user_id=?", (user_id,))
    result = c.fetchone()

    conn.close()

    return result[0] if result and result[0] else "بدون يوزرنيم"

# دالة /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username or "بدون يوزرنيم"
    full_name = user.full_name

    args = context.args
    referrer_code = args[0] if args else None

    conn = sqlite3.connect("referral.db")
    c = conn.cursor()

    # هل المستخدم مسجل؟
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user_exists = c.fetchone()

    if not user_exists:
        referred_by = referrer_code if referrer_code else None

        # سجل المستخدم
        c.execute("INSERT INTO users (user_id, username, full_name, referred_by) VALUES (?, ?, ?, ?)", 
                  (user_id, username, full_name, referred_by))
        conn.commit()

        # لو دخل من رابط إحالة
        if referred_by:
            referrer_id = int(referred_by.replace("REP_", ""))

            # أضف للإحالات
            c.execute("INSERT INTO referrals (referrer_id, referred_id, referred_username) VALUES (?, ?, ?)", 
                      (referrer_id, user_id, username))
            conn.commit()

            # أرسل للادمن
            ref_username = get_username_by_id(referrer_id)
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"""📥 إحالة جديدة!
👤 المستخدم: {full_name} (@{username})
🆔 ID: {user_id}
🎯 من مندوب: @{ref_username}
""")
        
        # رسالة ترحيب
        await update.message.reply_text(f"""👋 أهلاً بك في المتجر!
✅ لو دخلت من رابط إحالة ستظهر لك رسالة تأكيد.
🔗 يمكنك الحصول على رابط الإحالة الخاص بك باستخدام الأمر /get_link""")

    else:
        # لو مستخدم قديم → فقط رسالة عادية
        await update.message.reply_text("👋 مرحباً بك مجدداً في المتجر! يمكنك استخدام /get_link لمشاركة رابط الإحالة الخاص بك.")

    conn.close()

# دالة /get_link
async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    referral_code = f"REP_{user_id}"
    link = f"https://t.me/{context.bot.username}?start={referral_code}"
    await update.message.reply_text(f"🔗 رابط الإحالة الخاص بك:\n{link}")

# دالة /my_sales
async def my_sales(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    conn = sqlite3.connect("referral.db")
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM referrals WHERE referrer_id=?", (user_id,))
    count = c.fetchone()[0]

    conn.close()

    await update.message.reply_text(f"📊 عدد الإحالات المسجلة لديك: {count}")

# دالة /my_referrals
async def my_referrals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    conn = sqlite3.connect("referral.db")
    c = conn.cursor()

    c.execute("SELECT referred_username FROM referrals WHERE referrer_id=?", (user_id,))
    referrals = c.fetchall()

    conn.close()

    if referrals:
        text = "📋 قائمة الإحالات:\n"
        for i, row in enumerate(referrals, 1):
            username = row[0]
            text += f"{i}. @{username}\n"
    else:
        text = "❌ لا يوجد لديك إحالات حتى الآن."

    await update.message.reply_text(text)

# تشغيل البوت
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("get_link", get_link))
    app.add_handler(CommandHandler("my_sales", my_sales))
    app.add_handler(CommandHandler("my_referrals", my_referrals))

    print("✅ البوت يعمل الآن ...")
    app.run_polling()