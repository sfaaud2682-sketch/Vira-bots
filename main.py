import os
from telegram.ext import Application

TOKEN = "8821925270:AAFmIgSuN3enTMynetNDJVSlPKU_KU60L58"

def main():
    print("🚀 ... يعمل الآن بكامل الصلاحيات والميزات (Vira) بوت فيرا")
    application = Application.builder().token(TOKEN).build()
    application.run_polling()

if __name__ == '__main__':
    main()
