# -*- coding: utf-8 -*-

import os
import psycopg2
from psycopg2 import sql
import logging
import random
from dotenv import load_dotenv
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ConversationHandler,
)

# تحميل متغيرات البيئة
load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID'))
DATABASE_URL = os.getenv('DATABASE_URL')

# حالات المحادثة
WAITING_CATEGORY_NAME, WAITING_CATEGORY_DESC = range(2)

# الألوان للمستخدمين
COLOR_CODES = ["🔴", "🟠", "🟡", "🟢", "🔵", "🟣", "🟤", "⚫", "⚪", "🟥", "🟧", "🟨", "🟩", "🟦", "🟪", "🟫"] * 7
USER_COLORS = {}

def get_db_connection():
    """إنشاء اتصال بقاعدة البيانات"""
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def init_database():
    """إنشاء الجداول المطلوبة"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # جدول الأقسام
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    category_id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # جدول الإحالات
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS referrals (
                    user_id BIGINT PRIMARY KEY,
                    username VARCHAR(100),
                    referrer_id BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # جدول الرسائل
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    message_id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        
        conn.commit()
        print("✅ تم إنشاء الجداول بنجاح")
    except Exception as e:
        print(f"❌ خطأ في إنشاء الجداول: {e}")
    finally:
        conn.close()

async def get_categories():
    """جلب جميع الأقسام من قاعدة البيانات"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT category_id, name FROM categories ORDER BY name")
            return cursor.fetchall()
    except Exception as e:
        logging.error(f"خطأ في جلب الأقسام: {e}")
        return []
    finally:
        conn.close()

async def create_main_keyboard(user_id):
    """إنشاء لوحة المفاتيح الرئيسية"""
    categories = await get_categories()
    keyboard = []
    
    # إضافة أزرار الأقسام
    for category_id, name in categories:
        keyboard.append([KeyboardButton(f"📁 {name}")])
    
    # الأزرار الأساسية
    if user_id == ADMIN_USER_ID:
        keyboard.extend([
            [KeyboardButton("🔗 رابط الإحالة"), KeyboardButton("📊 عدد الإحالات")],
            [KeyboardButton("📋 عرض الإحالات"), KeyboardButton("🛠️ لوحة الإدارة")],
            [KeyboardButton("➕ إضافة قسم"), KeyboardButton("🗑️ حذف قسم")]
        ])
    else:
        keyboard.extend([
            [KeyboardButton("🔗 رابط الإحالة"), KeyboardButton("📊 عدد الإحالات")]
        ])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

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

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM referrals WHERE user_id=%s", (user_id,))
            result = cursor.fetchone()

            if not result:
                cursor.execute(
                    "INSERT INTO referrals (user_id, username, referrer_id) VALUES (%s, %s, %s)",
                    (user_id, username, referrer_user_id)
                )
                conn.commit()

                if referrer_user_id:
                    cursor.execute("SELECT username FROM referrals WHERE user_id=%s", (referrer_user_id,))
                    ref_data = cursor.fetchone()
                    ref_username = ref_data[0] if ref_data and ref_data[0] else f"{referrer_user_id}"

                    msg = f"""
📥 إحالة جديدة!
👤 المستخدم: {update.effective_user.full_name} (@{username})
🆔 ID: {user_id}
🎯 من مندوب: @{ref_username}
"""
                    await context.bot.send_message(chat_id=ADMIN_USER_ID, text=msg)
    except Exception as e:
        logging.error(f"خطأ في حفظ المستخدم: {e}")
    finally:
        conn.close()

    reply_markup = await create_main_keyboard(user_id)
    await update.message.reply_text("👋 أهلاً بك في المتجر!\nاختر من القائمة أدناه:", reply_markup=reply_markup)

async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    link = f"https://t.me/Janastoreiqbot?start=REP_{user_id}"
    await update.message.reply_text(f"🔗 رابط الإحالة الخاص بك:\n{link}")

