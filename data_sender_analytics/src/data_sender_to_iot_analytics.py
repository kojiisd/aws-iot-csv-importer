import sys
import os
import json
import logging
import traceback
import urllib.parse
import boto3
import pandas as pd

sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '../libs'))

from more_itertools import chunked

TMP_PATH = '/tmp/'
DATA_BATCH_SIZE = int(os.environ['DATA_BATCH_SIZE'])

logger = logging.getLogger()
logger.setLevel(logging.INFO)

iot_analytics_client = boto3.client('iotanalytics')
s3_client = boto3.resource('s3')

def convert_from_csv_to_json(file_path, bucket_name, header=False):
  df = pd.read_csv(file_path)
  tmp_json ={}

  if header:
    tmp_json = df.to_json(orient='records')
  else:
    tmp_json = df.to_json(orient='values')

  result_json_array = []
  for ele_json in json.loads(tmp_json):
    logger.info(ele_json)
    result_json = {}
    result_tmp_json = {}
    result_tmp_json['s3_bucket'] = bucket_name
    result_tmp_json['data'] = ele_json

    result_json['messageId'] = str(ele_json['account_number'])
    result_json['payload'] = json.dumps(result_tmp_json)
    result_json_array.append(result_json)

  logger.info(result_json_array)
  return result_json_array


def send_data_lambda(event, context):

  bucket_str = event['Records'][0]['s3']['bucket']['name']
  bucket = s3_client.Bucket(bucket_str)
  key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
  file_path = TMP_PATH + key

  logger.info(bucket_str)
  logger.info(key)
  logger.info(file_path)

  os.makedirs(os.path.dirname(file_path), exist_ok=True)
  bucket.download_file(key, file_path)

  json_array = convert_from_csv_to_json(file_path, bucket_str, True)
  
  for json_sub in chunked(json_array, DATA_BATCH_SIZE):
    response = iot_analytics_client.batch_put_message(
       channelName = 'csv_import_sample_channel',
       messages = json_sub
      )
      
    logger.info(response)
    
  return 'All data sending finished.'

