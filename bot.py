import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# ===== Переменные окружения =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID_RAW = os.getenv("GROUP_ID")

if not BOT_TOKEN:
    raise ValueError("Не найдена переменная окружения BOT_TOKEN")

if not GROUP_ID_RAW:
    raise ValueError("Не найдена переменная окружения GROUP_ID")

try:
    GROUP_ID = int(GROUP_ID_RAW)
except ValueError:
    raise ValueError("GROUP_ID должен быть числом, например: -1001234567890")

# ===== Состояния диалога =====
REQUEST, PHONE, NAME = range(3)

SKIP_TEXT = "Пропустить"

skip_keyboard = ReplyKeyboardMarkup(
    [[SKIP_TEXT]],
    resize_keyboard=True,
    one_time_keyboard=True
)

WELCOME_TEXT = """
Привет! Я бот Momty 💛

Помогаю организовать красивые свидания, детские праздники и необычные мероприятия.

Пожалуйста, опишите ваш запрос как можно подробнее ✨
"""

THANK_YOU_TEXT = """
Спасибо! Ваш запрос отправлен команде Momty 💛

Пожалуйста, ожидайте ответа здесь.
"""

# ===== Пользователь: старт =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Бот работает с пользователем только в личке
    if update.effective_chat.type != "private":
        return

    # очищаем старые данные формы
    context.user_data.clear()

    await update.message.reply_text(
        WELCOME_TEXT,
        reply_markup=ReplyKeyboardRemove()
    )
    return REQUEST

# ===== Шаг 1: запрос =====
async def get_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return

    text = update.message.text.strip()
    context.user_data["request_text"] = text

    await update.message.reply_text(
        "Если хотите, оставьте ваш номер телефона.\n\n"
        "Если не хотите указывать — нажмите «Пропустить».",
        reply_markup=skip_keyboard
    )
    return PHONE

# ===== Шаг 2: телефон =====
async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return

    text = update.message.text.strip()

    if text == SKIP_TEXT:
        context.user_data["phone"] = "Не указан"
    else:
        context.user_data["phone"] = text

    await update.message.reply_text(
        "Как к вам обращаться?\n\n"
        "Если не хотите указывать имя — нажмите «Пропустить».",
        reply_markup=skip_keyboard
    )
    return NAME

# ===== Шаг 3: имя + отправка в группу =====
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return

    text = update.message.text.strip()

    if text == SKIP_TEXT:
        context.user_data["name"] = "Не указано"
    else:
        context.user_data["name"] = text

    user = update.effective_user
    username = f"@{user.username}" if user.username else "без username"

    request_text = context.user_data.get("request_text", "Не указан")
    phone = context.user_data.get("phone", "Не указан")
    name = context.user_data.get("name", "Не указано")

    admin_text = (
        "📩 Новый запрос Momty\n\n"
        f"🆔 Диалог с пользователем: {user.id}\n"
        f"👤 Имя в Telegram: {user.first_name or '-'}\n"
        f"🔗 Username: {username}\n"
        f"📞 Телефон: {phone}\n"
        f"📝 Имя для связи: {name}\n\n"
        "💬 Запрос:\n"
        f"{request_text}\n\n"
        "↩️ Чтобы ответить клиенту, ответьте РЕПЛАЕМ на это сообщение в группе."
    )

    sent_message = await context.bot.send_message(
        chat_id=GROUP_ID,
        text=admin_text
    )

    # сохраняем связь "сообщение в группе -> пользователь"
    reply_map = context.application.bot_data.setdefault("reply_map", {})
    reply_map[sent_message.message_id] = user.id

    await update.message.reply_text(
        THANK_YOU_TEXT,
        reply_markup=ReplyKeyboardRemove()
    )

    context.user_data.clear()
    return ConversationHandler.END

# ===== Отмена =====
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return ConversationHandler.END

    context.user_data.clear()
    await update.message.reply_text(
        "Диалог отменён.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# ===== Ответ модератора из группы =====
async def handle_group_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # работаем только в нужной группе
    if update.effective_chat.id != GROUP_ID:
        return

    message = update.message

    # если это не reply — игнорируем
    if not message.reply_to_message:
        return

    reply_to_id = message.reply_to_message.message_id
    reply_map = context.application.bot_data.setdefault("reply_map", {})

    # если reply не на карточку клиента — игнорируем
    if reply_to_id not in reply_map:
        return

    user_id = reply_map[reply_to_id]

    # не отправляем команды как ответ клиенту
    if message.text and message.text.startswith("/"):
        return

    # поддержка текста
    if message.text:
        await context.bot.send_message(chat_id=user_id, text=message.text)

    # поддержка фото
    elif message.photo:
        caption = message.caption if message.caption else ""
        await context.bot.send_photo(
            chat_id=user_id,
            photo=message.photo[-1].file_id,
            caption=caption
        )

    # поддержка видео
    elif message.video:
        caption = message.caption if message.caption else ""
        await context.bot.send_video(
            chat_id=user_id,
            video=message.video.file_id,
            caption=caption
        )

    # поддержка голосовых
    elif message.voice:
        await context.bot.send_voice(
            chat_id=user_id,
            voice=message.voice.file_id
        )

    # поддержка документов
    elif message.document:
        caption = message.caption if message.caption else ""
        await context.bot.send_document(
            chat_id=user_id,
            document=message.document.file_id,
            caption=caption
        )

    else:
        await message.reply_text("Этот тип ответа пока не поддерживается ботом.")
        return

    # уведомление для модератора
    await message.reply_text("✅ Ответ отправлен пользователю.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            REQUEST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_request)
            ],
            PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)
            ],
            NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Личная переписка с пользователем
    app.add_handler(conv_handler)

    # Ответы модераторов из группы
    app.add_handler(
        MessageHandler(
            (filters.TEXT | filters.PHOTO | filters.VIDEO | filters.VOICE | filters.Document.ALL)
            & ~filters.COMMAND,
            handle_group_reply,
        )
    )

    print("Momty bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()