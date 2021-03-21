from random import sample

from telegram import Update, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

import data
import utils
from database.db import Db
from models.request import Request
from .functions import status_code


def set_up_random_chat(update: Update, context: CallbackContext):
    chat_id = update.callback_query.message.chat_id
    code = status_code(chat_id)
    if code == 1:
        context.bot.send_message(chat_id, '``` Close the current chat portal to start a new one ```',
                                 ParseMode.MARKDOWN)
        return
    if code == 0:
        data.delete_msg(chat_id, context)
        req: Request = data.active_requests[chat_id]
        if req.tel_id == chat_id:
            keyboard = [[InlineKeyboardButton("CANCEL REQUEST", callback_data=utils.CANCEL_REQUEST_CALLBACK_DATA)]]
            data.active_commands[chat_id] = context.bot.send_message(
                chat_id,
                '``` You are in request phase Waiting for Accepting```',
                ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard)).message_id
        elif req.tel_to == chat_id:
            keyboard = [[InlineKeyboardButton("ACCEPT", callback_data=utils.ACCEPT_CALLBACK_DATA),
                         InlineKeyboardButton("DECLINE", callback_data=utils.DECLINE_CALLBACK_DATA), ], ]
            data.active_commands[chat_id] = context.bot.send_message(
                chat_id, '``` You are in request phase```', ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)).message_id
        return
    if code == -1:
        user = Db.get_instance().read_user_data(chat_id)
        if user and user.date == 1:
            df = Db.get_instance().read_available_users(chat_id, user.date)
            if len(df) == 0:
                context.bot.send_message(
                    text=f'``` Oops! No Users Available try after some time or Switch to Date Track```',
                    parse_mode=ParseMode.MARKDOWN,
                    chat_id=update.callback_query.message.chat.id, )
            else:
                user = sample(df, 1)[0]
                request = Request()
                request.make(chat_id, user.tel_id, 0)
                data.active_requests[chat_id] = request
                data.active_requests[user.tel_id] = request
                data.delete_msg(chat_id, context)
                keyboard = [[InlineKeyboardButton("CANCEL REQUEST", callback_data=utils.CANCEL_REQUEST_CALLBACK_DATA)]]
                data.active_commands[chat_id] = context.bot.send_message(chat_id, '``` Waiting for Confirmation ```',
                                                                         ParseMode.MARKDOWN,
                                                                         reply_markup=InlineKeyboardMarkup(
                                                                             keyboard)).message_id
                keyboard = [[InlineKeyboardButton("ACCEPT", callback_data=utils.ACCEPT_CALLBACK_DATA),
                             InlineKeyboardButton("DECLINE", callback_data=utils.DECLINE_CALLBACK_DATA), ], ]
                data.delete_msg(user.tel_id, context)
                data.active_commands[user.tel_id] = context.bot.send_message(user.tel_id,
                                                                             '``` Anonymous Chat Request ```',
                                                                             ParseMode.MARKDOWN,
                                                                             reply_markup=InlineKeyboardMarkup(
                                                                                 keyboard)).message_id
                Db.get_instance().update_user_status(chat_id, 1)
                Db.get_instance().update_user_status(user.tel_id, 1)
        elif user and user.date == -1:
            df = Db.get_instance().read_users_with_gender(user)
            if len(df) == 0:
                context.bot.send_message(
                    text=f'``` Oops! No Users Available for Dating try after some time or Switch to Make Friends '
                         f'Track```',
                    parse_mode=ParseMode.MARKDOWN,
                    chat_id=update.callback_query.message.chat.id, )
            else:
                user = sample(df, 1)[0]
                request = Request()
                request.make(chat_id, user.tel_id, 0)
                data.active_requests[chat_id] = request
                data.active_requests[user.tel_id] = request
                data.delete_msg(chat_id, context)
                keyboard = [[InlineKeyboardButton("CANCEL REQUEST", callback_data=utils.CANCEL_REQUEST_CALLBACK_DATA)]]
                data.active_commands[chat_id] = context.bot.send_message(chat_id, '``` Waiting for Confirmation ```',
                                                                         ParseMode.MARKDOWN,
                                                                         reply_markup=InlineKeyboardMarkup(
                                                                             keyboard)).message_id
                keyboard = [[InlineKeyboardButton("ACCEPT", callback_data=utils.ACCEPT_CALLBACK_DATA),
                             InlineKeyboardButton("DECLINE", callback_data=utils.DECLINE_CALLBACK_DATA), ], ]
                data.delete_msg(user.tel_id, context)
                data.active_commands[user.tel_id] = context.bot.send_message(user.tel_id,
                                                                             '``` Anonymous Date Request ```',
                                                                             ParseMode.MARKDOWN,
                                                                             reply_markup=InlineKeyboardMarkup(
                                                                                 keyboard)).message_id
                Db.get_instance().update_user_status(chat_id, 1)
                Db.get_instance().update_user_status(user.tel_id, 1)


