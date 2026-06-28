import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    filters, ConversationHandler, ContextTypes, CallbackQueryHandler
)

# اسم ملف حفظ التاغات
DB_FILE = "tags.json"

# قائمة أرقام المعرفات (User IDs) للمديرين المسموح لهم بإدارة البوت
BOT_ADMINS = [
    5050332902,  # @na_128a
    5831617577,  # @A_nnn2
    8253495826   # الآيدي الإضافي
]

# دالة لتحميل التاغات من الملف
def load_tags():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

# دالة لحفظ التاغات في الملف
def save_tags_to_file(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

saved_tags = load_tags()

# مراحل المحادثة لإضافة تاق
ASKING_NAME, ASKING_TAG = range(2)

# 1. بدء التسجيل في الخاص
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != 'private':
        await update.message.reply_text("يرجى البدء معي في الخاص لإضافة تاق.")
        return ConversationHandler.END
    await update.message.reply_text("مرحباً! ما هو اسم التاق الذي تود استخدامه؟")
    return ASKING_NAME

# 2. استقبال اسم التاق
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['tag_name'] = update.message.text
    await update.message.reply_text("تمام، هات التاق (الأسماء أو النص) أضيفه لك!")
    return ASKING_TAG

# 3. حفظ التاق النهائي
async def save_tag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global saved_tags
    tag_content = update.message.text
    tag_name = context.user_data['tag_name']
    
    saved_tags[tag_name] = tag_content
    save_tags_to_file(saved_tags)
    
    await update.message.reply_text(f"تم حفظ تاق '{tag_name}' بنجاح! جربه الآن في المجموعة.")
    return ConversationHandler.END

# 4. عرض التاغات مع الأزرار (أمر /my_tags)
async def my_tags(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != 'private':
        await update.message.reply_text("هذا الأمر يُستخدم في الخاص فقط.")
        return
    
    user_id = update.effective_user.id
    
    # التحقق مما إذا كان المستخدم ضمن قائمة المديرين
    if user_id not in BOT_ADMINS:
        await update.message.reply_text("عذراً، أنت لست مخولاً لإدارة البوت.")
        return
    
    if not saved_tags:
        await update.message.reply_text("لا توجد لديك أي تاغات محفوظة حالياً.")
        return
        
    keyboard = []
    for tag_name in saved_tags.keys():
        keyboard.append([InlineKeyboardButton(f"🏷️ {tag_name}", callback_data=f"tag_{tag_name}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("اختر التاق المطلوب لإدارته:", reply_markup=reply_markup)

# 5. التعامل مع الضغط على زر التاق
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in BOT_ADMINS:
        return
        
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith("tag_"):
        tag_name = data.replace("tag_", "")
        context.user_data['managing_tag'] = tag_name
        
        keyboard = [
            [
                InlineKeyboardButton("✏️ تعديل محتوى التاق", callback_data=f"edit_{tag_name}"),
                InlineKeyboardButton("🗑️ حذف التاق", callback_data=f"delete_{tag_name}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=f"إدارة التاق: **{tag_name}**", reply_markup=reply_markup, parse_mode="Markdown")

# 6. التعديل والحذف
async def callback_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global saved_tags
    user_id = update.effective_user.id
    if user_id not in BOT_ADMINS:
        return

    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("delete_"):
        tag_name = data.replace("delete_", "")
        if tag_name in saved_tags:
            del saved_tags[tag_name]
            save_tags_to_file(saved_tags)
            await query.edit_message_text(text=f"🗑️ تم حذف التاق '{tag_name}' بنجاح.")
        else:
            await query.edit_message_text(text="حدث خطأ، التاق غير موجود.")
            
    elif data.startswith("edit_"):
        tag_name = data.replace("edit_", "")
        await query.edit_message_text(text=f"✏️ أنت الآن تقوم بتعديل محتوى التاق: '{tag_name}'.\nأرسل المحتوى الجديد للتاق الآن في رسالة واحدة:")
        context.user_data['is_editing'] = True

# 7. التحديث التلقائي أو الرد بالمجموعات
async def message_dispatcher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global saved_tags
    
    if context.user_data.get('is_editing'):
        user_id = update.effective_user.id
        if user_id not in BOT_ADMINS:
            return
            
        tag_name = context.user_data.get('managing_tag')
        new_content = update.message.text
        
        saved_tags[tag_name] = new_content
        save_tags_to_file(saved_tags)
        
        await update.message.reply_text(f"✅ تم تحديث محتوى التاق '{tag_name}' بنجاح!")
        context.user_data['is_editing'] = False
        return

    if update.message and update.message.text:
        text = update.message.text.strip()
        if text in saved_tags:
            await update.message.reply_text(saved_tags[text])

if __name__ == '__main__':
    # تم ربط التوكن الخاص بك هنا
    TOKEN = "8821925270:AAFmIgSuN3enTMynetNDJVSlPKU_KU60L58"
    
    application = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ASKING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            ASKING_TAG: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_tag)],
        },
        fallbacks=[],
        allow_reentry=True
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('my_tags', my_tags))
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^tag_"))
    application.add_handler(CallbackQueryHandler(callback_actions, pattern="^(delete_|edit_)"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_dispatcher))

    print("🚀 بوت فيرا (Vira) يعمل الآن بكامل الصلاحيات والميزات...")
    application.run_polling()
