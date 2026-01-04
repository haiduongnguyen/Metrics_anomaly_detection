
import json
import boto3
import csv
import io
import operator

s3 = boto3.client("s3")


def load_rule_from_config():
    """Load rule from local config.py packaged with Lambda code."""
    from config import rules
    # Return the list of rules
    return rules 


def lambda_handler(event, context):
    file_data = event["file_data"]
    
    s3_file = s3.get_object(Bucket=file_data["bucket"], Key=file_data["key"])
    content = s3_file["Body"].read().decode("utf-8")

    # Process the content as needed
    data = json.loads(content) # Assuming the file contains JSON data

    rules = load_rule_from_config()

    for rule in rules:
        print(f"Applying rule: {rule['name']}")
        # Implement rule application logic here
        # For example, check conditions and perform actions
        for condition, value in rule["conditions"].items():
            print(f" - Condition: {condition} with value {value}")

            if content[condition] > value:
                print(f"   -> Condition met for {condition}") 

                
    


