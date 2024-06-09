from flask import Flask, render_template, request, redirect, url_for, jsonify
# import os
# from sqlalchemy.ext.mutable import MutableDict
# from sqlalchemy.exc import NoResultFound
# from transformers import pipeline
# import fitz  # PyMuPDF
import secrets
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.dialects.postgresql import JSON
from datetime import datetime
import json
# from open_ai_chat import Solvrzchatbot
# from open_ai_direct_chat import main
import hashlib
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from werkzeug.security import check_password_hash
from langchain.prompts import PromptTemplate
# import fitz  # PyMuPDF
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1234@localhost/WEBCHAT'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from langchain.chat_models import ChatOpenAI

from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)
from dotenv import load_dotenv
import os
import PyPDF2
import pickle

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        text = ''
        for page_num in range(len(reader.pages)):
            text += reader.pages[page_num].extract_text()
    return text

msg_history = b''
load_dotenv()


def process_msg2(user_input, path, user):

    load_dotenv()
    pdf_path = path
    pdf_text = extract_text_from_pdf(pdf_path)

    # template = """You are a Helpful AI Assistant for Solvrz. You will act as you are the following texts.
    #
    #             """+pdf_text
    template = PromptTemplate.from_template(
        """You are a Helpful AI Assistant for Solvrz. You will act as you are the following texts.
                """+pdf_text
    )

    PROMPT = PromptTemplate.from_template(template)

    llm = ChatOpenAI(temperature=0.9)
    prev_msg = user.msg_history

    print(len(prev_msg))
    if len(prev_msg) == 0:
        conversation = ConversationChain(
            prompt=PROMPT,
            llm=llm,
            verbose=False,
            memory=ConversationBufferMemory()
        )
    # https://stackoverflow.com/questions/75965605/how-to-persist-langchain-conversation-memory-save-and-load
    # Solution link Stack OVerflow is goat
    else :
        conversation = ConversationChain(
            prompt=PROMPT,
            llm=llm,
            verbose=False,
            memory=pickle.loads(prev_msg)
        )

    ai_response = conversation.predict(input=user_input)
    pickled_str = pickle.dumps(conversation.memory)
    user.msg_history = pickled_str
    db.session.commit()
    return ai_response



def process_msg(user_input, path, user, prompt):
    load_dotenv()
    pdf_path = path
    pdf_text = extract_text_from_pdf(pdf_path)

    chat = ChatOpenAI(temperature=0.9)

    sys_msg = "Behave like that : "+prompt+".And Follow these following texts as an external knowledge source "+pdf_text


    prev_msg = user.msg_history

    if len(prev_msg) <= 1:
        msg = [SystemMessage(content=sys_msg), ]
        msg.append(HumanMessage(content=user_input))
        assistant_response = chat(msg)
        msg.append(AIMessage(content=assistant_response.content))
        pickled_str = pickle.dumps(msg)
        user.msg_history = pickled_str
        db.session.commit()
        return assistant_response.content

    else :
        msg = pickle.loads(prev_msg)
        msg.append(HumanMessage(content=user_input))
        assistant_response = chat(msg)
        msg.append(AIMessage(content=assistant_response.content))
        pickled_str = pickle.dumps(msg)
        user.msg_history = pickled_str
        db.session.commit()
        return assistant_response.content


class OrganizationInfo(db.Model):
    __tablename__ = 'OrganizationInfo'
    id = db.Column(db.Integer, primary_key=True)
    org_name = db.Column(db.Text)
    org_api = db.Column(db.Text)
    org_prompt = db.Column(db.Text)
    org_msg_limit = db.Column(db.Integer)
    org_monthly_limit = db.Column(db.Integer)
    org_started_date = db.Column(db.Date)
    org_expired_date = db.Column(db.Date)
    org_msg_counter = db.Column(db.Integer)
    org_status = db.Column(db.Text)
    org_pdf_1 = db.Column(db.Text)
    org_pdf_2 = db.Column(db.Text)


    def __init__(self, org_name, org_prompt, org_api, org_msg_limit, org_monthly_limit, org_started_date, org_expired_date, org_msg_counter, org_status, org_pdf_1, org_pdf_2):
        self.org_name = org_name
        self.org_prompt = org_prompt
        self.org_api = org_api
        self.org_msg_limit = org_msg_limit
        self.org_monthly_limit = org_monthly_limit
        self.org_started_date = org_started_date
        self.org_expired_date = org_expired_date
        self.org_msg_counter = org_msg_counter
        self.org_status = org_status
        self.org_pdf_1 = org_pdf_1
        self.org_pdf_2 = org_pdf_2



