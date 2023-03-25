import openai
import os
import click
import csv
import sys
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Context, Message, Template

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
        session.commit()
        context = Context(title=context_title)
        return context

    def get_context(self, session, context_title):
        context = session.query(Context).filter_by(title=context_title).first()
        return context

    def get_contexts(self, session):
        contexts = session.query(Context).all()
        return contexts

    def get_messages(self, context):
        return context.messages

    def get_message_from_template(self, session, template_name):
        template = session.query(Template).filter_by(template_name=template_name).first()
        if template is None:
            raise Exception("Template not found")
        message = Message(role='system', content=template.content)
        return message

    def list_templates(self, session):
        templates = session.query(Template).all()
        for template in templates:
            print("{}: {}\n".format(template.template_name, template.content))
        return templates

    def load_templates(self, session):
        url = "https://raw.githubusercontent.com/f/awesome-chatgpt-prompts/main/prompts.csv"
        response = requests.get(url)
        if response.status_code == 200:
            lines = response.text.splitlines()
            reader = csv.reader(lines)
            for row in reader:
                template = Template(template_name=row[0], content=row[1])
                session.add(template)
            session.commit()

    def add_message(self, session, context, message):
        context.messages.append(message)
        session.add(context)
        session.commit()

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
@click.option('--template', help="Message from template")
@click.option('--list-templates',
              is_flag=True,
              help="List templates")
@click.option('--load-templates',
              is_flag=True,
              help="Load templates"
              " from awesome-chatgpt-prompts")
@click.option('--context-name', help='Context to use')
@click.option('--message', help='Message to send')
@click.option('--max-tokens', default=150, help='Max tokens to use')
@click.option('--temperature', default=0.5, help='Temperature to use')
@click.option('--list-contexts', is_flag=True, help='List contexts')
@click.option('--list-messages', help='List messages for context')
@click.option('--delete-context', help="Delete context")
@click.option('--init-db', is_flag=True)
@click.option('--drop-db', is_flag=True)
def main(system,
         template,
         list_templates,
         load_templates,
         context_name,
         message,
         max_tokens,
         temperature,
         list_contexts,
         list_messages,
         delete_context,
         init_db,
         drop_db
         ):
    chatgptfy = Chatgptfy()
    user = 'user'
    session = chatgptfy.get_session()

    if system:
        user = 'system'
    if init_db:
        chatgptfy.init_database()
        return
    if drop_db:
        chatgptfy.drop_database()
        return
    if load_templates:
        chatgptfy.load_templates(session)
        return
    if list_templates:
        chatgptfy.list_templates(session)
        return
    if list_contexts:
        contexts = chatgptfy.get_contexts(session)
        for context in contexts:
            print(context.title)
        return
    if list_messages:
        session = chatgptfy.get_session()
        context = chatgptfy.get_context(session, list_messages)
        if context is None:
            raise Exception("Context not found")
        messages = chatgptfy.get_messages(context)
        for message in messages:
            print("{}: {}".format(message.role, message.content))
        return
    if delete_context:
        session = chatgptfy.get_session()
        context = chatgptfy.get_context(session, delete_context)
        if context is None:
            raise Exception("Context not found")
        session.delete(context)
        session.commit()
        return
    if sys.stdin.isatty() and not message:
        print("Enter your question: ")
        message = input()
    elif message:
        message = message
    else:
        message = input()
    try:
        session = chatgptfy.get_session()
        context = None
        if context_name is None:
            context_name = "default"
            context = chatgptfy.get_context(session, context_name)
            if context is None:
                context = chatgptfy.add_context(session, context_name)
                session.commit()
        else:
            context = chatgptfy.get_context(session, context_name)
            if context is None:
                context = chatgptfy.add_context(session, context_name)
        messages = chatgptfy.get_messages(context)
        message_obj = None
        if template is not None:
            message_obj = chatgptfy.get_message_from_template(session, template)
            context.messages.append(message_obj)
        else:
            message_obj = Message(role=user, content=message)
        messages.append(message_obj)
        response = chatgptfy.send_question_to_chatgpt_api(
            messages,
            max_tokens=max_tokens,
            temprature=temperature
            )
        chatgptfy.add_message(session,
                              context,
                              message_obj)
        chatgptfy.add_message(session,
                              context,
                              response)
        print(response.content)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()