async def my_sales(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM referrals WHERE referrer_id=%s", (user_id,))
            count = cursor.fetchone()[0]
            await update.message.reply_text(f"📊 عدد الإحالات المسجلة لديك: {count}")
    except Exception as e:
        logging.error(f"خطأ في جلب الإحالات: {e}")
        await update.message.reply_text("❌ حدث خطأ في جلب البيانات")
    finally:
        conn.close()

async def my_referrals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        return
    
    user_id = update.effective_user.id
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT user_id, username FROM referrals WHERE referrer_id=%s", (user_id,))
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
    except Exception as e:
        logging.error(f"خطأ في جلب الإحالات: {e}")
        await update.message.reply_text("❌ حدث خطأ في جلب البيانات")
    finally:
        conn.close()

# إدارة الأقسام
async def add_category_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("❌ غير مصرح لك بهذه العملية")
        return ConversationHandler.END
    
    await update.message.reply_text(
        "📝 أدخل اسم القسم الجديد:",
        reply_markup=ReplyKeyboardMarkup([["❌ إلغاء"]], resize_keyboard=True)
    )
    return WAITING_CATEGORY_NAME

async def add_category_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ إلغاء":
        reply_markup = await create_main_keyboard(update.effective_user.id)
        await update.message.reply_text("❌ تم إلغاء إضافة القسم", reply_markup=reply_markup)
        return ConversationHandler.END
    
    context.user_data['category_name'] = update.message.text
    await update.message.reply_text("📝 أدخل وصف القسم (اختياري):")
    return WAITING_CATEGORY_DESC

async def add_category_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ إلغاء":
        reply_markup = await create_main_keyboard(update.effective_user.id)
        await update.message.reply_text("❌ تم إلغاء إضافة القسم", reply_markup=reply_markup)
        return ConversationHandler.END
    
    name = context.user_data['category_name']
    description = update.message.text if update.message.text != "تخطي" else ""
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO categories (name, description) VALUES (%s, %s)",
                (name, description)
            )
            conn.commit()
            
        reply_markup = await create_main_keyboard(update.effective_user.id)
        await update.message.reply_text(
            f"✅ تم إضافة القسم '{name}' بنجاح!",
            reply_markup=reply_markup
        )
    except Exception as e:
        logging.error(f"خطأ في إضافة القسم: {e}")
        await update.message.reply_text("❌ حدث خطأ في إضافة القسم")
    finally:
        conn.close()
    
    return ConversationHandler.END

