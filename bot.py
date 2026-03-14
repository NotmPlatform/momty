import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

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
    group_id = context.bot_data["group_id"]

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
            chat_id=group_id,
            text=header + message.text
        )

    elif message.photo:
        caption = message.caption if message.caption else "Фото без подписи"
        await context.bot.send_photo(
            chat_id=group_id,
            photo=message.photo[-1].file_id,
            caption=header + caption
        )

    elif message.video:
        caption = message.caption if message.caption else "Видео без подписи"
        await context.bot.send_video(
            chat_id=group_id,
            video=message.video.file_id,
            caption=header + caption
        )

    elif message.voice:
        await context.bot.send_voice(
            chat_id=group_id,
            voice=message.voice.file_id
        )
        await context.bot.send_message(
            chat_id=group_id,
            text=header + "Голосовое сообщение"
        )

    elif message.document:
        caption = message.caption if message.caption else f"Документ: {message.document.file_name}"
        await context.bot.send_document(
            chat_id=group_id,
            document=message.document.file_id,
            caption=header + caption
        )

    else:
        await context.bot.send_message(
            chat_id=group_id,
            text=header + "Пользователь отправил неподдерживаемый тип сообщения."
        )

    await update.message.reply_text(
        "Спасибо! Ваш запрос отправлен команде Momty 💛\n\n"
        "Мы скоро свяжемся с вами здесь."
    )

def main():
    bot_token = os.getenv("BOT_TOKEN")
    group_id_raw = os.getenv("GROUP_ID")

    if not bot_token:
        raise ValueError("Не найдена переменная окружения BOT_TOKEN")

    if not group_id_raw:
        raise ValueError("Не найдена переменная окружения GROUP_ID")

    try:
        group_id = int(group_id_raw)
    except ValueError:
        raise ValueError("GROUP_ID должен быть числом, например: -1001234567890")

    app = ApplicationBuilder().token(bot_token).build()
    app.bot_data["group_id"] = group_id

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
