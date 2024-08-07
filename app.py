from flask import Flask, session, request, jsonify
from flask_cors import CORS
import os
import requests
import json
from dotenv import load_dotenv

app = Flask(__name__)
app.secret_key = b'\xac\xfe/\xa2\xf9y\xcc\x8d\x87,\x94\xacs\xe3u\xf7L;\xa8h2\xf6}'  # Ensure the secret key is correctly set

# Configure CORS to handle credentials
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = False
app.config['CORS_HEADERS'] = 'Content-Type'

project_folder = os.path.dirname(__file__)
load_dotenv(os.path.join(project_folder, '.env'))

api_base = os.getenv("API_BASE")
deployment_id = os.getenv("DEPLOYMENT_ID")
api_key = os.getenv("API_KEY")
cognitive_search_endpoint = os.getenv("COGNITIVE_SEARCH_ENDPOINT")
cognitive_search_key = os.getenv("COGNITIVE_SEARCH_KEY")
cognitive_search_index_name = os.getenv("COGNITIVE_SEARCH_INDEX_NAME")
OPENAI_URL = f"{api_base}/openai/deployments/{deployment_id}/extensions/chat/completions?api-version=2023-06-01-preview"

@app.route("/")
def home():
    return "<center><h1>Flask App deployment on AZURE</h1></center>"

@app.route('/input')
def index():
    if 'username' in session and 'email' in session:
        username = session['username']
        email = session['email']
        return f'Logged in as {username} with email {email}'
    return 'You are not logged in'

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()  # This will parse the JSON data from the request
        if data:
            username1=data.get('username')
            session['username'] = data.get('username')
            session['email'] = data.get('email')
            print(f"Session Data: {session}")
            print(f"Username: {session.get('username')}") 
            return jsonify({'message': 'Login successful','username': username1})
        else:
            return jsonify({'message': 'Invalid request data'}), 400
    return jsonify({'message': 'Invalid method'}), 405

@app.route("/get_response", methods=["POST"])
def get_response():
    url = OPENAI_URL

    headers = {
        "Content-Type": "application/json",
        "api-key": api_key,
    }
    user_input = request.get_json().get("message")

    body = {
        "temperature": 0,
        "max_tokens": 2000,
        "top_p": 1.0,
        "stream": False,
        "dataSources": [
            {
                "type": "AzureCognitiveSearch",
                "parameters": {
                    "endpoint": cognitive_search_endpoint,
                    "key": cognitive_search_key,
                    "indexName": cognitive_search_index_name,
                    "queryType": "simple",
                    "fieldsMapping": {
                        "contentFieldsSeparator": "\n",
                        "contentFields": ["page_content"],
                        "filepathField": "PageNumber",
                        "titleField": None,
                        "urlField": "URL",
                        "vectorFields": [],
                    },
                    "strictness": 3,
                    "top_n_documents": 5,
                    "inScope": True,
                }
            }
        ],
        "messages": [
            {
                "role": "user",
                "content": user_input
            }
        ]
    }

    response = requests.post(url, headers=headers, json=body)
    json_response = response.json()
    print(json_response)

    message = json_response["choices"][0]["messages"][1]["content"]
    tool_message_content = json_response["choices"][0]["messages"][0]["content"]

    tool_message_content_dict = json.loads(tool_message_content)

    url2 = ""
    if "citations" in tool_message_content_dict:
        citations = tool_message_content_dict["citations"]
        if citations:
            first_citation = citations[0]
            if "url" in first_citation:
                url2 = first_citation["url"]

    content2 = ""
    if "citations" in tool_message_content_dict:
        citations = tool_message_content_dict["citations"]
        if citations:
            first_citation = citations[0]
            if "filepath" in first_citation:
                content2 = first_citation["filepath"]

    # Get username from session
    

    return jsonify({"assistant_content": message, "Page-Number": content2, "url": url2})

if __name__ == '__main__':
    app.run(debug=True)
