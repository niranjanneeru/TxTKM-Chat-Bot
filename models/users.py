from utils import PLACEHOLDER


class User:
    GENDER = {
        -1: "She/Her",
        0: "Prefer Not To Say",
        1: "He/Him"
    }
    DATE = {
        -1: "Date",
        1: "Friends",
        0: "Not Selected"
    }
    name: str = PLACEHOLDER
    instagram_id: str = PLACEHOLDER
    batch: str = PLACEHOLDER

    gender: int = 0
    rec: int = 0
    connected: int = 0
    block: int = 0
    date: int = 0

    def __init__(self, tel_id: int) -> None:
        self.tel_id: int = tel_id
        self.askedName = True
        self.askedGender = True
        self.askedId = True
        self.askedBatch = True
        self.askedSkill = True
        self.askedRec = False

    def set_name(self, name: str) -> None:
        self.name = name

    def set_gender(self, gender: int) -> None:
        self.gender = gender

    def set_id(self, inst_id: str) -> None:
        self.instagram_id = inst_id

    def set_batch(self, batch: str) -> None:
        self.batch = batch

    def make(self, name: str, gender: int, insta_id: str, batch: str):
        self.set_id(insta_id)
        self.set_name(name)
        self.set_gender(gender)
        self.set_batch(batch)

    def json(self):
        return dict(telId=self.tel_id, name=self.name, instagramId=self.instagram_id, gender=self.gender,
                    batch=self.batch, b=self.block, k=self.connected, t=self.date, rec=self.rec)

    def __str__(self):
        return self.name