class UserInfo(db.Model):
    __tablename__ = 'UserInfo'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text)
    user_org = db.Column(db.Text)
    user_email = db.Column(db.Text)
    user_password = db.Column(db.Text)
    org_api_key = db.Column(db.Text)
    user_api_key = db.Column(db.Text)
    msg_history = db.Column(db.LargeBinary)
    # Adding a name field
    # msg_history = db.Column(db.JSON)
    def __init__(self, username, user_org, user_email, user_password, org_api_key, user_api_key, msg_history):
        self.username = username
        self.user_org = user_org
        self.user_email = user_email
        self.user_password = user_password
        self.org_api_key = org_api_key
        self.user_api_key = user_api_key
        # self.msg_history = json.dumps(msg_history)
        self.msg_history = msg_history

# Set the upload folder for the PDFs
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return "Hello World"

@app.route('/add_org')
def add_org():
    return render_template('Add_organization.html')


@app.route("/get_organization_names", methods=["GET"])
def get_organization_names():
    organizations = OrganizationInfo.query.with_entities(OrganizationInfo.org_name).all()
    organization_names = [org.org_name for org in organizations]
    return jsonify(organization_names), 200



# Need to send the previous History too
@app.route('/User_login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    user = UserInfo.query.filter_by(user_email=email, user_password=password).first()

    if user:
        response_data = {
            "success": True,
            "org_api_key": user.org_api_key,
            "user_api_key": user.user_api_key,
            "user_name": user.username
        }
    else:
        response_data = {
            "success": False,
            "message": "Invalid credentials"
        }

    return jsonify(response_data)



@app.route("/user_register", methods=["POST"])
def user_register():
    data = request.json
    username = data.get("username")
    user_org = data.get("user_org")
    user_email = data.get("user_email")
    user_password = data.get("user_password")

    if not username or not user_org or not user_email or not user_password:
        return jsonify({"message": "All fields are required"}), 400

    # user api key
    user_api = generate_api_key()
    organization = OrganizationInfo.query.filter_by(org_name=user_org).first()
    org_api_key = organization.org_api
    new_user = UserInfo(
        username=username,
        user_org=user_org,
        user_email=user_email,
        user_password=user_password,
        org_api_key=org_api_key,
        user_api_key=user_api,
        msg_history=msg_history
    )

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "User added successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to add user", "error": str(e)}), 500

@app.route('/organization_list')
def org_list():
    organizations = OrganizationInfo.query.all()
    # Convert the organization data to a list of dictionaries
    organization_data = [{
        'org_name': org.org_name,
        'org_prompt': org.org_prompt,
        'org_api': org.org_api,
        'org_msg_limit': org.org_msg_limit,
        'org_monthly_limit': org.org_monthly_limit,
        'org_started_date': str(org.org_started_date),
        'org_expired_date': str(org.org_expired_date),
        'org_msg_counter': org.org_msg_counter,
        'org_status': org.org_status,
        'org_pdf_1': org.org_pdf_1,
        'org_pdf_2': org.org_pdf_2
    } for org in organizations]
    # Return the organization data as JSON
    return jsonify(organization_data)

@app.route('/user_list')
def user_list():
    users = UserInfo.query.all()

    user_msg_history = users.msg_history
    msg = pickle.loads(user_msg_history)
    user_data = [{
        'username': user.username,
        'user_org': user.user_org,
        'user_email': user.user_email,
        'org_api_key': user.org_api_key,
        # 'msg_history': msg
    } for user in users]

    # Return the user data as JSON
    return jsonify(user_data)



def generate_api_key():
    return secrets.token_hex(16)  # Change 16 to the desired key length in bytes


