# -*- coding: utf-8 -*-

import sqlite3
import logging
import random
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)

TOKEN = '8028540649:AAF8bp_jvM8tibUUmzUzq1DBzwJdrNvAzRo'
ADMIN_USER_ID = 920325080

conn = sqlite3.connect('referrals.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS referrals (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        referrer_id INTEGER
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        user_id INTEGER,
        message TEXT
    )
''')
conn.commit()

COLOR_CODES = ["🔴", "🟠", "🟡", "🟢", "🔵", "🟣", "🟤", "⚫", "⚪", "🟥", "🟧", "🟨", "🟩", "🟦", "🟪", "🟫"] * 7
USER_COLORS = {}

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

    if user_id == ADMIN_USER_ID:
        keyboard = [[KeyboardButton("📋 عرض الإحالات")], [KeyboardButton("🛠️ لوحة الإدارة")]]
    else:
        keyboard = [[KeyboardButton("🔗 رابط الإحالة")], [KeyboardButton("📊 عدد الإحالات")]]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("👋 أهلاً بك في المتجر!\nاختر من القائمة أدناه:", reply_markup=reply_markup)

async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    link = f"https://t.me/Janastoreiqbot?start=REP_{user_id}"
    await update.message.reply_text(f"🔗 رابط الإحالة الخاص بك:\n{link}")

async def my_sales(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cursor.execute("SELECT COUNT(*) FROM referrals WHERE referrer_id=?", (user_id,))
    count = cursor.fetchone()[0]
    await update.message.reply_text(f"📊 عدد الإحالات المسجلة لديك: {count}")

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

async def forward_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message
    text = message.caption or message.text or "📎 محتوى غير نصي (صورة/ملف/صوت)"

    cursor.execute("INSERT INTO messages (user_id, message) VALUES (?, ?)", (user.id, text))
    conn.commit()

    if user.id not in USER_COLORS:
        USER_COLORS[user.id] = random.choice(COLOR_CODES)
    color = USER_COLORS[user.id]

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔁 الرد على المستخدم", callback_data=f"reply_{user.id}"),
            InlineKeyboardButton("🗂️ تجميع رسائل العضو", callback_data=f"history_{user.id}")
        ]
    ])

    caption = f"{color} رسالة من @{user.username or 'بدون يوزر'} ({user.full_name}):\n{text}"

    if message.photo:
        await context.bot.send_photo(chat_id=ADMIN_USER_ID, photo=message.photo[-1].file_id, caption=caption, reply_markup=keyboard)
    elif message.document:
        await context.bot.send_document(chat_id=ADMIN_USER_ID, document=message.document.file_id, caption=caption, reply_markup=keyboard)
    elif message.video:
        await context.bot.send_video(chat_id=ADMIN_USER_ID, video=message.video.file_id, caption=caption, reply_markup=keyboard)
    elif message.voice:
        await context.bot.send_voice(chat_id=ADMIN_USER_ID, voice=message.voice.file_id, caption=caption, reply_markup=keyboard)
    else:
        await context.bot.send_message(chat_id=ADMIN_USER_ID, text=caption, reply_markup=keyboard)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("reply_"):
        target_id = int(data.split("_")[1])
        context.user_data['reply_target'] = target_id
        await query.message.reply_text(f"✍️ اكتب الآن رسالتك للمستخدم (ID: {target_id})")
    elif data.startswith("history_"):
        target_id = int(data.split("_")[1])
        cursor.execute("SELECT message FROM messages WHERE user_id=?", (target_id,))
        msgs = cursor.fetchall()
        if msgs:
            combined = "\n---\n".join([m[0] for m in msgs[-20:]])
            await query.message.reply_text(f"📄 آخر رسائل المستخدم:\n{combined}")
        else:
            await query.message.reply_text("❌ لا توجد رسائل مسجلة لهذا المستخدم.")

async def reply_followup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    msg = update.message

    if user_id != ADMIN_USER_ID:
        if msg.text in ["🔗 رابط الإحالة", "📊 عدد الإحالات"]:
            await handle_buttons(update, context)
        else:
            await forward_all(update, context)
        return

    target_id = context.user_data.get("reply_target")
    if target_id:
        if msg.text:
            await context.bot.send_message(chat_id=target_id, text=msg.text)
        elif msg.photo:
            await context.bot.send_photo(chat_id=target_id, photo=msg.photo[-1].file_id, caption=msg.caption)
        elif msg.document:
            await context.bot.send_document(chat_id=target_id, document=msg.document.file_id, caption=msg.caption)
        elif msg.video:
            await context.bot.send_video(chat_id=target_id, video=msg.video.file_id, caption=msg.caption)
        elif msg.voice:
            await context.bot.send_voice(chat_id=target_id, voice=msg.voice.file_id, caption=msg.caption)
        await update.message.reply_text("✅ تم إرسال الرسالة.")
        context.user_data["reply_target"] = None
    else:
        await handle_buttons(update, context)

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🔗 رابط الإحالة":
        await get_link(update, context)
    elif text == "📊 عدد الإحالات":
        await my_sales(update, context)
    elif text == "📋 عرض الإحالات" and update.effective_user.id == ADMIN_USER_ID:
        await my_referrals(update, context)
    elif text == "🛠️ لوحة الإدارة" and update.effective_user.id == ADMIN_USER_ID:
        await update.message.reply_text("🛠️ استخدم الزر أسفل كل رسالة للرد مباشرة.")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("get_link", get_link))
    app.add_handler(CommandHandler("my_sales", my_sales))
    app.add_handler(CommandHandler("my_referrals", my_referrals))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(
        filters.ALL & ~filters.COMMAND,
        reply_followup
    ))

    print("✅ البوت يعمل الآن ...")
    app.run_polling()
