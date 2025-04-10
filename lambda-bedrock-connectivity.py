import boto3
import json

# Initialize Bedrock client
bedrock_client = boto3.client('bedrock-agent-runtime')

# Bedrock Agent details
AGENT_ID = "<your_agent_id>"
AGENT_ALIAS_ID = "<your_alias_id>"
SESSION_ID = "1234"

def invoke_bedrock_agent(prompt):
    """ Invoke AWS Bedrock Agent and return the response. """
    response = bedrock_client.invoke_agent(
        agentId=AGENT_ID,
        agentAliasId=AGENT_ALIAS_ID,
        sessionId=SESSION_ID,
        inputText=prompt
    )
    print("Response from Bedrock Agent:", response)  # Debugging log
    return "".join(event["chunk"]["bytes"].decode() for event in response.get("completion", []))

def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event))  # Debugging log

        # Use provided prompt or default to a predefined message
        prompt = event.get("prompt", "Hi, I'm Platinum tier, what all baggage allowance can i avail?").strip()

        # Invoke Bedrock Agent
        response_text = invoke_bedrock_agent(prompt)

        return {"statusCode": 200, "body": json.dumps(response_text)}

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps(f"Error: {str(e)}")}
