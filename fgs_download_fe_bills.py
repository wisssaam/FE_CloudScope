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
    #params = json.dumps({'documentType':"all", 'limit':100})            # sent only 10 documents : all the latest usage reports (type="reports")
    #params = {'documentType': 'all', 'limit':10}                        # sent: {"documents": null}
    #params = {'documentType': 'comsumptionRatedReports', 'limit': 8}    # sent the correct answer :)
    #params = {'documentType': document_type, 'limit': max_files}        # sent the correct answer :) - with document_type='comsumptionRatedReports'
    #params = {'documentType': document_type, 'limit': max_files}        # sent: {"documents": null} - with document_type='partialComsumptionRatedReports'
    #params = {'documentType': 'toto', 'limit': max_files}               # sent: {"documents": null}
    #params = {'documentType': '', 'limit': 100}                         # sent: the correct answer :)

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
    document_type = 'bills'
    max_files = 3
    contract_id = obs_address = context.getUserData('contract_id')
    print(contract_id)
    print(type(contract_id))
    
    cloudstore_credentials = """{
            "auth_header":"Basic WWczTFhSY0ZUR3c4dENIWnlYUHoyZTc3WERvN3R5M0k6UVRDSHNPdEwxRFBVMTNJUA==", 
            "api_key": "P+AuA5qT3UGLC+eQXgCZg/2DbPCjumzAA/P6ZhfBkAGMyV04pbnU/V3jfsj/Uj8FIw51QgtCbsXDEgVaf6nV+sh4nNcVyxHa8cImeUjHctrG1D11tTE/QSDaInPNA37slCx75WrMcIJ3CUj+DYPrUVON6zC+zUPBHC6TlzA8YKu1qzH5NwO+NIARWnPJ8vtBcs381AiOVby8lmFyGftz4hBKWblgGzDZ7HXK77WqyqrPA6Yi+dLMb3vScgXIM9BuaY5FJxBndFObEZt6qXx5XKkJodPBMGYHpJojRXYKXUuF6RDeG+r0nOv2bDstBHjw5Vx+snDr2KWbT6K1jHpiRvBzd/SAE5rzPRbV63RhO7J1+h1KxEhiccGEoA1A1Qd0hYTNcN05MKh3UcmpAzIwvogbmwnV5o4ZkHUAoeOpRVTzOkt3zGiaOmh5wHHP6z9IViQq0SnouwrTvRMyXNq7UCbN/ra0EXynlXyjG5OwbShMIAhGlglivBe+YRhPtTpRhYUo7n84WjOvIsQU2WZbDGJ8E0h1xLAIJIP1NUUMhSfcmPg21L1MVWAYXxmi2ctiGxBMFXCj/L8JIeL8z826xc4p1kpE9bfS0P/fQHK9olZCdgerwoADKsKQoeT+lLdI47OCNdazvvXD3SMagwHcP0ikyiHsF7xFALPGIfNO54uXtg2pgo51fPehixHMNpKARL2GVxq6kh1td5IfCV8v7++tQ4ygvUuRIqw1IWy6cEjK/dl6aWghBsMthT1ylYkY+RYvKQj0shWf0mYAMkElZr+JF8ZzG9RbicjZktb2sS+V4ipuCTNVlcMoOLKnib0z20J8HIo/P2yxstRE9Adyki/XHWjq7JRa7/kj0mwwhLTUAvFpHn1D0OsgYl+1gjHVhbFABwesL0kjW81/39XnXABChCNKu8F/7zgphzVlpCaMjw/pOURG1qId1Qf66PS24b3RHo75Y+qLiat+jfpLyB0klxBAD1BLivr3haDVe36Nxy7p1o4M5j7MM5s8XbJl82GBW1kf7rGI12fDpQrZ9o37P/xnDGu86Mfkq00ZTAJ8bc/m/tDXQhWpRynXfPlXv7357whuehjqKllM6kNqpozroUXZCAso2qtCYlWyGKVQrlemovBQeD85fH0B/rvXtzXNkKb65FxY4Xfo2ZmFGMmryejQn+uMG5TFEMJ5LMeE1YGOLpNvlNcwsiWt5TkSfXz1asQS9+zgMBKzCvdclMDGjBL7xqSa0uN2kqmjGU/TjzCNz75HVJvqMZM8JG6u",
            "client": {"id" : "Yg3LXRcFTGw8tCHZyXPz2e77XDo7ty3I", "secret" : "QTCHsOtL1DPU13IP"}
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