@app.route('/org_register', methods=['POST'])
def submit_form():
    # Get form data
    org_name = request.form['company_name']
    org_prompt = request.form['company_prompt']
    msg_limit = int(request.form['msg_limit'])
    monthly_limit = int(request.form['monthly_limit'])
    started_date = request.form['started_date']
    expired_date = request.form['expired_date']

    # Checking if expired or not
    expired_date = datetime.strptime(expired_date, '%Y-%m-%d').date()
    current_date = datetime.now().date()
    if current_date < expired_date:
        org_status = "Active"
    else:
        org_status = "Disabled"

    # Check if organization already exists
    org = OrganizationInfo.query.filter_by(org_name=org_name).first()
    if org:
        return jsonify({"answer": "Your Organization is already registered"})

    # Generate API-Key
    org_api = generate_api_key()
    # Create a folder for the organization to save uploaded PDFs
    org_folder_path = os.path.join(app.config['UPLOAD_FOLDER'], org_name)
    os.makedirs(org_folder_path, exist_ok=True)

    # Save the uploaded PDFs to the organization's folder
    org_pdf_1_path = None
    org_pdf_2_path = None
    if 'org_pdf1' in request.files:
        pdf_file_1 = request.files['org_pdf1']
        if pdf_file_1.filename:
            filename_1 = "Common.pdf"  # You can set a common name for the first PDF
            org_pdf_1_path = os.path.join(org_folder_path, filename_1)
            pdf_file_1.save(org_pdf_1_path)

    if 'org_pdf2' in request.files:
        pdf_file_2 = request.files['org_pdf2']
        if pdf_file_2.filename:
            filename_2 = "Classified.pdf"  # You can set a common name for the second PDF
            org_pdf_2_path = os.path.join(org_folder_path, filename_2)
            pdf_file_2.save(org_pdf_2_path)

    # Save the organization to the database
    org_entry = OrganizationInfo(
        org_name=org_name,
        org_prompt=org_prompt,
        org_api=org_api,
        org_msg_limit=msg_limit,
        org_monthly_limit=monthly_limit,
        org_started_date=started_date,
        org_expired_date=expired_date,
        org_msg_counter=0,
        org_status=org_status,
        org_pdf_1=org_pdf_1_path,
        org_pdf_2=org_pdf_2_path,
    )
    db.session.add(org_entry)
    db.session.commit()

    return jsonify({"answer": "Organization Added successfully"})

import Solvrz
# Only for Solvrz
@app.route("/solvrz_web_chat", methods=["POST"])
def get_answer_for_solvrz():
    if not request.json or "user_question" not in request.json:
        return jsonify({"error": "Invalid request format or missing 'user_question' key"}), 400

    session_id = request.headers.get('SESSION-ID', '')
    user_question = request.json["user_question"]

    answer = Solvrz.Solvrzchatbot(user_question, session_id)

    return jsonify({"answer": answer})

# Getting answers using API header
@app.route("/get_answer/company/using_header", methods=["POST"])
def get_answer():

    if not request.json or "user_question" not in request.json:
        return jsonify({"error": "Invalid request format or missing 'user_question' key"}), 400


    orgz_api_key = request.headers.get('ORG-API-Key', '')
    usrz_api_key = request.headers.get('USER-API-Key', '')

    user_question = request.json["user_question"]
    organization = OrganizationInfo.query.filter_by(org_api=orgz_api_key).first()
    prompt = organization.org_prompt
    counter = organization.org_msg_counter

    current_date = datetime.now().date()
    if current_date > organization.org_expired_date:
        org_status = "Disabled"
        organization.org_status = org_status
        db.session.commit()
        return jsonify({"answer": "Your Time is expired"})

    org_msg_lim = organization.org_msg_limit
    if org_msg_lim > counter:
        path = f"uploads/{organization.org_name}/Classified.pdf"
        user = UserInfo.query.filter_by(user_api_key=usrz_api_key).first()
        answer = process_msg(user_question, path, user, prompt)



        if user:
            counter = counter + 1
            # user.msg_history = updated_msg_history
            organization.org_msg_counter = counter
            db.session.commit()
            return jsonify({"answer": answer})


    else :
        organization.org_status = "Deactivated"
        return jsonify({"answer": "Your Message Limit is Over"})


