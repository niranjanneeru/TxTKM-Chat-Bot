import json

from telegram import Update

import utils
from data import active_chats
from database.db import Db


def get_user_id(update, context):
    update.message.reply_markdown(f'``` Tel Id:- {update.message.chat.id}```')


def store(update, context):
    if update.message.chat.id == utils.DEV_ID:
        Db.get_instance().save()


def reveal(update, context):
    if update.message.chat.id in utils.ADMIN_IDs:
        user_id = active_chats.get(update.message.chat.id)
        if user_id:
            user = Db.get_instance().read_user_data(user_id)
            if user:
                update.message.reply_text(user.json())
                msg = Db.get_instance().get_slug(user.tel_id)
                update.message.reply_text(json.dumps(json.loads(msg), indent=4, sort_keys=True))


def users(update, context):
    if update.message.chat.id != utils.DEV_ID:
        return
    data = Db.get_instance().read_users()
    msg = ''
    for i in data:
        msg += f'{str(i.tel_id)} {str(i.json())}\n'
    n = len(msg)
    j = 0
    while j < n:
        update.message.reply_text(msg[j:4000 + j])
        j += 4000


def search(update: Update, context):
    if update.message.chat.id != utils.DEV_ID:
        return
    res = update.message.text.strip().split(' ')
    if len(res) == 2:
        res = int(res[1].strip())
        msg = Db.get_instance().get_slug(res)
        update.message.reply_text(json.dumps(json.loads(msg), indent=4, sort_keys=True))
