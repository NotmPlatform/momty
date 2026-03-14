import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.environ("BOT_TOKEN")
GROUP_ID = int(os.environ("GROUP_ID"))

WELCOME_TEXT = """
Привет! Я бот Momty 💛

Помогаю организовать красивые свидания, детские праздники и необычные мероприятия.

Напишите, что вас интересует, и по возможности опишите запрос подробнее — так мы сможем быстрее помочь ✨
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_TEXT)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message

    username = f"@{user.username}" if user.username else "без username"

    header = (
        "📩 Новый запрос Momty\n\n"
        f"Имя в Telegram: {user.first_name or '-'}\n"
        f"Username: {username}\n"
        f"Telegram ID: {user.id}\n\n"
        "Сообщение:\n"
    )

    if message.text:
        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=header + message.text
        )

    elif message.photo:
        caption = message.caption if message.caption else "Фото без подписи"
        await context.bot.send_photo(
            chat_id=GROUP_ID,
            photo=message.photo[-1].file_id,
            caption=header + caption
        )

    elif message.video:
        caption = message.caption if message.caption else "Видео без подписи"
        await context.bot.send_video(
            chat_id=GROUP_ID,
            video=message.video.file_id,
            caption=header + caption
        )

    elif message.voice:
        await context.bot.send_voice(
            chat_id=GROUP_ID,
            voice=message.voice.file_id,
            caption=header + "Голосовое сообщение"
        )

    elif message.document:
        caption = message.caption if message.caption else f"Документ: {message.document.file_name}"
        await context.bot.send_document(
            chat_id=GROUP_ID,
            document=message.document.file_id,
            caption=header + caption
        )

    else:
        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=header + "Пользователь отправил неподдерживаемый тип сообщения."
        )

    await update.message.reply_text(
        "Спасибо! Ваш запрос отправлен команде Momty 💛\n\n"
        "Мы скоро свяжемся с вами здесь."
    )

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(
            filters.TEXT | filters.PHOTO | filters.VIDEO | filters.VOICE | filters.Document.ALL,
            handle_message
        )
    )

    print("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
