import cryptography
import json
import requests
import logging
import os
import simplejson
from dotenv import load_dotenv
from intersight_auth import IntersightAuth
from datetime import datetime, timedelta
from google.cloud import storage

def lambda_handler():
    load_dotenv()
        
    addresses = list()
    health = list()
    summary = list()
    
    # Create an Intersight AUTH object using the API key and Secret Key from Intersight
    AUTH = IntersightAuth(
        secret_key_filename='SecretKey.txt',
        api_key_id=os.getenv('INTERSIGHT_API_KEY')
        )

    # Intersight REST API Base URL
    BURL = 'https://www.intersight.com/api/v1/'

    alarms_json_body = {
        "request_method": "GET",
        "resource_path": (
                'https://www.intersight.com/api/v1/compute/PhysicalSummaries'
        )
    }

    RESPONSE = requests.request(
        method=alarms_json_body['request_method'],
        url=alarms_json_body['resource_path'],
        auth=AUTH
    )

    results = RESPONSE.json()["Results"]
    
    for tags in results:
        for i in tags['Tags']:
            if i['Key'] == 'Location':
                addresses.append(i['Value'])
                if tags['AlarmSummary']['Critical'] > 0:
                    health.append("redhealth.png")
                elif tags['AlarmSummary']['Warning'] > 0 and tags['AlarmSummary']['Critical'] == 0:
                    health.append("yellowhealth.png")
                elif tags['AlarmSummary']['Critical'] == 0 and tags['AlarmSummary']['Critical'] == 0:
                    health.append("greenhealth.png")
                summary.append("Critical Faults: " + str(tags['AlarmSummary']['Critical']) + "<br>" + "Warning Faults: " + str(tags['AlarmSummary']['Warning']) + "<br><a href='https://intersight.com/an/compute/physical-summaries'>View Details</a>")

    #Save our data as a javascript variable for use by google maps
    f = open("data.js", "w")
    f.write("const address = ")
    simplejson.dump(addresses, f)
    f.write("\nconst health = ")
    simplejson.dump(health,f)
    f.write("\nconst summary = ")
    simplejson.dump(summary,f)
    f.close()

    client = storage.Client.from_service_account_json(json_credentials_path='GoogleSecretKey.json')
    bucket = client.get_bucket('datacentermap')
    object_name_in_gcs_bucket = bucket.blob('data.js')
    object_name_in_gcs_bucket.upload_from_filename('data.js')
    object_name_in_gcs_bucket.make_public()
    return 1

    
lambda_handler()