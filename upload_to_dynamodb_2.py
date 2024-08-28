import boto3
import json
import time
from botocore.exceptions import ClientError

# Initialize a session using Amazon DynamoDB
session = boto3.Session(
    aws_access_key_id='YOUR_ACCESS_KEY',  # Replace with your AWS Access Key
    aws_secret_access_key='YOUR_SECRET_KEY',  # Replace with your AWS Secret Key
    region_name='YOUR_REGION'  # Replace with your AWS region (e.g., 'us-east-1')
)
# Connect to the DynamoDB service
dynamodb = session.resource('dynamodb')

# Connect to your specific DynamoDB table
table = dynamodb.Table('SkinCareProducts')  # Replace with your DynamoDB table name

# Load JSON data
with open('skincare_products.json', 'r', encoding='utf-8') as json_file:
    products = json.load(json_file)

def batch_write_with_retry(products, retries=5):
    with table.batch_writer() as batch:
        for product in products:
            for i in range(retries):
                try:
                    batch.put_item(Item=product)
                    break  # Break out of the retry loop on success
                except ClientError as e:
                    if e.response['Error']['Code'] == 'ProvisionedThroughputExceededException':
                        wait_time = (2 ** i)  # Exponential backoff
                        print(f"Throughput exceeded, retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        raise  # Reraise the exception if it's not a throughput issue

# Batch write to DynamoDB with retry logic
batch_write_with_retry(products)

print("Data successfully uploaded to DynamoDB.")