import charpent_db_controller
# New Charpent FROM SEPTEMBER
@app.route("/chirpent_user_register", methods=["POST"])
def chirpent_user_register():
    data = request.json

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    phone = data.get("phone")
    user_api = generate_api_key()

    if not username or not email or not password or not phone:
        return jsonify({"message": "All fields are required"}), 400

    isok = charpent_db_controller.insert_chirpent_user(username, email, password, phone, user_api)

    if isok == "OK":
        return jsonify({"answer": "User registered Successfully"})
    else :
        return jsonify({"answer": "User is registered"})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()



    # if check_password_hash(user.user_password, password):
    #     return jsonify({"success": True, "message": "Login successful", "org_api_key": user.org_api_key}), 200
    #
    # else:
    #     return jsonify({"success": False, "message": "Invalid credentials"}), 401

    # def generate_api_header(api_key, form_data):
    #     # Create an API header using some hashing algorithm (e.g., SHA256)
    #     data_str = ''.join(sorted(form_data))  # Concatenate form data and sort it to ensure consistent ordering
    #     signature = hashlib.sha256(f"{data_str}{api_key}".encode()).hexdigest()
    #     return signature

    # print(organization.org_msg_limit < counter)
    #
    # print(user_question)
    # print(api_key)
    # return jsonify({"answer" : f"{user_question}"})
    # Query the database to check if the API-Header matches
    # organization = OrganizationInfo.query.filter_by(org_api=api_key).first()
    # # organization = OrganizationInfo.query.filter_by(
    # #     org_header=json.dumps({'API-Key': api_key, 'API-Header': api_header})).first()
    #
    # print(organization)
    # if organization:
    #     org_name = organization.org_name
    #     print(org_name)
    #     user_question = request.json["user_question"]
    #     pdf_text = load_pdf_text(f"uploads/company_{api_key}.pdf")  # Use api_key instead of api_header here
    #     answer = chatbot({"question": user_question, "context": pdf_text})
    #     msg_history.append({"role": "user", "content": f"{user_question}"})
    #     msg_history.append({"role": "bot", "content": f"{answer}"})
    #
    #     user_name = "Mehrab"
    #     user = UserInfo.query.filter_by(username=user_name).first()
    #     if user and organization:
    #         session_id = user.session_id
    #         previous_msg = json.dumps(msg_history)
    #         user_entry = UserInfo(session_id=session_id, msg_history=previous_msg, username=user_name, user_org=org_name)
    #         db.session.add(user_entry)
    #         db.session.commit()
    #         return jsonify({"answer": answer["answer"]})
    #     else:
    #         session_id = "1234"
    #         previous_msg = json.dumps(msg_history)
    #         user_entry = UserInfo(session_id=session_id, msg_history=previous_msg, username=user_name, user_org=org_name)
    #         db.session.add(user_entry)
    #         db.session.commit()
    #         return jsonify({"answer": answer["answer"]})
    #
    # else:
    #     # The organization with the provided API key and API header does not exist or is invalid
    #     # Set a default value for org_name to handle this case
    #     org_name = "Unknown Organization"
    #     return jsonify({"answer": "Unknown Org"})

# OLD SUBMIT
# @app.route('/submit', methods=['POST'])
# def submit_form():
#     # Get form data
#     org_name = request.form['company_name']
#     org_prompt = request.form['company_prompt']
#     print(org_name)
#     print(org_prompt)
#     # Generate a unique API key (token) for this form submission
#     api_key = generate_api_key()
#
#     # Generate the API header using the API key and form data
#     api_header = generate_api_header(api_key, request.form)
#
#     # Include the API key in the request headers
#     headers = {'API-Key': api_key, 'API-Header': api_header}
#     # api_key = secrets.token_hex(16)  # Change 16 to the desired key length in bytes
#     # Get the uploaded PDF file
#     pdf_file = request.files['pdf_file']
#     print(f"Company Name: {org_name}")
#     print(f"Company Prompt: {org_prompt}")
#     print(f"API Key: {api_key}")
#     print(f"headers: {headers}")
#     org = OrganizationInfo.query.filter_by(org_name=org_name).first()
#     # org = 1
#     if org:
#         return jsonify({"answer": "Your Organization is already registered"})
#     else:
#         # Save the uploaded PDF to the 'uploads' folder
#         if pdf_file:
#             # Change the filename to include the company name and API key
#             filename = f"company_{api_header}.pdf"
#             pdf_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
#         org_entry = OrganizationInfo(org_name=org_name, org_prompt=org_prompt, org_api=api_key, org_header=headers)
#         db.session.add(org_entry)
#         db.session.commit()
#         return jsonify({"answer": "Organization Added successfully"})
#
#     # Process the data or perform any other actions here.
#     # For this example, we'll just print the data.
#
#
#     return redirect(url_for('index', 'Org added successfully'))



# @app.route('/submitMulti', methods=['POST'])
# def upload_files():
#     if request.method == 'POST':
#         files = request.files.getlist('file')
#         for file in files:
#             file.save(os.path.join('uploads', file.filename))
#         return jsonify({'message': 'Files uploaded successfully.'})


# @app.route('/api/company/<string:company_name>', methods=['GET'])
# def get_company(company_name):
#     # Process the data or perform any other actions here.
#     # For this example, we'll just return a JSON response with the company name.
#     response = {'message': f'Company Name: {company_name}'}
#     return jsonify(response)
#     #calling apis through this ::: http://127.0.0.1:5000/api/company/Solvrz
#




