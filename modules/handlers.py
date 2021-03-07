import html
import json
import logging
import traceback

from telegram import Update, ParseMode, error
from telegram.ext import CallbackContext

import data
import utils
from database.db import Db
from .chat_functions import (set_up_random_chat, accept_request_to_chat, cancel_chat_request, decline_chat_request,
                             close_chat, report_chat, report_confirmation, reveal_request, status_code,
                             accept_reveal_request, decline_reveal_request)
from .functions import (register_user, check_for_name, set_gender, check_id, check_batch, add_poll, switch_to_friends,
                        switch_to_date_track, alter_interest, skip_process, helper)
from .questionnaire import (questionnaire, edit_questionnaire, view_questionnaire, send_questionnaire, parse_questions,
                            handle_answers)


def callback_query_handler(update: Update, context: CallbackContext):
    if update.callback_query.message.chat.id in data.black_list:
        update.callback_query.message.reply_markdown(utils.BLACK_LIST_CUSTOM_MESSAGE)
        return
    if update.callback_query.data == utils.DATE:
        register_user(update, context, -1)
    elif update.callback_query.data == utils.FRIENDS:
        register_user(update, context, 1)
    elif update.callback_query.data == utils.MALE_CALLBACK_DATA or utils.FEMALE_CALLBACK_DATA == update.callback_query.data:
        set_gender(update, context, update.callback_query.data)
    elif update.callback_query.data == utils.RANDOM_CHAT_CALLBACK_DATA:
        set_up_random_chat(update, context)
    elif update.callback_query.data == utils.ACCEPT_CALLBACK_DATA:
        accept_request_to_chat(update, context)
    elif update.callback_query.data == utils.DECLINE_CALLBACK_DATA:
        decline_chat_request(update, context)
    elif update.callback_query.data == utils.CANCEL_REQUEST_CALLBACK_DATA:
        cancel_chat_request(update.callback_query.message, context)
    elif update.callback_query.data == utils.CLOSE_CHAT:
        close_chat(update, context)
    elif update.callback_query.data == utils.REPORT_CHAT:
        report_chat(update, context)
    elif update.callback_query.data == utils.ACCEPT_REPORT_CALLBACK_DATA or update.callback_query.data == utils.DECLINE_REPORT_CALLBACK_DATA:
        report_confirmation(update, context)
    elif update.callback_query.data == utils.SWITCH_TO_MAKE_FRIENDS:
        switch_to_friends(update, context)
    elif update.callback_query.data == utils.SWITCH_TO_DATE:
        switch_to_date_track(update, context)
    elif update.callback_query.data == utils.ALTER_INT_CALLBACK_DATA:
        alter_interest(update, context)
    elif update.callback_query.data == utils.REVEAL_IDENTITY_REQUEST:
        reveal_request(update, context)
    elif update.callback_query.data == utils.SKIP_REG_CALLBACK_DATA:
        skip_process(update.callback_query.message, context)
    elif update.callback_query.data == utils.DECLINE_CALLBACK_DATA:
        decline_reveal_request(update, context)
    elif update.callback_query.data == utils.ACCEPT_CALLBACK_DATA:
        accept_reveal_request(update, context)
    elif update.callback_query.data == utils.QUESTIONNAIRE:
        questionnaire(update, context)
    elif update.callback_query.data == utils.QUESTIONNAIRE_SET:
        edit_questionnaire(update, context)
    elif update.callback_query.data == utils.QUESTIONNAIRE_SENT:
        send_questionnaire(update, context)
    elif update.callback_query.data == utils.VIEW_QUES:
        view_questionnaire(update, context)
    elif update.callback_query.data == utils.MENU:
        helper(update.callback_query.message.chat_id, context)
    elif update.callback_query.data == utils.COMMAND_CALLBACK_DATA:
        context.bot.send_message(update.callback_query.message.chat.id, utils.COMMANDS, ParseMode.MARKDOWN)
    elif update.callback_query.data == utils.ABOUT_US_CALLBACK_DATA:
        context.bot.send_message(update.callback_query.message.chat.id, utils.ABOUT_US, ParseMode.MARKDOWN)
    elif update.callback_query.data == utils.WALKABOUT_CALLBACK_DATA:
        context.bot.send_message(update.callback_query.message.chat.id, utils.HOW_THIS_WORKS, ParseMode.MARKDOWN)
    elif update.callback_query.data == utils.PRIVATE_POLICY_CALLBACK_DATA:
        context.bot.send_message(update.callback_query.message.chat.id,
                                 "https://telegra.ph/Privacy-Policy-for-Under-25-TKMCE-02-03")


