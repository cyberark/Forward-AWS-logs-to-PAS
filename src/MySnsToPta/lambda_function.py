import json
import socket
import os
from aws_syslog_mapper import normalize_aws_syslog  # our mapping function

TCP_IP = os.environ['PTAIP']
TCP_PORT = int(os.environ['PTAPort'])  # PTA Port
BUFFER_SIZE = 1024

def sendData(sock, msg):
    try:
        sock.sendall(msg)
    except:
        print("Failed to send data!")

def lambda_handler(event, context):
    print(json.dumps(event))  # For debugging

    for record in event["Records"]:
        try:
            message = parse_and_transform(record)
            print(f"Transformed message: {message}")

            # Open TCP connection
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                print(f"Connecting to PTA at {TCP_IP}:{TCP_PORT}")
                sock.connect((TCP_IP, TCP_PORT))
                b_event = message.encode("utf-8")
                sendData(sock, b_event)
                print(f"Sent: {b_event}")

        except Exception as e:
            print(f"Error processing record: {e}")

    return {
        'statusCode': 200,
        'body': json.dumps('Lambda to PTA completed successfully!')
    }

def parse_and_transform(record):
    print(f"Record data: {record}")

    if record.get("EventSource") == "aws:sns":
        print("The event source is aws:sns")
        sns_message = record["Sns"]["Message"]
    else:
        print(f"The event source is {record.get('EventSource')}")
        sns_message = json.dumps(record)

    try:
        cloudtrail_event = json.loads(sns_message)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in SNS message: {e}")

    transformed_event = normalize_aws_syslog(cloudtrail_event)

    return json.dumps(transformed_event)
