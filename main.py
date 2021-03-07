from telegram.ext import (Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, PollAnswerHandler)

from database.db import Db
from modules.admin_functions import get_user_id, store, users, reveal, search
from modules.functions import help_menu, status, skip
from modules.handlers import callback_query_handler, message_handler, poll_answer_handler, sticker_handler, \
    message_all_handler, error_handle
from modules.questionnaire import cancel

if __name__ == '__main__':
    updater = Updater('TOKEN', use_context=True,
                      request_kwargs={'read_timeout': 6, 'connect_timeout': 7})
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('chat', help_menu))
    dp.add_handler(CommandHandler('start', help_menu))
    dp.add_handler(CommandHandler('help', help_menu))
    dp.add_handler(CommandHandler('status', status))
    dp.add_handler(CommandHandler('cancel', cancel))
    dp.add_handler(CommandHandler('chat_id', get_user_id))
    dp.add_handler(CommandHandler('skip', skip))
    dp.add_handler(CommandHandler('save', store))
    dp.add_handler(CommandHandler('users', users))
    dp.add_handler(CommandHandler('reveal', reveal))
    dp.add_handler(CommandHandler('search', search))
    dp.add_handler(CallbackQueryHandler(callback_query_handler))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, message_handler))
    dp.add_handler(MessageHandler(Filters.sticker, sticker_handler))
    dp.add_handler(MessageHandler(Filters.all & ~Filters.command, message_all_handler))
    dp.add_handler(PollAnswerHandler(poll_answer_handler))
    dp.add_error_handler(error_handle)

    Db.get_instance().create_black_list()

    updater.start_polling()
    updater.idle()
