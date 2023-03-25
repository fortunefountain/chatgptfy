import openai
import os
import click
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Context, Message

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
HOME = os.environ.get("HOME")
CONTEXT_DB = "{}/.config/chatgptfy/context.db".format(HOME)
openai.api_key = OPENAI_API_KEY
GPT_MODEL = "gpt-3.5-turbo"

class Chatgptfy:
    def __init__(self):
        self.engine = create_engine("sqlite:///{}".format(CONTEXT_DB))

    def init_database(self):
        Base.metadata.create_all(self.engine)

    def add_context(self, session, context_title):
        context = Context(title=context_title)
        session.add(context)
        return context

    def get_context(self, session, context_title):
        context = session.query(Context).filter_by(title=context_title).first()
        return context

    def get_contexts(self, session):
        contexts = session.query(Context).all()
        return contexts

    def get_messages(self, context):
        return context.messages

    def add_message(self, session, context, content, role='user'):
        message = Message(role=role, content=content)
        context.messages = [message]
        session.add(context)

    def get_session(self):
        Session = sessionmaker(bind=self.engine)
        session = Session()
        return session

    def drop_database(self):
        Base.metadata.drop_all(self.engine)

    def send_question_to_chatgpt_api(
            self,
            messages,
            max_tokens=150,
            temprature=0.5
            ) -> Message:
        dict_messages = [{'role': message.role,
                          'content': message.content}
                         for message in messages]
        response = openai.ChatCompletion.create(
            model=GPT_MODEL,
            messages=dict_messages,
            max_tokens=max_tokens,
            n=1,
            temperature=temprature,
        )
        if (response):
            total_tokens = response['usage']['total_tokens']
            content = response['choices'][0]['message']['content']
            finish_reason = response['choices'][0]['finish_reason']
            message = Message(role='assistant',
                              content=content,
                              total_tokens=total_tokens,
                              finish_reason=finish_reason)
            return message
        else:
            raise Exception("No response from OpenAI API")


@click.command()
@click.option('--system', is_flag=True)
@click.option('--context', default='default', help='Context to use')
@click.option('--message', default='Hello', help='Message to send')
@click.option('--max-tokens', default=150, help='Max tokens to use')
@click.option('--temperature', default=0.5, help='Temperature to use')
@click.option('--list-contexts', help='List contexts')
@click.option('--list-messages', default='default', help='List messages for context')
@click.option('--init-db', is_flag=True)
@click.option('--drop-db', is_flag=True)
def main(system,
         context,
         message,
         max_tokens,
         temperature,
         list_contexts,
         list_messages,
         init_db,
         drop_db
         ):
    chatgptfy = Chatgptfy()
    user = 'user'
    if system:
        user = 'system'
    if init_db:
        chatgptfy.init_database()
        return
    if drop_db:
        chatgptfy.drop_database()
        return
    if list_contexts:
        session = chatgptfy.get_session()
        contexts = chatgptfy.get_contexts(session)
        for context in contexts:
            print(context.title)
        return
    if list_messages:
        session = chatgptfy.get_session()
        context = chatgptfy.get_context(session, list_messages)
        if context is None:
            print("No context found")
            return
        messages = chatgptfy.get_messages(context)
        for message in messages:
            print(message.role, message.content)
        return
    else:
        session = chatgptfy.get_session()
        context = chatgptfy.get_context(session, context)
        if not context:
            context = chatgptfy.add_context(session, "default")
        chatgptfy.add_message(session, context, message)
        messages = chatgptfy.get_messages(context)
        message = Message(role=user, content=message)
        messages.append(message)
        response = chatgptfy.send_question_to_chatgpt_api(
            messages,
            max_tokens=max_tokens,
            temprature=temperature
            )
        chatgptfy.add_message(session, message.context, message.role)
        chatgptfy.add_message(session,
                              context,
                              response.content,
                              role='assistant')
        session.commit()
        print(response.content)


if __name__ == "__main__":
    main()
