import logging
import sqlite3
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# ✅ توكن البوت:
BOT_TOKEN = '8028540649:AAF8bp_jvM8tibUUmzUzq1DBzwJdrNvAzRo'

# ✅ ضع هنا ID الخاص بك (صاحب البوت) لكي تستقبل Log عند تسجيل إحالة جديدة:
ADMIN_ID = 920325080  # <-- هذا هو ID حسب الرابط الذي ظهر عندك

# إعداد قاعدة البيانات
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

# إعداد اللوجات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    args = context.args
    rep_id = args[0] if args else None

    # تحقق هل المستخدم مسجل مسبقاً
    cursor.execute('SELECT * FROM referrals WHERE user_id = ?', (user.id,))
    result = cursor.fetchone()

    if not result and rep_id:
        # سجل الإحالة
        cursor.execute('''
            INSERT INTO referrals (user_id, username, rep_id, date_joined)
            VALUES (?, ?, ?, ?)
        ''', (user.id, user.username or '', rep_id, datetime.date.today().isoformat()))
        conn.commit()

        await context.bot.send_message(chat_id=user.id, text='✅ تم تسجيل دخولك من رابط إحالة بنجاح!')

        # أرسل Log إلى الـ ADMIN
        await context.bot.send_message(chat_id=ADMIN_ID,
                                       text=f'📥 إحالة جديدة!\n👤 المستخدم: {user.full_name} (@{user.username})\n🆔 ID: {user.id}\n🎯 من مندوب: {rep_id}')

    # عرض الرسالة الافتراضية مع الأزرار
    keyboard = [
        [InlineKeyboardButton("🔗 اضغط هنا للدخول من رابط الإحالة (خارج تيليجرام)", url=f'https://t.me/{context.bot.username}?start=REP_{user.id}')],
        [InlineKeyboardButton("✅ تم الدخول من رابط الإحالة", callback_data='confirm_referral')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(chat_id=user.id,
                                   text='👋 أهلاً بك في المتجر!\n\n✅ لو دخلت من رابط إحالة ستظهر لك رسالة تأكيد.\nلو لم تدخل من رابط إحالة — اضغط الزر أدناه للدخول من رابطك الخاص.\n\n🔷 بعد الضغط، يمكنك الضغط على زر ✅ لتأكيد تسجيل الإحالة.',
                                   reply_markup=reply_markup)

# زر ✅ تم الدخول
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user

    await query.answer()

    # تحقق هل المستخدم مسجل
    cursor.execute('SELECT * FROM referrals WHERE user_id = ?', (user.id,))
    result = cursor.fetchone()

    if not result:
        # سجل الإحالة يدوياً من الزر ✅
        cursor.execute('''
            INSERT INTO referrals (user_id, username, rep_id, date_joined)
            VALUES (?, ?, ?, ?)
        ''', (user.id, user.username or '', 'manual_entry', datetime.date.today().isoformat()))
        conn.commit()

        await query.edit_message_text('✅ تم تسجيل دخولك بنجاح عبر زر الإحالة!')

        # أرسل Log إلى ADMIN
        await context.bot.send_message(chat_id=ADMIN_ID,
                                       text=f'📥 إحالة جديدة (من الزر ✅)!\n👤 المستخدم: {user.full_name} (@{user.username})\n🆔 ID: {user.id}\n🎯 مصدر: manual_entry')

    else:
        await query.edit_message_text('✅ أنت مسجل بالفعل! شكراً.')

# /get_link
async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    referral_link = f"https://t.me/{context.bot.username}?start=REP_{user.id}"

    await context.bot.send_message(chat_id=user.id,
                                   text=f'🔗 رابط الإحالة الخاص بك:\n{referral_link}')

# /my_sales
async def my_sales(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    rep_id = f'REP_{user.id}'

    cursor.execute('SELECT COUNT(*) FROM referrals WHERE rep_id = ?', (rep_id,))
    count = cursor.fetchone()[0]

    await context.bot.send_message(chat_id=user.id,
                                   text=f'📊 عدد الإحالات المسجلة لديك: {count}')

# /my_referrals
async def my_referrals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    rep_id = f'REP_{user.id}'

    cursor.execute('SELECT username, date_joined FROM referrals WHERE rep_id = ?', (rep_id,))
    rows = cursor.fetchall()

    if not rows:
        await context.bot.send_message(chat_id=user.id,
                                       text='❌ لا يوجد لديك إحالات حتى الآن.')
    else:
        message = '📋 قائمة الإحالات:\n\n'
        for i, (username, date_joined) in enumerate(rows, start=1):
            username_display = f'@{username}' if username else 'بدون اسم مستخدم'
            message += f'{i}. {username_display} — {date_joined}\n'

        await context.bot.send_message(chat_id=user.id, text=message)

# MAIN
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler('get_link', get_link))
    app.add_handler(CommandHandler('my_sales', my_sales))
    app.add_handler(CommandHandler('my_referrals', my_referrals))

    print("🤖 Bot is running...")
    app.run_polling()