import boto3
import json

# --- Configuration ---
AWS_REGION = "ap-southeast-1"
LAMBDA_FILTER = "vpbank_lambda_filter"
LAMBDA_NORMALIZATION = "vpbank_lambda_normalization"

# Create a Lambda client
lambda_client = boto3.client("lambda", region_name=AWS_REGION)

def invoke_lambda(function_name, payload):
    """Helper to call a Lambda and print results."""
    print(f"\n🚀 Invoking Lambda: {function_name}")
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType="RequestResponse",  # 'Event' for async
        Payload=json.dumps(payload),
    )
    payload_str = response["Payload"].read().decode("utf-8")
    print(f"Response:\n{payload_str}\n")

if __name__ == "__main__":
    # Example test input
    event_filter = {"dataset": "apm_metrics"}
    event_normalization = {"dataset": "apm_metrics"}

    # 1️⃣ Trigger Filter Lambda
    invoke_lambda(LAMBDA_FILTER, event_filter)

    # 2️⃣ Trigger Normalization Lambda
    invoke_lambda(LAMBDA_NORMALIZATION, event_normalization)
