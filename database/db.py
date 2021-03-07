from configparser import ConfigParser

import pyrebase

from data import black_list, active_chats
from models.users import User


class Db:
    __instance = None
    __db: pyrebase.pyrebase.Database = None

    def __init__(self):
        config = ConfigParser()
        config.read('secrets.ini')
        self.firebaseConfig = dict(apiKey=config['FIREBASE']['apiKey'],
                                   authDomain=config['FIREBASE']['authDomain'],
                                   databaseURL=config['FIREBASE']['databaseURL'],
                                   projectId=config['FIREBASE']['projectId'],
                                   storageBucket=config['FIREBASE']['storageBucket'],
                                   messagingSenderId=config['FIREBASE']['messagingSenderId'],
                                   appId=config['FIREBASE']['appId'],
                                   measurementId=config['FIREBASE']['measurementId'])
        self.__db = pyrebase.initialize_app(self.firebaseConfig).database()

    @staticmethod
    def get_instance():
        if Db.__instance is None:
            Db.__instance = Db()
        return Db.__instance

    def get_db(self):
        return self.__db

    def add_user(self, user: User):
        data = user.json()
        del data['telId']
        self.__db.child('users').child(user.tel_id).set(data)

    def read_user_data(self, chat_id: int):
        data = self.__db.child('users').child(chat_id).get()
        if data.val():
            user = User(chat_id)
            data = data.val()
            user.make(data.get('name'), int(data.get('gender')), data.get('instagramId'), data.get('batch'))
            user.connected = int(data.get('k'))
            user.block = int(data.get('b'))
            user.date = int(data.get('t'))
            user.rec = int(data.get('rec'))
            return user
        return data.val()

    def read_users(self):
        data = self.__db.child('users').get()
        users = None
        if data.val():
            users = []
            for res in data.val():
                user = User(int(res))
                user.make(data.val()[res].get('name'), int(data.val()[res].get('gender')),
                          data.val()[res].get('instagramId'),
                          data.val()[res].get('batch'))
                user.block = int(data.val()[res].get('b'))
                user.connected = int(data.val()[res].get('k'))
                user.date = int(data.val()[res].get('t'))
                user.rec = int(data.val()[res].get('rec'))
                users.append(user)
        return users

    def add_interest(self, user_id, skills):
        self.__db.child('users').child(user_id).child('skills').set({i: skills[i] for i in range(len(skills))})

    def get_available_users(self):
        return self.__db.child('users').order_by_child('k').equal_to(0).get().val()

    @staticmethod
    def utils(datum, data):
        user = User(int(datum))
        user.make(data[datum].get('name'), int(data[datum].get('gender')), data[datum].get('instagramId'),
                  data[datum].get('batch'))
        user.block = int(data[datum].get('b'))
        user.connected = int(data[datum].get('k'))
        user.date = int(data[datum].get('t'))
        user.rec = int(data[datum].get('rec'))
        return user

    def read_available_users(self, chat_id, code):
        data = self.get_available_users()
        try:
            del data[str(chat_id)]
        except:
            pass
        res = []
        for i in data:
            if str(data[i].get('t')) != str(code):
                continue
            res.append(Db.utils(i, data))
        return res

    def read_users_with_gender(self, user: User):
        data = self.get_available_users()
        try:
            del data[str(user.tel_id)]
        except:
            pass
        res = []
        for i in data:
            if str(data[i].get('gender')) == str(user.rec) and str(data[i].get('rec')) == str(user.gender) and str(
                    data[i].get('t') == str(user.date)):
                res.append(Db.utils(i, data))
        return res

    def update_user_status(self, chat_id, code):
        self.__db.child('users').child(chat_id).child('k').set(code)

    def get_interests(self, chat_id):
        data = self.__db.child('users').child(chat_id).child('skills').get()
        data = data.val()
        res = set(data)
        return res

    def get_common_interests(self, user_1, user_2):
        user1 = self.get_interests(user_1)
        user2 = self.get_interests(user_2)
        return user1, user2

    def update_block(self, chat_id):
        block = int(self.__db.child('users').child(chat_id).child('b').get().val())
        block += 1
        self.__db.child('users').child(chat_id).child('b').set(block)
        if block == 5:
            black_list.append(chat_id)

    def change_mode(self, chat_id, mode):
        self.__db.child('users').child(chat_id).child('t').set(mode)

    def create_black_list(self):
        data = self.read_users()
        if data:
            for i in data:
                if i.block > 4:
                    black_list.append(i.tel_id)
        data = self.__db.child('chats').get().each()
        active_chats.clear()
        if data:
            for i in data:
                active_chats[int(i.key())] = i.val()

    def is_interest_chosed(self, chat_id):
        data = self.__db.child('users').child(chat_id).child('skills').get()
        print(data.val())
        if data.val():
            return False
        return True

    def update_user(self, user: User):
        self.__db.child('users').child(user.tel_id).child('gender').set(user.gender)
        self.__db.child('users').child(user.tel_id).child('rec').set(user.rec)

    def save(self):
        self.__db.child('chats').set(active_chats)

    def get_questions(self, chat_id):
        data = self.__db.child('users').child(chat_id).child('questionnaire').get().val()
        if data:
            return data
        return None

    def add_questions(self, chat_id, questions):
        if len(questions) != 0:
            self.__db.child('users').child(chat_id).child('questionnaire').set(
                {i: questions[i] for i in range(len(questions))})

    def add_slug(self, chat_id, slug):
        self.__db.child('slugs').child(chat_id).set(slug)

    def get_slug(self, chat_id):
        return self.__db.child('slugs').child(chat_id).get().val()
