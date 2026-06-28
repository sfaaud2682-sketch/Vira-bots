import json
import os
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    filters, ConversationHandler, ContextTypes, CallbackQueryHandler
)

# إعداد السجلات
logging.basicConfig(level=logging.INFO)

# اسم ملف حفظ التاغات
DB_FILE = "tags.json"
BOT_ADMINS = [5050332902, 5831617577, 8253495826]

# --- نظام الخادم الوهمي لـ Render ---
class SimpleServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Vira Bot is running!")

def run_server():
    port = int(os.getenv("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleServer)
    server.serve_forever()

# --- دوال التاغات ---
def load_tags():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_tags_to_file(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

saved_tags = load_tags()
ASKING_NAME, ASKING_TAG = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != 'private':
        await update.message.reply_text("يرجى البدء معي في الخاص لإضافة تاق.")
        return ConversationHandler.END
    await update.message.reply_text("مرحباً! ما هو اسم التاق الذي تود استخدامه؟")
    return ASKING_NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['tag_name'] = update.message.text
    await update.message.reply_text("تمام، هات التاق (الأسماء أو النص) أضيفه لك!")
    return ASKING_TAG

async def save_tag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global saved_tags
    tag_name = context.user_data['tag_name']
    saved_tags[tag_name] = update.message.text
    save_tags_to_file(saved_tags)
    await update.message.reply_text(f"تم حفظ تاق '{tag_name}' بنجاح!")
    return ConversationHandler.END

async def my_tags(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != 'private' or update.effective_user.id not in BOT_ADMINS: 
        return
    if not saved_tags:
        await update.message.reply_text("لا توجد تاغات.")
        return
    keyboard = [[InlineKeyboardButton(f"🏷️ {k}", callback_data=f"tag_{k}")] for k in saved_tags.keys()]
    await update.message.reply_text("إدارة التاغات:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("tag_"):
        tag_name = query.data.replace("tag_", "")
        context.user_data['managing_tag'] = tag_name
        kb = [[InlineKeyboardButton("✏️ تعديل", callback_data=f"edit_{tag_name}"), InlineKeyboardButton("🗑️ حذف", callback_data=f"delete_{tag_name}")]]
        await query.edit_message_text(f"إدارة التاق: {tag_name}", reply_markup=InlineKeyboardMarkup(kb))

async def callback_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global saved_tags
    query = update.callback_query
    data = query.data
    if data.startswith("delete_"):
        tag_name = data.replace("delete_", "")
        if tag_name in saved_tags:
            del saved_tags[tag_name]
            save_tags_to_file(saved_tags)
            await query.edit_message_text(f"🗑️ تم حذف '{tag_name}'.")
    elif data.startswith("edit_"):
        context.user_data['is_editing'] = True
        await query.edit_message_text(f"أرسل المحتوى الجديد للتاق '{data.replace('edit_', '')}':")

async def message_dispatcher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global saved_tags
    if context.user_data.get('is_editing'):
        tag_name = context.user_data.get('managing_tag')
        saved_tags[tag_name] = update.message.text
        save_tags_to_file(saved_tags)
        context.user_data['is_editing'] = False
        await update.message.reply_text("✅ تم التحديث!")
    elif update.message and update.message.text in saved_tags:
        await update.message.reply_text(saved_tags[update.message.text])

if __name__ == '__main__':
    # سحب التوكن من المتغيرات وتأكد من إزالة أي مسافات أو رموز بالخطأ
    TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
    
    if not TOKEN:
        print("❌ خطأ: التوكن غير موجود في إعدادات Render!")
    else:
        # تشغيل خادم الويب في الخلفية لضمان عمل الخدمة
        threading.Thread(target=run_server, daemon=True).start()
        
        application = ApplicationBuilder().token(TOKEN).build()
        
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)], 
            states={
                ASKING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)], 
                ASKING_TAG: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_tag)]
            }, 
            fallbacks=[], 
            allow_reentry=True
        )
        
        application.add_handler(conv_handler)
        application.add_handler(CommandHandler('my_tags', my_tags))
        application.add_handler(CallbackQueryHandler(button_handler, pattern="^tag_"))
        application.add_handler(CallbackQueryHandler(callback_actions, pattern="^(delete_|edit_)"))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_dispatcher))
        
        print("🚀 بوت فيرا (Vira) يعمل الآن...")
        application.run_polling()
