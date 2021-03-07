from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext

import data
import utils
from database.db import Db
from models.request import Request
from models.users import User


def welcome(chat_id: int, context: CallbackContext) -> None:
    menu = [
        [InlineKeyboardButton("Do you want to date?", callback_data=utils.DATE), ],
        [InlineKeyboardButton("Make Friends", callback_data=utils.FRIENDS)],
        [InlineKeyboardButton("Privacy Policy", callback_data=utils.PRIVATE_POLICY_CALLBACK_DATA),
         InlineKeyboardButton("About Us", callback_data=utils.ABOUT_US_CALLBACK_DATA)]]
    msg = context.bot.send_message(text=utils.WELCOME_TEXT,
                                   parse_mode=ParseMode.MARKDOWN,
                                   chat_id=chat_id,
                                   reply_markup=InlineKeyboardMarkup(menu))
    data.delete_msg(chat_id, context)
    data.active_commands[chat_id] = msg.message_id


def helper(chat_id: int, context: CallbackContext):
    if chat_id in data.black_list:
        context.bot.send_message(chat_id, utils.BLACK_LIST_CUSTOM_MESSAGE, ParseMode.MARKDOWN)
    if data.active_chats.get(chat_id, None):
        if Db.get_instance().get_questions(chat_id):
            menu = [[InlineKeyboardButton("Reveal Identity Request", callback_data=utils.REVEAL_IDENTITY_REQUEST), ],
                    [InlineKeyboardButton("Send Questionnaire", callback_data=utils.QUESTIONNAIRE_SENT), ],
                    [InlineKeyboardButton("Report Chat", callback_data=utils.REPORT_CHAT),
                     InlineKeyboardButton("View/ Edit Questionnaire", callback_data=utils.QUESTIONNAIRE)],
                    [InlineKeyboardButton("Close Chat Portal", callback_data=utils.CLOSE_CHAT), ]]
        else:
            menu = [[InlineKeyboardButton("Reveal Identity Request", callback_data=utils.REVEAL_IDENTITY_REQUEST), ],
                    [InlineKeyboardButton("Report Chat", callback_data=utils.REPORT_CHAT),
                     InlineKeyboardButton("View/ Edit Questionnaire", callback_data=utils.QUESTIONNAIRE)],
                    [InlineKeyboardButton("Close Chat Portal", callback_data=utils.CLOSE_CHAT), ]]
        data.delete_msg(chat_id, context)
        data.active_commands[chat_id] = context.bot.send_message(chat_id, "``` Anonymous Chat Settings ```",
                                                                 ParseMode.MARKDOWN,
                                                                 reply_markup=InlineKeyboardMarkup(menu)).message_id
        return
    user = Db.get_instance().read_user_data(chat_id)
    if user:
        if user.date == 1:
            menu = [[InlineKeyboardButton("Random Chat", callback_data=utils.RANDOM_CHAT_CALLBACK_DATA), ],
                    [InlineKeyboardButton("Questionnaire", callback_data=utils.QUESTIONNAIRE), ],
                    [InlineKeyboardButton("Switch to Date Track", callback_data=utils.SWITCH_TO_DATE), ],
                    [InlineKeyboardButton("Alter Interest", callback_data=utils.ALTER_INT_CALLBACK_DATA), ],
                    [InlineKeyboardButton("How This Works", callback_data=utils.WALKABOUT_CALLBACK_DATA),
                     InlineKeyboardButton("Commands", callback_data=utils.COMMAND_CALLBACK_DATA)]]
        elif user.date == -1:
            menu = [[InlineKeyboardButton("Random Chat", callback_data=utils.RANDOM_CHAT_CALLBACK_DATA), ],
                    [InlineKeyboardButton("Questionnaire", callback_data=utils.QUESTIONNAIRE), ],
                    [InlineKeyboardButton("Switch to Make Friends Track",
                                          callback_data=utils.SWITCH_TO_MAKE_FRIENDS), ],
                    [InlineKeyboardButton("Alter Interest", callback_data=utils.ALTER_INT_CALLBACK_DATA), ],
                    [InlineKeyboardButton("How This Works", callback_data=utils.WALKABOUT_CALLBACK_DATA),
                     InlineKeyboardButton("Commands", callback_data=utils.COMMAND_CALLBACK_DATA)]]
        msg = context.bot.send_message(text="``` TxTKM Anonymous Chat Settings ```",
                                       parse_mode=ParseMode.MARKDOWN,
                                       chat_id=chat_id,
                                       reply_markup=InlineKeyboardMarkup(menu))
        data.delete_msg(chat_id, context)
        data.active_commands[chat_id] = msg.message_id
    else:
        welcome(chat_id, context)


