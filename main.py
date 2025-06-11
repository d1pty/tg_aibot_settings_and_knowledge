import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from config import TELEGRAM_BOT_TOKEN, BTN_SETTINGS, BTN_KNOWLEDGE, BTN_CHANGE, BTN_BACK, ADMIN_GROUP_ID
from db import init_db
from handlers import (
    start,
    handle_main_menu,
    handle_update_menu,
    handle_update_input,
    answer_query,
    admin_toggle_bot,
    admin_reply
)

def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
    )

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.job_queue.run_once(lambda ctx: init_db(), 0)

    application.add_handler(CommandHandler('start', start))

    application.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(f"^({BTN_SETTINGS}|{BTN_KNOWLEDGE})$"),
        handle_main_menu
    ))

    application.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(f"^({BTN_CHANGE}|{BTN_BACK})$"),
        handle_update_menu
    ))
    application.add_handler(MessageHandler(
        filters.Chat(ADMIN_GROUP_ID) & filters.Regex(r"^/(disable|enable)"),
        admin_toggle_bot
    ))

    application.add_handler(MessageHandler(
        filters.Chat(ADMIN_GROUP_ID) & filters.TEXT & ~filters.Regex(r"^/"),
        admin_reply
    ))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_update_input))

    application.run_polling()


if __name__ == '__main__':
    main()