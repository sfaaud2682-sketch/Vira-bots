import os
from telegram.ext import Application

TOKEN = "8821925270:AAEqt1jatqhrgQH6p8LTffD1av_LGArb0os"

def main():
    print("🚀 ... يعمل الآن بكامل الصلاحيات والميزات (Vira) بوت فيرا")
    application = Application.builder().token(TOKEN).build()
    application.run_polling()

if __name__ == '__main__':
    main()
