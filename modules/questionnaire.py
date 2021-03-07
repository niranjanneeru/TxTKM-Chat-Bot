from telegram import Update, ext, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup

import data
import utils
from database.db import Db


def edit_questionnaire(update: Update, context: ext.CallbackContext):
    chat_id = update.callback_query.message.chat_id
    data.delete_msg(chat_id, context)
    data.active_commands[chat_id] = context.bot.send_message(text=utils.ASK_FOR_QN, chat_id=chat_id,
                                                             parse_mode=ParseMode.MARKDOWN).message_id
    data.asked_questionnaire[update.callback_query.message.chat.id] = True


def view_questionnaire(update, context):
    chat_id = update.callback_query.message.chat_id
    data.delete_msg(chat_id, context)
    ques = Db.get_instance().get_questions(chat_id)
    msg = "Entered Questions\n"
    for i in ques:
        msg += f'{ques.index(i) + 1} {i.strip()}\n'
    keyboard = [[InlineKeyboardButton("Edit Questionnaire", callback_data=utils.QUESTIONNAIRE_SET),
                 InlineKeyboardButton("<- Menu", callback_data=utils.MENU), ], ]
    data.active_commands[chat_id] = context.bot.send_message(text=f"```{msg}```",
                                                             parse_mode=ParseMode.MARKDOWN,
                                                             chat_id=chat_id,
                                                             reply_markup=InlineKeyboardMarkup(keyboard)).message_id
    data.asked_questionnaire[chat_id] = False


def questionnaire(update: Update, context: ext.CallbackContext):
    chat_id = update.callback_query.message.chat_id
    data.delete_msg(chat_id, context)
    if Db.get_instance().get_questions(chat_id) is None:
        data.active_commands[chat_id] = context.bot.send_message(text=utils.ASK_FOR_QN, chat_id=chat_id,
                                                                 parse_mode=ParseMode.MARKDOWN).message_id
        data.asked_questionnaire[update.callback_query.message.chat.id] = True
    else:
        view_questionnaire(update, context)
        pass


def send_questionnaire(update: Update, context: ext.CallbackContext):
    data.delete_msg(update.callback_query.message.chat.id, context)
    ques = Db.get_instance().get_questions(update.callback_query.message.chat.id)
    for i in ques:
        msg = context.bot.send_poll(data.active_chats[update.callback_query.message.chat.id],
                                    f"{ques.index(i) + 1}) {i.strip()}",
                                    utils.OPTION_LIST, is_anonymous=False)
        data.active_polls[msg.poll.id] = (msg.message_id, i)
    data.active_commands[update.callback_query.message.chat.id] = context.bot.send_message(
        update.callback_query.message.chat.id, "``` Poll Sent Waiting for reply```",
        parse_mode=ParseMode.MARKDOWN).message_id


def handle_answers(update: Update, context: ext.CallbackContext):
    user_id = update.poll_answer.user.id
    poll_id = update.poll_answer.poll_id
    option = utils.OPTION_LIST[update.poll_answer.option_ids[0]]
    ques = data.active_polls.get(poll_id, None)
    if ques:
        context.bot.send_message(data.active_chats[user_id],
                                 f"""``` {ques[1].strip()} \n Anonymous User answered :- {option}```""",
                                 parse_mode=ParseMode.MARKDOWN)
        del data.active_polls[poll_id]
        context.bot.delete_message(user_id, ques[0])


def cancel(update: Update, context: ext.CallbackContext):
    if data.asked_questionnaire.get(update.message.chat.id, None):
        data.asked_questionnaire[update.message.chat.id] = False
        data.delete_msg(update.message.chat.id, context)
        data.active_commands[update.message.chat.id] = context.bot.send_message(
            text="""``` Questionnaire Operation Cancelled```""", chat_id=update.message.chat.id,
            parse_mode=ParseMode.MARKDOWN).message_id


def parse_questions(update: Update, context: ext.CallbackContext):
    data.delete_msg(update.message.chat.id, context)
    ques = update.message.text.strip().split('/')
    for i in range(len(ques)):
        if len(ques[i].strip()) == 0:
            ques.pop(i)
    Db.get_instance().add_questions(update.message.chat_id, ques)
    msg = "Entered Questions\n"
    for i in ques:
        msg += f"{ques.index(i) + 1} {i.strip()}\n"
    keyboard = [[InlineKeyboardButton("Edit Questionnaire", callback_data=utils.QUESTIONNAIRE_SET),
                 InlineKeyboardButton("<- Menu", callback_data=utils.MENU), ], ]
    data.active_commands[update.message.chat.id] = context.bot.send_message(text=f"```{msg}```",
                                                                            parse_mode=ParseMode.MARKDOWN,
                                                                            chat_id=update.message.chat_id,
                                                                            reply_markup=InlineKeyboardMarkup(
                                                                                keyboard)).message_id
    data.asked_questionnaire[update.message.chat.id] = False
