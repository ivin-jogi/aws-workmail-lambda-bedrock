import boto3
import json
import email
import logging
from botocore.exceptions import ClientError

# Initialize logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize the Bedrock client
bedrock_client = boto3.client('bedrock-agent-runtime')

class BedrockAgent:
    def invoke_agent(self, agent_id, agent_alias_id, session_id, prompt):
        """
        Sends a prompt for the agent to process and respond to.
        """
        try:
            response = bedrock_client.invoke_agent(
                agentId=agent_id,
                agentAliasId=agent_alias_id,
                sessionId=session_id,
                inputText=prompt
            )

            completion = ""

            for event in response.get("completion", []):
                chunk = event["chunk"]
                completion += chunk["bytes"].decode()

        except ClientError as e:
            logger.error(f"Couldn't invoke agent. {e}")
            raise

        return completion
        
def send_email(subject, body, sender, recipient):
    client = boto3.client('ses', region_name='us-west-2')
    response = client.send_email(
        Source=sender,
        Destination={
            'ToAddresses': [recipient]
        },
        Message={
            'Subject': {
                'Data': subject
            },
            'Body': {
                'Text': {
                    'Data': body
                }
            }
        }
    )
    return response['MessageId']
    
def lambda_handler(event, context):
    try:
        agent_id = "<your_agent_id>"
        agent_alias_id = "<your_alias_id>"
        session_id = "1234"
        # first code will fetch fromaddress, subject and messageId
        # then it will call workmail API to fetch actual message using this messageId
        # and then it will parse the message properly to convert it into text message

        workmail = boto3.client('workmailmessageflow', region_name="us-west-2")


        from_addr = event['envelope']['mailFrom']['address']
        print(from_addr)
        subject = event['subject']
        flowDirection = event['flowDirection']
        msg_id = event['messageId']

        # calling workmail API to fetch message body
        raw_msg = workmail.get_raw_message_content(messageId=msg_id)
        t = raw_msg['messageContent'].read()
        parsed_msg = email.message_from_bytes(t)

        subject = subject
    
        sender = "support@support-sample.awsapps.com"
        recipient = from_addr

        
        if parsed_msg.is_multipart():
            for part in parsed_msg.walk():
                payload = part.get_payload(decode=True) #returns a bytes object
                if type(payload) is bytes:
                    msg_text = payload.decode('utf-8') #utf-8 is default
                    print('*** Multipart payload ****', msg_text)
                    
                    prompt = msg_text
                    
                    if not all([agent_id, agent_alias_id, session_id, prompt]):
                        logger.error("Missing required parameters in the event.")
                        return {
                            'statusCode': 400,
                            'body': json.dumps('Missing required parameters.')
                        }
                
                    bedrock_agent = BedrockAgent()
                    try:
                        completion = bedrock_agent.invoke_agent(agent_id, agent_alias_id, session_id, prompt)
                        body = json.dumps(completion)
                        formatted_body = f"""
Dear {recipient},
                
{body.strip()}
                
Thank you,
Support Bot
"""
                        send_email(subject, formatted_body, sender, recipient)
                        print(formatted_body)
                        print("Successfully send mail")
                        return {
                            'statusCode': 200,
                            'body': json.dumps(completion)
                        }
                        
                        
                    except Exception as e:
                        logger.error(f"Error invoking Bedrock agent: {e}")
                        return {
                            'statusCode': 500,
                            'body': json.dumps(f"Error invoking Bedrock agent: {e}")
                        }
                    break
        else:
            payload = parsed_msg.get_payload(decode=True)
            if type(payload) is bytes:
                msg_text = payload.decode('utf-8') #utf-8 is default
                print('*** Single payload ****', msg_text)


    except Exception as e:
        # Send some context about this error to Lambda Logs
        print(e)
        raise e

    # Return value is ignored when Lambda is configured asynchronously at Amazon WorkMail
    # For more information, see https://docs.aws.amazon.com/workmail/latest/adminguide/lambda.html
    return {
          'actions': [
          {
            'allRecipients': True,                  # For all recipients
            'action' : { 'type' : 'DEFAULT' }       # let the email be sent normally
          }
        ]}
