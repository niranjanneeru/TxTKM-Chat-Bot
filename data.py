active_commands = {}
current_list_users = {}
active_requests = {}
active_chats = {}
black_list = []
active_reveals = {}


def delete_msg(chat_id, context):
    global active_commands
    if chat_id:
        msg_id = active_commands.get(chat_id, None)
        if msg_id:
            context.bot.delete_message(chat_id, msg_id)
            active_commands[chat_id] = None


asked_questionnaire = {}

active_polls = {}
