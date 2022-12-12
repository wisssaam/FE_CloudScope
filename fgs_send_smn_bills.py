# -*- coding:utf-8 -*-
import json
import requests
import os
import re

C_cloudstore_base_url = "https://api.orange.com/cloud/b2b/v1"

def authentification_smn():
    url = "https://iam.eu-west-0.prod-cloud-ocb.orange-business.com/v3/auth/tokens"

    payload = json.dumps({
    "auth": {
        "identity": {
        "methods": [
            "password"
        ],
        "password": {
            "user": {
            "name": "firstname.lastname",
            "password": ".....",
            "domain": {
                "name": "OCB000XXX"
            }
            }
        }
        },
        "scope": {
        "project": {
            "id": "fa742...."
        }
        }
    }
    })
    headers = {
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    token = response.headers['X-Subject-Token']

    return token

def getCloudStoreDocumentFile(cloudstore_header, document_name, document_id, logger):
    # build url to fetch the document
    url = "{}/documents/{}/file".format(C_cloudstore_base_url, document_id)
    C_temp_dir = "/tmp"
    document_path = os.path.join(C_temp_dir, document_name)
    # pass the default zippping mode for fetched files from CloudStore
    C_default_zipped_mode = 0 # 1 for zip else 0
    C_zipped_file = 0
    params = {'zipped':C_default_zipped_mode}
    if C_default_zipped_mode == C_zipped_file:
        # if the files are retrieved zipped, then change the document name (which is always in .csv) accordingly
        document_path = re.sub("\.csv$", ".zip", document_path)

   # Get document file
    try:
        r = requests.get(url, headers=cloudstore_header, params=params, stream=True)
        with open(document_path, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=128):
                fd.write(chunk)
    except:
        document_path = None
    
    return document_path

def computeCloudStoreHeader(cloudstore_credentials, contract_id, logger): 
    # set default initial value
    header = None
    
    # extract data from credentials dict
    auth_header   = cloudstore_credentials["auth_header"]
    api_key       = cloudstore_credentials["api_key"]
    client_id     = cloudstore_credentials["client"]["id"]
    client_secret = cloudstore_credentials["client"]["secret"]
    
    url  = "https://api.orange.com/oauth/v3/token"
    data = "grant_type=client_credentials"
    headers = {
        "Authorization": auth_header,
        "Cache-Control": "no-cache",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "Connection": "keep-alive"
    }

   # Generate token
    try:
        r = requests.post(url, headers=headers, data=data, auth=(client_id, client_secret))
        logger.info("Request CloudStore API token: {}".format(r.status_code))  

        if r.status_code < 300:
            token = r.json()['access_token']            
            header = {
                "Authorization": "Bearer " + token,
                "X-API-Key": api_key,
                "X-ECCS-Contract-Id": contract_id,
                "Accept": "application/json"
            }
        else:
            logger.error("Failed to get Cloud Store API token: {}".format(r.status_code))

    except Exception as error:
        logger.error("Failed to get Cloud Store API token: {}".format(error))
    
    return header

def getCloudStoreDocumentsList(cloudstore_header, document_type, max_files, logger): # 
    # build url to fetch the documents list
    url = "{}/documents".format(C_cloudstore_base_url)

    params = {'documentType': document_type, 'limit': max_files}        # sent: the correct answer :) - with document_type='partialConsumptionRatedReports'
    logger.info(params)
 
   # Get documents
    try:
        r = requests.get(url, headers=cloudstore_header, params=params)
        #logger.info("Request CloudStore documents list (params= - {} - {}): {}".format(document_type, max_files, r.status_code))
        
        if r.status_code != requests.codes.ok:
            raise Exception("Unable to get documents list: exit")
        
        documents = r.json()
        logger.info("documents="+json.dumps(documents))

    except:
        documents = None
    
    return documents


def send_smn_msg(token, year, month):
    url = "https://smn.eu-west-0.prod-cloud-ocb.orange-business.com/v2/fa7426a17fe246698cf9a475f4254099/notifications/topics/urn:smn:eu-west-0:fa7426a17fe246698cf9a475f4254099:9469994203fa42f5b51cba3b78b55549_dedicated_queue_dli_topic/publish"

    period = year + "/" + month

    payload = json.dumps({
    "subject": "Facture disponible",
    "message": "Votre facture est disponible " + period,
    "time_to_live": "3600"
    })
    headers = {
    'X-Auth-Token': token,
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)

def check_bill_available(year, month):
    import datetime

    def get_current_year():
        today = datetime.date.today()
        year = today.strftime("%Y")
        return year

    def get_current_month():
        return datetime.date.today().strftime("%m")


    if year == get_current_year() and month == get_current_month():
        return True
    else:
        return False
    
def handler (event, context):
    global logger
    logger = context.getLogger()

    contract_id = obs_address = context.getUserData('contract_id')
    document_type = obs_address = context.getUserData('document_type')
    max_files = obs_address = int(context.getUserData('max_files'))
    
    cloudstore_credentials = """{
            "auth_header":"Basic WWcz ...", 
            "api_key": "P+AuA5qT3UGLC+e ...",
            "client": {"id" : "Yg3 ...", "secret" : "QTC ..."}
    }"""

    cloudstore_header = computeCloudStoreHeader(json.loads(cloudstore_credentials), contract_id, logger)
    jsonObject = getCloudStoreDocumentsList(cloudstore_header, document_type, max_files, logger)

    for i in range(max_files):
        document_name = jsonObject[i]['filename']
        document_id = jsonObject[i]['id']
        document_path = getCloudStoreDocumentFile(cloudstore_header, document_name, document_id, logger)
        
        year = jsonObject[i]['period'][0:4]
        month = jsonObject[i]['period'][4:6]

        if (check_bill_available(year, month)):
            send_smn_msg(authentification_smn(), year, month)
            return {
                "statusCode": 200,
                "isBase64Encoded": False,
                "body": "Facture disponible",
                "headers": {
                    "Content-Type": "application/json"
                }
            }

        else:
            return {
                "statusCode": 200,
                "isBase64Encoded": False,
                "body": "Facture indisponible",
                "headers": {
                    "Content-Type": "application/json"
                }
            }
