from sqlalchemy import create_engine
from sqlalchemy import MetaData
from sqlalchemy import Table
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import ForeignKey
import os

HOME = os.environ['HOME']

# create directory if it doesn't exist
if not os.path.exists('%s/.config/chatgptfy' % HOME):
    os.makedirs('%s/.config/chatgptfy' % HOME)

engine = create_engine(
            'sqlite:///%s/.config/chatgptfy/chatgptfy.db' % HOME,
            echo=False
        )

metadata = MetaData()


chatgpt_session = Table(
        'chatgpt_session',
        metadata,
        Column('id', Integer, primary_key=True),
    )

message = Table(
        'message',
        metadata,
        Column('id', Integer, primary_key=True),
        Column('role', String(50)),
        Column('message', String(50)),
        Column('timestamp', String(50)),
        Column('chatgpt_session_id', Integer, ForeignKey('chatgpt_session.id')),
    )

metadata.create_all(engine)