# Passing usin URL
# @app.route("/get_answer/company/<string:api_key>", methods=["POST"])
# def get_answer(api_key):
#     # Validate the API key before processing the request
#     # For example, you can check if the API key exists in a database or a dictionary of valid keys.
#
#
#
#     if not request.json or "user_question" not in request.json:
#         return jsonify({"error": "Invalid request format or missing 'user_question' key"}), 400
#
#
#
#     user_question = request.json["user_question"]
#     pdf_text = load_pdf_text(f"uploads/company_{api_key}.pdf")
#     answer = chatbot({"question": user_question, "context": pdf_text})
#     msg_history.append({"role": "user", "content": f"{user_question}"})
#     msg_history.append({"role": "bot", "content": f"{answer}"})
#     user_name = "Mehrab"
#     user = UserInfo.query.filter_by(username=user_name).first()
#     if user:
#         session_id = user.session_id
#         previous_msg = json.dumps(msg_history)
#         user_entry = UserInfo(session_id=session_id, msg_history=previous_msg, username=user_name, user_org="Solvrz")
#         db.session.add(user_entry)
#         db.session.commit()
#         return jsonify({"answer": answer["answer"]})
#     else :
#         session_id = "1234"
#         previous_msg = json.dumps(msg_history)
#         user_entry = UserInfo(session_id=session_id, msg_history=previous_msg, username=user_name, user_org="Solvrz")
#         db.session.add(user_entry)
#         db.session.commit()
#         return jsonify({"answer": answer["answer"]})

# Define the base URL of your Flask web app

# Streamlit Part---------
# import requests
#
# BASE_URL = "http://127.0.0.1:5000"  # Replace with the actual URL of your Flask app
#
# # Define the endpoints of your Flask web app
# ENDPOINTS = {
#     "index": "/",
#     "add_org": "/add_org",
#     "organization_list": "/organization_list",
#     "user_list": "/user_list",
# }
#
# def make_request(endpoint):
#     url = BASE_URL + endpoint
#     response = requests.get(url)
#     return response.json()
#
# def run_streamlit():
#     st.title("Preview of Flask Web App")
#
#     # Create a sidebar menu to navigate through the pages of your Flask app
#     page = st.sidebar.selectbox("Select a page", list(ENDPOINTS.keys()))
#
#     # Make API requests to your Flask app based on the selected page
#     if page == "index":
#         st.write("Home Page")
#         response = make_request(ENDPOINTS[page])
#         st.write("Response:", response)
#
#     elif page == "add_org":
#         st.write("Add Organization Page")
#         response = make_request(ENDPOINTS[page])
#         st.write("Response:", response)
#
#     elif page == "organization_list":
#         st.write("Organization List Page")
#         response = make_request(ENDPOINTS[page])
#         st.write("Response:", response)
#
#     elif page == "user_list":
#         st.write("User List Page")
#         response = make_request(ENDPOINTS[page])
#         st.write("Response:", response)
#Streamlit Part




# @app.route("/get_answer/company/<string:company_name>", methods=["POST"])
# def get_answer(company_name):
#     if not request.json or "user_question" not in request.json:
#         return jsonify({"error": "Invalid request format or missing 'user_question' key"}), 400
#
#     user_question = request.json["user_question"]
#     pdf_text = load_pdf_text(f"uploads/{company_name}.pdf")
#     answer = chatbot({"question": user_question, "context": pdf_text})
#     return jsonify({"answer": answer["answer"]})

    # if not request.json or "user_question" not in request.json:
    #     return jsonify({"error": "Invalid request format or missing 'user_question' key"}), 400
    # print(company_name)
    # pdf_path = (f"uploads/{company_name}.pdf")
    # user_question = request.json["user_question"]
    # answer = chat_with_pdf(pdf_path, user_question)
    # # answer = chat_with_pdf({"question": user_question, "context": pdf_text})
    # return jsonify({"answer": answer["answer"]})
# @app.route("/get_answer", methods=["POST"])
# def get_answer():
#     user_question = request.json["user_question"]
#     pdf_path = "website_data.pdf"
#     answer = chat_with_pdf(pdf_path, user_question)
#     return jsonify({"answer": answer})


# # Testing the headers:::
# @app.route('/your_endpoint', methods=['POST'])
# def your_endpoint():
#     # Retrieve the API key and API header from the request headers
#     api_key = request.headers.get('X-API-Key')
#     api_header = request.headers.get('X-API-Header')
#
#     # Verify the authenticity and integrity of the data using the API key and API header
#     # ...
#     print(api_header)
#     print(api_key)
#     # Process the request data as needed
#     # ...
#     return "Your response"
