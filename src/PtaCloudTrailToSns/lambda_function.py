import boto3
import json
import zlib
import os
import gzip
import io
import logging

# AWS SDK clients for Python
s3 = boto3.client('s3')
sns = boto3.client('sns', region_name=os.environ['SNSREGION'])
logger = logging.getLogger()
logger.setLevel("INFO")

def publish_record(record):
    logger.info('Publishing notification: ' + record)
    sns.publish(Message=json.dumps(record), TopicArn=os.environ['SNSTOPICARN'])

def lambda_handler(event, context):
    logger.trace(json.dumps(event))
    
    if not "s3" in event['Records'][0]:
        return {"message": "Event doesn't have s3 data"}
        
    src_bucket = event['Records'][0]['s3']['bucket']['name']
    src_key = event['Records'][0]['s3']['object']['key']
    
    try:
        # Fetching compressed log from S3
        logger.info('Fetching compressed log from S3...')
        response = s3.get_object(Bucket=src_bucket, Key=src_key)
        compressed_data = response['Body'].read()

        # Uncompressing log
        logger.info("Decompressing log...")
        with gzip.GzipFile(fileobj=io.BytesIO(compressed_data)) as gz:
            decompressed_data = gz.read()

        # Filtering log
        logger.info('Filtering log...')
        json_data = decompressed_data.decode('utf-8')
        logger.debug('CloudTrail JSON from S3: ' + json_data)
        records = json.loads(json_data)
        
        if "Records" in records:
            matching_records = [record for record in records['Records'] if 'accessKeyId' in record.get('userIdentity', {})]
    
            # Publishing notifications
            logger.info(f'Publishing {len(matching_records)} notification(s)...')
            for record in matching_records:
                publish_record(record)
                
        else:
            record = records
            if 'accessKeyId' in record.get('userIdentity', {}):
                publish_record(record)
            
        logger.info('Successfully published all notifications.')
        return {"message": "Success"}
            
    except Exception as e:
        logger.error(f'Error: {str(e)}')
        return {"message": "Error"}