def help_menu(update: Update, context: CallbackContext) -> None:
    if Db.get_instance().get_slug(update.message.chat.id) is None:
        Db.get_instance().add_slug(update.message.chat.id, update.to_json())
    helper(update.message.chat.id, context)


def status_code(chat_id: int):
    if Db.get_instance().read_user_data(chat_id):
        return -1
    if data.active_chats.get(chat_id, None):
        return 1
    if data.active_requests.get(chat_id, None):
        return 0


def status(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    code = status_code(chat_id)
    if code == 1:
        data.delete_msg(chat_id, context)
        data.active_commands[chat_id] = context.bot.send_message(chat_id,
                                                                 """``` You are in a chat with an anonymous person```""",
                                                                 ParseMode.MARKDOWN).message_id
    elif code == -1:
        data.delete_msg(chat_id, context)
        data.active_commands[chat_id] = context.bot.send_message(chat_id,
                                                                 """``` You are all set to go Anonymous```""",
                                                                 parse_mode=ParseMode.MARKDOWN).message_id
    elif code == 0:
        data.delete_msg(chat_id, context)
        res: Request = data.active_requests.get(chat_id, None)
        if res:
            if res.tel_id == chat_id:
                keyboard = [[InlineKeyboardButton("CANCEL REQUEST", callback_data=utils.CANCEL_REQUEST_CALLBACK_DATA)]]
                msg_id = context.bot.send_message(chat_id,
                                                  """``` You are in request phase Waiting for Accepting```""",
                                                  ParseMode.MARKDOWN,
                                                  reply_markup=InlineKeyboardMarkup(keyboard)).message_id
                data.active_commands[chat_id] = msg_id
            elif res.tel_to == chat_id:
                keyboard = [[InlineKeyboardButton("ACCEPT", callback_data=utils.ACCEPT_CALLBACK_DATA),
                             InlineKeyboardButton("DECLINE", callback_data=utils.DECLINE_CALLBACK_DATA), ], ]
                msg_id = context.bot.send_message(chat_id,
                                                  """``` You are in request phase```""",
                                                  ParseMode.MARKDOWN,
                                                  reply_markup=InlineKeyboardMarkup(keyboard)).message_id
                data.active_commands[chat_id] = msg_id


def register_user(update: Update, context: CallbackContext, mode):
    chat_id = update.callback_query.message.chat.id
    if Db.get_instance().read_user_data(chat_id) is None:
        if data.current_list_users.get(chat_id, None) is None:
            data.delete_msg(chat_id, context)
            keyboard = [
                [InlineKeyboardButton("SKIP PROVIDING CREDENTIALS", callback_data=utils.SKIP_REG_CALLBACK_DATA)]]
            data.active_commands[chat_id] = context.bot.send_message(chat_id, utils.ASK_FOR_NAME, ParseMode.MARKDOWN,
                                                                     reply_markup=InlineKeyboardMarkup(
                                                                         keyboard)).message_id
            user = User(update.callback_query.message.chat.id)
            user.askedName = True
            user.date = mode
            data.current_list_users[update.callback_query.message.chat.id] = user


def ask_gender(chat_id, context, mode):
    user = data.current_list_users.get(chat_id, None)
    if user.date == 1:
        keyboard = [[InlineKeyboardButton("He/Him", callback_data=utils.MALE_CALLBACK_DATA),
                     InlineKeyboardButton("She/Her", callback_data=utils.FEMALE_CALLBACK_DATA), ], [
                        InlineKeyboardButton("Prefer Not To Say", callback_data=utils.NEUTRAL_CALLBACK_DATA), ]]
    else:
        keyboard = [[InlineKeyboardButton("He/Him", callback_data=utils.MALE_CALLBACK_DATA),
                     InlineKeyboardButton("She/Her", callback_data=utils.FEMALE_CALLBACK_DATA), ]]
    data.delete_msg(chat_id, context)
    if mode == 1:
        user.askedGender = True
        text = utils.ASK_FOR_GENDER
    else:
        user.askedRec = True
        text = utils.ASK_FOR_REC_GENDER
    data.active_commands[chat_id] = context.bot.send_message(chat_id,
                                                             text=text,
                                                             parse_mode=ParseMode.MARKDOWN,
                                                             reply_markup=InlineKeyboardMarkup(
                                                                 keyboard)).message_id


def check_for_name(update, context: CallbackContext):
    chat_id = update.message.chat.id
    user = data.current_list_users.get(chat_id, None)
    if user and user.askedName:
        name = update.message.text
        user.set_name(name)
        user.askedName = False
        data.delete_msg(chat_id, context)
        keyboard = [
            [InlineKeyboardButton("SKIP PROVIDING CREDENTIALS", callback_data=utils.SKIP_REG_CALLBACK_DATA)]]
        data.active_commands[chat_id] = context.bot.send_message(text=utils.ASK_FOR_ID,
                                                                 parse_mode=ParseMode.MARKDOWN,
                                                                 chat_id=chat_id,
                                                                 reply_markup=InlineKeyboardMarkup(keyboard)).message_id
        return True
    return False


def set_gender(update, context, gender):
    chat_id = update.callback_query.message.chat.id
    user: User = data.current_list_users.get(chat_id, None)
    if user and user.askedGender:
        if gender == utils.MALE_CALLBACK_DATA:
            user.gender = 1
        elif gender == utils.FEMALE_CALLBACK_DATA:
            user.gender = -1
        user.askedGender = False
        data.delete_msg(chat_id, context)
        if user.date == 1:
            context.bot.send_message(text=f'``` Inserted Data\n'
                                          f'Name {user.name}\n'
                                          f'Instagram {user.instagram_id}\n'
                                          f'Gender {user.GENDER[user.gender]}\n'
                                          f'Year {user.batch}```',
                                     parse_mode=ParseMode.MARKDOWN,
                                     chat_id=update.callback_query.message.chat.id, )
            Db.get_instance().add_user(user)
            data.active_commands[update.callback_query.message.chat.id] = context.bot.send_poll(
                update.callback_query.message.chat.id,
                utils.ASK_FOR_INTEREST,
                utils.INTEREST_LIST,
                allows_multiple_answers=True,
                is_anonymous=False).message_id
            user.askedSkill = True
        else:
            ask_gender(update.callback_query.message.chat.id, context, -1)
            pass
    elif user and user.askedRec:
        if gender == utils.MALE_CALLBACK_DATA:
            user.rec = 1
        elif gender == utils.FEMALE_CALLBACK_DATA:
            user.rec = -1
        user.askedRec = False
        data.delete_msg(chat_id, context)
        context.bot.send_message(text=f'``` Inserted Data\n'
                                      f'Name {user.name}\n'
                                      f'Instagram {user.instagram_id}\n'
                                      f'Gender {user.GENDER[user.gender]}\n'
                                      f'Year {user.batch}\n'
                                      f'Receiver {user.GENDER[user.gender]}```',
                                 parse_mode=ParseMode.MARKDOWN,
                                 chat_id=update.callback_query.message.chat.id, )
        if Db.get_instance().read_user_data(chat_id):
            Db.get_instance().change_mode(chat_id, user.date)
            Db.get_instance().update_user(user)
            del data.current_list_users[chat_id]
            helper(chat_id, context)
            return
        Db.get_instance().add_user(user)
        data.active_commands[update.callback_query.message.chat.id] = context.bot.send_poll(
            update.callback_query.message.chat.id,
            utils.ASK_FOR_INTEREST,
            utils.INTEREST_LIST,
            allows_multiple_answers=True,
            is_anonymous=False).message_id
        user.askedSkill = True


def check_id(update: Update, context: CallbackContext) -> bool:
    user: User = data.current_list_users.get(update.message.chat.id, None)
    if user and user.askedId:
        user.set_id(update.message.text)
        user.askedId = False
        data.delete_msg(update.message.chat.id, context)
        keyboard = [
            [InlineKeyboardButton("SKIP PROVIDING CREDENTIALS", callback_data=utils.SKIP_REG_CALLBACK_DATA)]]
        data.active_commands[update.message.chat.id] = context.bot.send_message(text=utils.ASK_FOR_BATCH,
                                                                                parse_mode=ParseMode.MARKDOWN,
                                                                                chat_id=update.message.chat.id,
                                                                                reply_markup=InlineKeyboardMarkup(
                                                                                    keyboard)).message_id
        return True
    return False


def check_batch(update: Update, context: CallbackContext) -> bool:
    user: User = data.current_list_users.get(update.message.chat.id, None)
    if user and user.askedBatch:
        user.set_batch(update.message.text)
        user.askedBatch = False
        data.delete_msg(update.message.chat.id, context)
        ask_gender(update.message.chat_id, context, 1)
        return True
    return False


def add_poll(update, context):
    user_id = update.poll_answer.user.id
    user = data.current_list_users.get(user_id, None)
    if user and user.askedSkill:
        Db.get_instance().add_interest(user_id, update.poll_answer.option_ids[:3])
        msg = [utils.INTEREST_LIST[i] for i in update.poll_answer.option_ids[:3]]
        user.askedSkill = False
        context.bot.send_message(text=f'``` Selected Interest:- {",".join(msg)} ```',
                                 parse_mode=ParseMode.MARKDOWN,
                                 chat_id=user_id, )
        del data.current_list_users[user_id]
        context.bot.send_message(text=f'``` You are all set to go Anonymous ```',
                                 parse_mode=ParseMode.MARKDOWN,
                                 chat_id=user_id, )
        helper(user_id, context)
        return True
    return False


def switch_to_friends(update, context):
    Db.get_instance().change_mode(update.callback_query.message.chat.id, 1)
    context.bot.send_message(update.callback_query.message.chat.id, '``` Switched to Make Friends Track```',
                             ParseMode.MARKDOWN)
    helper(update.callback_query.message.chat.id, context)
    pass


def switch_to_date_track(update, context):
    user = Db.get_instance().read_user_data(update.callback_query.message.chat.id)
    user.date = -1
    user.askedGender = True
    user.askedName = False
    user.askedRec = False
    user.askedBatch = False
    user.askedSkill = False
    user.askedId = False
    context.bot.send_message(update.callback_query.message.chat.id, '``` Switched to Dating Track```',
                             ParseMode.MARKDOWN)
    data.current_list_users[update.callback_query.message.chat.id] = user
    ask_gender(user.tel_id, context, 1)


def alter_interest(update, context):
    chat_id = update.callback_query.message.chat.id
    user = Db.get_instance().read_user_data(chat_id)
    user.askedName = user.askedId = user.askedBatch = user.askedRec = user.askedGender = False
    user.askedSkill = True
    data.delete_msg(chat_id, context)
    data.active_commands[chat_id] = context.bot.send_poll(chat_id, utils.ASK_FOR_INTEREST, utils.INTEREST_LIST,
                                                          allows_multiple_answers=True,
                                                          is_anonymous=False).message_id
    data.current_list_users[chat_id] = user


def skip_process(message, context):
    chat_id = message.chat.id
    if not Db.get_instance().read_user_data(chat_id):
        user: User = data.current_list_users.get(chat_id, None)
        if user:
            if user.date == 1:
                Db.get_instance().add_user(user)
                data.delete_msg(message.chat.id, context)
                data.active_commands[chat_id] = context.bot.send_poll(chat_id, utils.ASK_FOR_INTEREST,
                                                                      utils.INTEREST_LIST,
                                                                      allows_multiple_answers=True,
                                                                      is_anonymous=False).message_id
                user.askedSkill = True
                user.askedName = user.askedId = user.askedBatch = user.askedRec = user.askedGender = False
            elif user.date == -1:
                user.askedGender = True
                user.askedName = user.askedId = user.askedBatch = user.askedRec = user.askedSkill = False
                ask_gender(chat_id, context, 1)


def skip(update, context):
    skip_process(update.message, context)
