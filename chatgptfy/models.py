from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class Context(Base):
    __tablename__ = 'context'
    id = Column(Integer, primary_key=True)
    messages = relationship('Message', back_populates='context')
    title = Column(String(50))

    def __repr__(self):
        return f'Context(id={self.id})'


class Message(Base):
    __tablename__ = 'message'
    id = Column(Integer, primary_key=True)
    role = Column(String(50))
    content = Column(String(4096))
    timestamp = Column(String(50))
    total_tokens = Column(Integer)
    finish_reason = Column(String(50))
    context_id = Column(Integer, ForeignKey('context.id'))
    context = relationship('Context', back_populates='messages')

    def __repr__(self):
        return f"""
                 Message(
                    id={self.id},
                    role={self.role},
                    content={self.message},
                    timestamp={self.timestamp},
                    context_id={self.context_id}
                 )
               """


class Template(Base):
    __tablename__ = 'template'
    id = Column(Integer, primary_key=True)
    template_name = Column(String(50))
    content = Column(String(4096))