def accept_request_to_chat(update: Update, context: CallbackContext):
    request: Request = data.active_requests.get(update.callback_query.message.chat_id, None)
    if request:
        tel_1 = request.tel_id
        tel_2 = request.tel_to
        data.active_chats[request.tel_id] = request.tel_to
        data.active_chats[request.tel_to] = request.tel_id
        del data.active_requests[tel_1]
        del data.active_requests[tel_2]
        data.delete_msg(tel_1, context)
        data.delete_msg(tel_2, context)
        context.bot.send_message(tel_1, f'``` The Messages Now on (except Commands will be visible to the Anonymous '
                                        f'person) ```', parse_mode=ParseMode.MARKDOWN)
        context.bot.send_message(tel_2, f'``` The Messages Now on (except Commands will be visible to the Anonymous '
                                        f'person) ```', parse_mode=ParseMode.MARKDOWN)
        context.bot.send_message(tel_1,
                                 f'``` Do not use this bot to indulge in any form of harassment of a person. You can '
                                 f'use the report feature to report any such behaviour. ```', ParseMode.MARKDOWN)
        context.bot.send_message(tel_2,
                                 f'``` Do not use this bot to indulge in any form of harassment of a person. You can '
                                 f'use the report feature to report any such behaviour. ```', ParseMode.MARKDOWN)
        data.active_commands[tel_1] = context.bot.send_message(text=f'``` Anonymous User Accepted the Request ```',
                                                               parse_mode=ParseMode.MARKDOWN,
                                                               chat_id=tel_1).message_id
        res = Db.get_instance().get_common_interests(tel_1, tel_2)
        val = [utils.INTEREST_LIST[x] for x in res[0].intersection(res[1])]
        if len(val) != 0:
            context.bot.send_message(tel_1, f'``` Common Interest {" ".join(val)} ```', ParseMode.MARKDOWN)
            context.bot.send_message(tel_2, f'``` Common Interest {" ".join(val)} ```', ParseMode.MARKDOWN)
        else:
            context.bot.send_message(tel_1,
                                     f'``` Interests the Anonymous User have:-  {" ".join([utils.INTEREST_LIST[i] for i in res[1]])}```',
                                     ParseMode.MARKDOWN)
            context.bot.send_message(tel_2,
                                     f'``` Interests the Anonymous User have:-  {" ".join([utils.INTEREST_LIST[i] for i in res[0]])}```',
                                     ParseMode.MARKDOWN)
    else:
        data.delete_msg(update.callback_query.message.chat_id, context)
        data.active_commands[update.callback_query.message.chat_id] = context.bot.send_message(
            update.callback_query.message.chat_id, f'``` Expired Request ```', ParseMode.MARKDOWN, ).message_id


def decline_chat_request(update, context):
    request: Request = data.active_requests.get(update.callback_query.message.chat_id, None)
    if request:
        tel_1 = request.tel_id
        tel_2 = request.tel_to
        del data.active_requests[tel_1]
        del data.active_requests[tel_2]
        data.delete_msg(tel_1, context)
        data.delete_msg(tel_2, context)
        data.active_commands[tel_1] = context.bot.send_message(tel_1, f'``` Request was cancelled ```',
                                                               ParseMode.MARKDOWN, ).message_id
        data.active_commands[tel_2] = context.bot.send_message(tel_2, f'``` Request was cancelled ```',
                                                               ParseMode.MARKDOWN, ).message_id
        Db.get_instance().update_user_status(tel_1, 0)
        Db.get_instance().update_user_status(tel_2, 0)
    else:
        data.delete_msg(update.callback_query.message.chat_id, context)
        data.active_commands[update.callback_query.message.chat_id] = context.bot.send_message(
            update.callback_query.message.chat_id, f'``` Expired Request ```', ParseMode.MARKDOWN, ).message_id


