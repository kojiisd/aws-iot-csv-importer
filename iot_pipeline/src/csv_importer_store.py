import os
import json
import logging

import boto3

DYNAMODB_TABLE = os.environ['DYNAMODB_TABLE']
CONF_PATH = os.environ['CONF_PATH']
TMP_PATH = '/tmp/'

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.resource('s3')
ddb_client = boto3.resource('dynamodb')

def store_data_lambda(event, context):
  logger.info("Start store data: {}".format(event))
  
  bucket = s3_client.Bucket(event[0]['s3_bucket'])
  key = CONF_PATH
  file_path = TMP_PATH + key
  os.makedirs(os.path.dirname(file_path), exist_ok=True)
  
  bucket.download_file(key, file_path)
  conf_file = open(file_path, 'r')
  conf_json = json.load(conf_file)
  
  logger.info(conf_json)
  result_json_array = []
  tmp_json = {}

  for ev in event:
    tmp_json = {}
    for key, value in ev['data'].items():
      if key in conf_json.keys():
        tmp_json[conf_json[key]] = value
    result_json_array.append(tmp_json)

  logger.info(result_json_array)
  
  ddb_table = ddb_client.Table(DYNAMODB_TABLE)
  
  with ddb_table.batch_writer() as batch:
    for item_json in result_json_array:
      batch.put_item(
        Item=item_json
        )

  return result_json_array

