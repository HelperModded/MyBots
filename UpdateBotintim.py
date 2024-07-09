from telegram import Update, Bot, PhotoSize, Video
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext
import logging
import random
import json
import os

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

BOT_TOKEN = '7010837600:AAHxE5bjnPD0_3lAUoyD8J76PmJC2oTGuVU'
MEDIA_CHANNEL_ID = '2165228328'
USERNAMES_CHANNEL_ID = '2235641578'
SOURCE_CHANNEL_ID = '2165228328' 

OWNER_ID = '7302923565'
 

OWNER_ID = 'OWNER_ID'

RESPONSE_PHOTOS = []
RESPONSE_VIDEOS = []
BANNED_USERS_FILE = "banned_users.json"
BANNED_USERS = set()
USERS_DATA_FILE = "users_data.json"
users_data = {}

if os.path.exists(BANNED_USERS_FILE):
    with open(BANNED_USERS_FILE, "r") as f:
        BANNED_USERS = set(json.load(f))

if os.path.exists(USERS_DATA_FILE):
    with open(USERS_DATA_FILE, "r") as f:
        users_data = json.load(f)

async def fetch_media_files(bot: Bot):
    async for message in bot.get_chat_history(chat_id=SOURCE_CHANNEL_ID, limit=100):
        if message.photo:
            file_id = message.photo[-1].file_id
            if file_id not in RESPONSE_PHOTOS:
                RESPONSE_PHOTOS.append(file_id)
        if message.video:
            file_id = message.video.file_id
            if file_id not in RESPONSE_VIDEOS:
                RESPONSE_VIDEOS.append(file_id)

async def start(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id in BANNED_USERS:
        return
    if str(update.effective_user.id) not in users_data:
        users_data[str(update.effective_user.id)] = {"currency": 0, "referrals": []}
        save_users_data()
    await update.message.reply_text("Привет! Я бот, который обменивает фото, видео и принимает юзернеймы если вы зотите лично обменять интимками с владельцем, просто ждите. Он вам напишет, а пока если хотите, то можете испробовать реферальную систему бота, для того что бы узнать больше напишите /referals")

async def link(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id in BANNED_USERS:
        return
    user_username = update.effective_user.username
    if user_username:
        await context.bot.send_message(chat_id=USERNAMES_CHANNEL_ID, text=f"Юзернейм пользователя: @{user_username}")
        await update.message.reply_text(f"Ваш юзернейм отправлен в базу данных, ждите пока с вами свяжутся, @{user_username}")
    else:
        await update.message.reply_text("У вас нет юзернейма")

async def handle_message(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id in BANNED_USERS:
        return
    if update.message.text and update.message.text.startswith('@'):
        await context.bot.send_message(chat_id=USERNAMES_CHANNEL_ID, text=f"Юзернейм: {update.message.text}")
    elif update.message.photo:
        file_id = update.message.photo[-1].file_id
        if file_id not in RESPONSE_PHOTOS:
            RESPONSE_PHOTOS.append(file_id)
            await context.bot.send_photo(chat_id=MEDIA_CHANNEL_ID, photo=file_id)
            if RESPONSE_PHOTOS:
                response_photo = random.choice(RESPONSE_PHOTOS)
                await context.bot.send_photo(chat_id=update.effective_chat.id, photo=response_photo)
            else:
                await update.message.reply_text("Нет доступных фото для обмена")
        else:
            await update.message.reply_text("Это фото уже есть в базе данных, поищите ещё")
    elif update.message.video:
        file_id = update.message.video.file_id
        if file_id not in RESPONSE_VIDEOS:
            RESPONSE_VIDEOS.append(file_id)
            await context.bot.send_video(chat_id=MEDIA_CHANNEL_ID, video=file_id)
            if RESPONSE_VIDEOS:
                response_video = random.choice(RESPONSE_VIDEOS)
                await context.bot.send_video(chat_id=update.effective_chat.id, video=response_video)
            else:
                await update.message.reply_text("Нет доступных видео для обмена")
        else:
            await update.message.reply_text("Это видео уже есть в базе данных, поищите ещё")

async def ban_user(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("У вас нет прав на использование этой команды.")
        return

    if not context.args:
        await update.message.reply_text("Пожалуйста, укажите пользователя для бана.")
        return

    try:
        user_id = int(context.args[0])
        BANNED_USERS.add(user_id)
        with open(BANNED_USERS_FILE, "w") as f:
            json.dump(list(BANNED_USERS), f)
        await update.message.reply_text(f"Пользователь {user_id} забанен в боте.")
    except Exception as e:
        await update.message.reply_text(f"Не удалось забанить пользователя {context.args[0]}. Ошибка: {e}")

async def referals(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id in BANNED_USERS:
        return
    referral_link = f"https://t.me/{context.bot.username}?start={update.effective_user.id}"
    await update.message.reply_text(
        f"1 валюта - 1 фото\n"
        f"2 валюты - 1 видео\n"
        f"Приглашай людей, для получения реферальной валюты.\n"
        f"Ваша реферальная ссылка: {referral_link}"
    )

async def handle_start_command(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id in BANNED_USERS:
        return
    referrer_id = context.args[0] if context.args else None
    if referrer_id and referrer_id != str(update.effective_user.id) and referrer_id in users_data:
        users_data[referrer_id]["currency"] += 10
        users_data[referrer_id]["referrals"].append(update.effective_user.id)
        save_users_data()
        await context.bot.send_message(chat_id=referrer_id, text=f"Вы получили 10 валюты за приглашение пользователя {update.effective_user.username}!")

def save_users_data():
    with open(USERS_DATA_FILE, "w") as f:
        json.dump(users_data, f)

async def buy_photo(update: Update, context: CallbackContext) -> None:
    user_id = str(update.effective_user.id)
    if user_id in users_data and users_data[user_id]["currency"] >= 1:
        users_data[user_id]["currency"] -= 1
        save_users_data()
        if RESPONSE_PHOTOS:
            response_photo = random.choice(RESPONSE_PHOTOS)
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=response_photo)
        else:
            await update.message.reply_text("Нет доступных фото для покупки")
    else:
        await update.message.reply_text("У вас недостаточно валюты для покупки фото")

async def buy_video(update: Update, context: CallbackContext) -> None:
    user_id = str(update.effective_user.id)
    if user_id in users_data and users_data[user_id]["currency"] >= 2:
        users_data[user_id]["currency"] -= 2
        save_users_data()
        if RESPONSE_VIDEOS:
            response_video = random.choice(RESPONSE_VIDEOS)
            await context.bot.send_video(chat_id=update.effective_chat.id, video=response_video)
        else:
            await update.message.reply_text("Нет доступных видео для покупки")
    else:
        await update.message.reply_text("У вас недостаточно валюты для покупки видео")

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("link", link))
    application.add_handler(CommandHandler("ban", ban_user))
    application.add_handler(CommandHandler("referals", referals))
    application.add_handler(CommandHandler("buy_photo", buy_photo))
    application.add_handler(CommandHandler("buy_video", buy_video))
    application.add_handler(CommandHandler("start", handle_start_command))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^@'), handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_message))
    application.add_handler(MessageHandler(filters.VIDEO, handle_message))

    bot = application.bot

    async def fetch_media_files_job(context: CallbackContext) -> None:
        await fetch_media_files(bot)

    application.job_queue.run_once(fetch_media_files_job, when=0)

    application.run_polling()

if __name__ == '__main__':
    main()
