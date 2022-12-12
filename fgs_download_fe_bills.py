# -*- coding:utf-8 -*-
import json
import requests
import os
import re
from obs import ObsClient
import sys

C_cloudstore_base_url = "https://api.orange.com/cloud/b2b/v1"


def upload_file_to_obs(obsAddr, bucket, objName, ak, sk):

    TestObs = ObsClient(access_key_id=ak, secret_access_key=sk,server=obsAddr)
    objAbsPath = os.path.join('/tmp', objName)   # Obtains the absolute path of a local file.
    resp = TestObs.putFile(bucketName=bucket, objectKey=objName, file_path=objAbsPath)

    if isinstance(resp, list):
        for k, v in resp:
            print('PostObject, objectKey',k, 'common msg:status:', v.status, ',errorCode:', v.errorCode, ',errorMessage:', v.errorMessage)
    else:
        print('PostObject, common msg: status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)
    # Returns the status code of a POST event.
    return (int(resp.status))


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

def getCloudStoreDocumentsList(cloudstore_header, contract_id, document_type, max_files, logger): # 
    # build url to fetch the documents list
    url = "{}/documents".format(C_cloudstore_base_url)
    #params = json.dumps({'documentType':document_type, 'limit':max_files})

    params = {'documentType': document_type, 'limit': max_files}        # sent: the correct answer :) - with document_type='partialConsumptionRatedReports'
    logger.info(params)



   # Get documents
    #if True:
    try:
        r = requests.get(url, headers=cloudstore_header, params=params)
        
        logger.info("Request CloudStore documents list (params= {} - {} - {}): {}".format(contract_id, document_type, max_files, r.status_code))
                
        if r.status_code != requests.codes.ok:
            
            raise Exception("Unable to get documents list: exit")
        documents = r.json()
        logger.info("documents="+json.dumps(documents))


    #if False:
    except:
        documents = None
    
    return documents

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

def file_upload(context, logger, fileName):
    objBucket = context.getUserData('objBucket')     # Enter the name of the bucket to which you want to upload files.

    if objBucket is None or fileName is None:
        logger.error("Please set environment variables objBucket and fileName.")
        return ("Please set environment variables objBucket and fileName.")

    # You are advised to use the log instance provided by FunctionGraph to debug or print messages and not to use the native print function.
    logger.info("*** objBucket: " + objBucket)
    logger.info("*** fileName:" + fileName)

    # Obtains a temporary AK and SK. An agency is required to access IAM.
    ak = context.getAccessKey()
    sk = context.getSecretKey()
    
    if ak == "" or sk == "":
        logger.error("Failed to access OBS because no temporary AK, SK, or token has been obtained. Please set an agency.")
        return ("Failed to access OBS because no temporary AK, SK, or token has been obtained. Please set an agency.")

    obs_address = context.getUserData('obsAddress')  # Domain name of the OBS service. Use the default value.
    if obs_address is None:
        obs_address = 'oss.eu-west-0.prod-cloud-ocb.orange-business.com'
    
    # Uploads a file to a specified bucket.
    status = upload_file_to_obs(obs_address, objBucket, fileName, ak, sk)
    if (status == 200 or status == 201):
        logger.info("File uploaded to OBS successfully. View details in OBS.")
        return ("File uploaded to OBS successfully. View details in OBS.")
    else:
        logger.error("Failed to upload the file to OBS.")
        return ("Failed to upload the file to OBS.")


def handler (event, context):
    global logger

    logger = context.getLogger()

    contract_id = obs_address = context.getUserData('contract_id')
    document_type = obs_address = context.getUserData('document_type')
    max_files = obs_address = int(context.getUserData('max_files'))

    cloudstore_credentials = """{
            "auth_header":"Basic WWczTFhSY...", 
            "api_key": "P+AuA5qT3UGLC+eQXgCZg/2DbPu...",
            "client": {"id" : "Yg3LX.....", "secret" : "QTCHs....."}
    }"""

    cloudstore_header = computeCloudStoreHeader(json.loads(cloudstore_credentials), contract_id, logger)
    jsonObject = getCloudStoreDocumentsList(cloudstore_header, contract_id, document_type, max_files, logger)

    for i in range(max_files):
        document_name = jsonObject[i]['filename']
        document_id = jsonObject[i]['id']
        document_path = getCloudStoreDocumentFile(cloudstore_header, document_name, document_id, logger)
        file_upload(context, logger, document_name)

    return {
        "statusCode": 200,
        "isBase64Encoded": False,
        "body": document_path,
        "headers": {
            "Content-Type": "application/json"
        }
    }