def search_keywords(text):
    for i in utils.KEYWORDS:
        if text.find(i) != -1:
            return False
    return True


def message_handler(update: Update, context: CallbackContext):
    if update.edited_message is not None:
        context.bot.send_message(update.edited_message.chat.id, '``` Edit Message Feature Unavailable! ```',
                                 ParseMode.MARKDOWN)
        return
    if update.message.chat.id in data.black_list:
        update.message.reply_markdown(utils.BLACK_LIST_CUSTOM_MESSAGE)
        return
    if check_for_name(update, context):
        return
    elif check_id(update, context):
        return
    elif check_batch(update, context):
        return
    if data.asked_questionnaire.get(update.message.chat.id, None):
        parse_questions(update, context)
        return
    if data.active_chats.get(update.message.chat.id, None):
        if search_keywords(update.message.text):
            context.bot.send_message(data.active_chats[update.message.chat.id], update.message.text)
        else:
            context.bot.send_message(text="``` HATE SPEECH Detected ! Warned (5 Warns Turns to Block)```",
                                     parse_mode=ParseMode.MARKDOWN,
                                     chat_id=update.message.chat.id)
            Db.get_instance().update_block(update.message.chat.id)


def poll_answer_handler(update: Update, context: CallbackContext):
    if update.poll_answer.user.id in data.black_list:
        update.message.reply_markdown(utils.BLACK_LIST_CUSTOM_MESSAGE)
        return
    if add_poll(update, context):
        return
    handle_answers(update, context)


def sticker_handler(update: Update, context: CallbackContext):
    if update.message.chat.id in data.black_list:
        update.message.reply_markdown(utils.BLACK_LIST_CUSTOM_MESSAGE)
        return
    if data.active_chats.get(update.message.chat.id, None):
        context.bot.send_sticker(sticker=update.message.sticker, chat_id=data.active_chats[update.message.chat.id])


def message_all_handler(update: Update, context: CallbackContext):
    if update.message.chat.id in data.black_list:
        update.message.reply_markdown(utils.BLACK_LIST_CUSTOM_MESSAGE)
        return
    update.message.reply_markdown("""``` Files Sharing Not Supported according to privacy policy```""")


def error_handle(update: Update, context: CallbackContext) -> None:
    logger = logging.getLogger()
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    print(context.error)
    if isinstance(context.error, error.BadRequest):
        update.message.reply_markdown("``` Kindly Repeat the process ```")
        data.active_commands[update.message.chat_id] = None
    elif isinstance(context.error, error.Unauthorized):
        if status_code(update.message.chat_id) == 1:
            context.bot.send_message(update.message.chat_id,
                                     "``` The Anonymous user blocked the chat bot so we are stopping the chat````",
                                     parse_mode=ParseMode.MARKDOWN, )
            Db.get_instance().delete_user(data.active_chats[update.message.chat_id])
            Db.get_instance().update_user_disconnected(update.message.chat_id)
            del data.active_chats[update.message.chat_id]
        elif status_code(update.message.chat_id) == 0:
            context.bot.send_message(update.message.chat_id,
                                     "``` The Anonymous user blocked the chat bot so make another request````",
                                     parse_mode=ParseMode.MARKDOWN, )
            cancel_chat_request(update.message, context)
            Db.get_instance().delete_user(data.active_requests[update.message.chat_id])
    elif isinstance(context.error, error.TimedOut):
        print(update)
        context.bot.send_message(update.message.chat_id,
                                 "``` Connection Timed Out Repeat the process````",
                                 parse_mode=ParseMode.MARKDOWN, )
        helper(update.message.chat_id, context)
    tb_string = ''.join(tb_list)
    message = (
        f'An exception was raised while handling an update\n'
        f'<pre>update = {html.escape(json.dumps(update.to_dict(), indent=2, ensure_ascii=False))}'
        '</pre>\n\n'
        f'<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n'
        f'<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n'
        f'<pre>{html.escape(tb_string)}</pre>'
    )
    context.bot.send_message(chat_id=utils.DEV_ID, text=message, parse_mode=ParseMode.HTML)