def cancel_chat_request(message, context: CallbackContext):
    request: Request = data.active_requests.get(message.chat_id, None)
    if request:
        tel_1 = request.tel_id
        tel_2 = request.tel_to
        try:
            del data.active_requests[tel_1]
            del data.active_requests[tel_2]
        except:
            pass
        data.delete_msg(tel_1, context)
        data.active_commands[tel_1] = context.bot.send_message(tel_1, '``` Request was cancelled ```',
                                                               ParseMode.MARKDOWN).message_id
        Db.get_instance().update_user_status(tel_1, 0)
        Db.get_instance().update_user_status(tel_2, 0)

    else:
        data.delete_msg(message.chat_id, context)
        data.active_commands[message.chat_id] = context.bot.send_message(
            message.chat_id, f'``` Expired Request ```', ParseMode.MARKDOWN, ).message_id


def close_chat(update, context):
    tel_id = data.active_chats.get(update.callback_query.message.chat_id, None)
    if tel_id:
        Db.get_instance().update_user_status(tel_id, 0)
        Db.get_instance().update_user_status(data.active_chats[tel_id], 0)
        data.delete_msg(tel_id, context)
        data.delete_msg(data.active_chats[tel_id], context)
        data.active_commands[tel_id] = context.bot.send_message(
            text=f'The chat with the user has ended, click /chat to find a new match',
            chat_id=tel_id).message_id
        data.active_commands[data.active_chats[tel_id]] = context.bot.send_message(
            text=f'The chat with the user has ended, click /chat to find a new match',
            chat_id=data.active_chats[tel_id]).message_id
        context.bot.send_message(text="/chat for chat settings",
                                 parse_mode=ParseMode.MARKDOWN,
                                 chat_id=data.active_chats[tel_id])
        context.bot.send_message(text="/chat for chat settings",
                                 parse_mode=ParseMode.MARKDOWN,
                                 chat_id=tel_id)
        del data.active_chats[data.active_chats[tel_id]]
        del data.active_chats[tel_id]


def report_chat(update: Update, context: CallbackContext):
    keyboard = [[InlineKeyboardButton("REPORT", callback_data=utils.ACCEPT_REPORT_CALLBACK_DATA),
                 InlineKeyboardButton("CANCEL", callback_data=utils.DECLINE_REPORT_CALLBACK_DATA), ], ]
    data.delete_msg(update.callback_query.message.chat.id, context)
    data.active_commands[update.callback_query.message.chat.id] = context.bot.send_message(
        text="""``` Are you sure to block the user? This may blacklist the user and will those this chat portal```""",
        chat_id=update.callback_query.message.chat.id,
        parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard)).message_id


def report_confirmation(update: Update, context: CallbackContext):
    if update.callback_query.data == utils.ACCEPT_REPORT_CALLBACK_DATA:
        context.bot.send_message(update.callback_query.message.chat_id, '``` Report Successful! ```',
                                 ParseMode.MARKDOWN)
        Db.get_instance().update_block(data.active_chats[update.callback_query.message.chat.id])
        close_chat(update, context)
    elif update.callback_query.data == utils.DECLINE_CALLBACK_DATA:
        data.delete_msg(update.callback_query.message.chat.id, context)
        data.active_commands[update.callback_query.message.chat.id] = context.bot.send_message(
            text="""``` Report Request Closed```""",
            chat_id=update.callback_query.message.chat.id,
            parse_mode=ParseMode.MARKDOWN).message_id


