from dotenv import load_dotenv
import os
import PyPDF2
import pickle
from langchain.chat_models import ChatOpenAI
import re
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)
import dbcon
import dbcon2

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        text = ''
        for page_num in range(len(reader.pages)):
            text += reader.pages[page_num].extract_text()
    return text


def Solvrzchatbot(user_message, session_id):
    load_dotenv()
    pdf_path = "Solvrz_webchat.pdf"
    pdf_text = extract_text_from_pdf(pdf_path)

    dbcon.update_user_id(session_id)
    text = user_message
    numbers = re.findall(r'\d{9,}', text)
    if numbers:
        dbcon.update_phone(numbers, session_id)

    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b', text)
    if emails:
        dbcon.update_email(emails, session_id)

    chat = ChatOpenAI(temperature=0.9)
    sys_msg = "Behave like that : " + ".And Follow these following texts as an external knowledge source " + pdf_text

    user_data = dbcon2.get_user_data(session_id)
    if user_data == None :
        msg = [SystemMessage(content=sys_msg), ]
        msg.append(HumanMessage(content=user_message))
        assistant_response = chat(msg)
        msg.append(AIMessage(content=assistant_response.content))
        pickled_str = pickle.dumps(msg)
        dbcon2.insert_user_message(session_id, pickled_str)
        return assistant_response.content
    else :
        if user_message == "cls":
            dbcon2.delete_user_data(session_id)
            return "Your Message History is cleared 😊"
        else :
            prev_msg = user_data["msg_history"]
            msg = pickle.loads(prev_msg)
            msg.append(HumanMessage(content=user_message))
            assistant_response = chat(msg)
            msg.append(AIMessage(content=assistant_response.content))
            print(msg)
            human_messages_content = [message.content for message in msg if isinstance(message, HumanMessage)]

            dbcon.update_msg(human_messages_content, session_id)

            pickled_str = pickle.dumps(msg)
            dbcon2.update_msg_history(session_id, pickled_str)
            return assistant_response.content