async def delete_category_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("❌ غير مصرح لك بهذه العملية")
        return
    
    categories = await get_categories()
    if not categories:
        await update.message.reply_text("❌ لا توجد أقسام لحذفها")
        return
    
    keyboard = []
    for category_id, name in categories:
        keyboard.append([InlineKeyboardButton(f"🗑️ {name}", callback_data=f"delete_cat_{category_id}")])
    keyboard.append([InlineKeyboardButton("❌ إلغاء", callback_data="cancel_delete")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🗑️ اختر القسم المراد حذفه:", reply_markup=reply_markup)

async def delete_category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel_delete":
        await query.edit_message_text("❌ تم إلغاء الحذف")
        return
    
    if query.data.startswith("delete_cat_"):
        category_id = int(query.data.split("_")[2])
        
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # جلب اسم القسم قبل الحذف
                cursor.execute("SELECT name FROM categories WHERE category_id=%s", (category_id,))
                result = cursor.fetchone()
                
                if result:
                    category_name = result[0]
                    cursor.execute("DELETE FROM categories WHERE category_id=%s", (category_id,))
                    conn.commit()
                    
                    await query.edit_message_text(f"✅ تم حذف القسم '{category_name}' بنجاح!")
                    
                    # تحديث لوحة المفاتيح
                    reply_markup = await create_main_keyboard(ADMIN_USER_ID)
                    await context.bot.send_message(
                        chat_id=ADMIN_USER_ID,
                        text="🔄 تم تحديث القائمة",
                        reply_markup=reply_markup
                    )
                else:
                    await query.edit_message_text("❌ القسم غير موجود")
        except Exception as e:
            logging.error(f"خطأ في حذف القسم: {e}")
            await query.edit_message_text("❌ حدث خطأ في حذف القسم")
        finally:
            conn.close()

async def forward_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message
    text = message.caption or message.text or "📎 محتوى غير نصي (صورة/ملف/صوت)"

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO messages (user_id, message) VALUES (%s, %s)", (user.id, text))
            conn.commit()
    except Exception as e:
        logging.error(f"خطأ في حفظ الرسالة: {e}")
    finally:
        conn.close()

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

    try:
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
    except Exception as e:
        logging.error(f"خطأ في إرسال الرسالة للأدمن: {e}")

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
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT message FROM messages WHERE user_id=%s ORDER BY created_at DESC LIMIT 20", (target_id,))
                msgs = cursor.fetchall()
                if msgs:
                    combined = "\n---\n".join([m[0] for m in msgs[::-1]])  # عكس الترتيب لإظهار الأحدث أولاً
                    await query.message.reply_text(f"📄 آخر رسائل المستخدم:\n{combined}")
                else:
                    await query.message.reply_text("❌ لا توجد رسائل مسجلة لهذا المستخدم.")
        except Exception as e:
            logging.error(f"خطأ في جلب رسائل المستخدم: {e}")
            await query.message.reply_text("❌ حدث خطأ في جلب الرسائل")
        finally:
            conn.close()
    elif data.startswith("delete_cat_") or data == "cancel_delete":
        await delete_category_callback(update, context)

async def reply_followup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    msg = update.message

    if user_id != ADMIN_USER_ID:
        await handle_buttons(update, context)
        return

    target_id = context.user_data.get("reply_target")
    if target_id:
        try:
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
        except Exception as e:
            logging.error(f"خطأ في إرسال الرد: {e}")
            await update.message.reply_text("❌ حدث خطأ في إرسال الرسالة")
    else:
        await handle_buttons(update, context)

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    
    if text == "🔗 رابط الإحالة":
        await get_link(update, context)
    elif text == "📊 عدد الإحالات":
        await my_sales(update, context)
    elif text == "📋 عرض الإحالات" and user_id == ADMIN_USER_ID:
        await my_referrals(update, context)
    elif text == "🛠️ لوحة الإدارة" and user_id == ADMIN_USER_ID:
        await update.message.reply_text("🛠️ استخدم الزر أسفل كل رسالة للرد مباشرة.")
    elif text == "➕ إضافة قسم" and user_id == ADMIN_USER_ID:
        await add_category_start(update, context)
    elif text == "🗑️ حذف قسم" and user_id == ADMIN_USER_ID:
        await delete_category_start(update, context)
    elif text.startswith("📁 "):
        # التعامل مع اختيار قسم
        category_name = text[2:]  # إزالة الرمز التعبيري
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT description FROM categories WHERE name=%s", (category_name,))
                result = cursor.fetchone()
                if result:
                    description = result[0] if result[0] else "لا يوجد وصف"
                    await update.message.reply_text(f"📁 {category_name}\n\n📝 {description}")
                else:
                    await update.message.reply_text("❌ القسم غير موجود")
        except Exception as e:
            logging.error(f"خطأ في جلب معلومات القسم: {e}")
            await update.message.reply_text("❌ حدث خطأ في جلب معلومات القسم")
        finally:
            conn.close()
    else:
        # إرسال الرسالة للأدمن إذا لم تكن من الأزرار المعروفة
        if user_id != ADMIN_USER_ID:
            await forward_all(update, context)

async def cancel_add_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = await create_main_keyboard(update.effective_user.id)
    await update.message.reply_text("❌ تم إلغاء إضافة القسم", reply_markup=reply_markup)
    return ConversationHandler.END

if __name__ == '__main__':
    # التحقق من متغيرات البيئة
    if not TOKEN or not ADMIN_USER_ID or not DATABASE_URL:
        print("❌ يجب تعيين متغيرات البيئة: BOT_TOKEN, ADMIN_USER_ID, DATABASE_URL")
        exit(1)
    
    # إنشاء قاعدة البيانات
    init_database()
    
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).build()

    # معالج المحادثة لإضافة الأقسام
    add_category_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^➕ إضافة قسم$"), add_category_start)],
        states={
            WAITING_CATEGORY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_category_name)],
            WAITING_CATEGORY_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_category_desc)],
        },
        fallbacks=[MessageHandler(filters.Regex("^❌ إلغاء$"), cancel_add_category)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("get_link", get_link))
    app.add_handler(CommandHandler("my_sales", my_sales))
    app.add_handler(CommandHandler("my_referrals", my_referrals))
    app.add_handler(add_category_conv)
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(
        filters.ALL & ~filters.COMMAND,
        reply_followup
    ))

    print("✅ البوت يعمل الآن ...")
    app.run_polling()