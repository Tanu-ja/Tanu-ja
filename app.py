from flask import Flask, jsonify, request
import json
import requests
import os
import openai
from langdetect import detect
from dotenv import load_dotenv
from flask_cors import CORS, cross_origin

app = Flask(__name__)
cors = CORS(app)
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
def index():
    return f"<center><h1>Flask App deployment on AZURE</h1></center"

@app.route("/get_response", methods=["POST"])
@cross_origin()
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

    # Converting the content string to a dictionary

    tool_message_content_dict = json.loads(tool_message_content)

    # Extracting the 'citations' field if present
    url2 = ""
    if "citations" in tool_message_content_dict:
        citations = tool_message_content_dict["citations"]
        

        # Extracting the URL from the first citation if present

        if citations:
            first_citation = citations[0]

            if "url" in first_citation:
                url2 = first_citation["url"]

                # print(url2)

            else:
                print("No URL found in the first citation")

        else:
            print("No citations found")
    else:
        print("No 'citations' field found in the tool message content")
        



    content2 = ""
    if "citations" in tool_message_content_dict:
        citations = tool_message_content_dict["citations"]
        
        # Extracting the URL from the first citation if present
        if citations:
            first_citation = citations[0]

            if "filepath" in first_citation:
                content2 = first_citation["filepath"]
            else:
                print("No Content found in the first citation")
        else:
            print("No citations found")
    else:
        print("No 'citations' field found in the tool message content")


    return jsonify({"assistant_content": message + " " + url2, "Page-Number": content2})
    

if __name__ == "__main__":
    app.run()