def reveal_request(update, context: CallbackContext):
    chat_id = update.callback_query.message.chat_id
    user = Db.get_instance().read_user_data(chat_id)
    if user:

        if user.name == utils.PLACEHOLDER:
            data.delete_msg(chat_id, context)
            data.active_commands[chat_id] = context.bot.send_message(chat_id,
                                                                     '``` You haven\'t provided the details```',
                                                                     ParseMode.MARKDOWN).message_id
            return
        else:
            user = Db.get_instance().read_user_data(data.active_chats[chat_id])
            if user:
                if user.name == utils.PLACEHOLDER:
                    data.delete_msg(user.tel_id, context)
                    data.active_commands[user.tel_id] = context.bot.send_message(user.tel_id,
                                                                                 '``` The user who\'s chatting with you hasn\'t provided the details ```',
                                                                                 ParseMode.MARKDOWN).message_id
                    return
        keyboard = [[InlineKeyboardButton("ACCEPT", callback_data=utils.ACCEPT_REVEAL_CALLBACK_DATA),
                     InlineKeyboardButton("DECLINE", callback_data=utils.DECLINE_REVEAL_CALLBACK_DATA), ], ]
        data.delete_msg(data.active_chats.get(chat_id, None), context)
        data.active_commands[data.active_chats[chat_id]] = context.bot.send_message(data.active_chats[chat_id],
                                                                                    '``` Reveal Request ```',
                                                                                    ParseMode.MARKDOWN,
                                                                                    reply_markup=InlineKeyboardMarkup(
                                                                                        keyboard)).message_id
        data.delete_msg(chat_id, context)
        data.active_commands[chat_id] = context.bot.send_message(chat_id, '``` Reveal Request Sent```',
                                                                 ParseMode.MARKDOWN).message_id
        request = Request()
        request.make(chat_id, data.active_chats[chat_id], 0)
        data.active_reveals[request.tel_id] = request
        data.active_reveals[request.tel_to] = request


def accept_reveal_request(update: Update, context: CallbackContext):
    user_id = update.callback_query.message.chat_id
    request = data.active_reveals.get(user_id, None)
    if request is None:
        data.delete_msg(user_id, context)
        data.active_commands[user_id] = context.bot.send_message(user_id, '``` Expired Request ```',
                                                                 ParseMode.MARKDOWN, ).message_id
        return
    data.delete_msg(user_id, context)
    data.delete_msg(data.active_chats.get(user_id, None), context)
    user = Db.get_instance().read_user_data(user_id)
    if user:
        msg = f'``` Name:-  {user.name}\n Instagram Id:- {user.instagram_id}\n Gender:- {user.GENDER[user.gender]}\n Batch:- {user.batch}```'
        context.bot.send_message(user.tel_id, msg, ParseMode.MARKDOWN)
    user = Db.get_instance().read_user_data(data.active_chats[user_id])
    if user:
        msg = f'``` Name:-  {user.name}\n Instagram Id:- {user.instagram_id}\n Gender:- {user.GENDER[user.gender]}\n Batch:- {user.batch}```'
        context.bot.send_message(user.tel_id, msg, ParseMode.MARKDOWN)
    del data.active_reveals[user_id]
    del data.active_reveals[data.active_chats[user_id]]


def decline_reveal_request(update: Update, context: CallbackContext):
    user_id = update.callback_query.message.chat.id
    request = data.active_reveals.get(user_id, None)
    if request is None:
        data.delete_msg(user_id, context)
        data.active_commands[user_id] = context.bot.send_message(user_id, '``` Expired Request ```',
                                                                 ParseMode.MARKDOWN, ).message_id
        return
    data.delete_msg(data.active_chats.get(user_id, None), context)
    data.delete_msg(user_id, context)
    data.active_commands[data.active_chats[user_id]] = context.bot.send_message(text="``` Reveal Request Declined```",
                                                                                parse_mode=ParseMode.MARKDOWN,
                                                                                chat_id=data.active_chats[
                                                                                    user_id]).message_id
    data.active_commands[user_id] = context.bot.send_message(text="``` Reveal Request Declined```",
                                                             parse_mode=ParseMode.MARKDOWN,
                                                             chat_id=user_id).message_id
    del data.active_reveals[user_id]
    del data.active_reveals[data.active_chats[user_id]]
