import requests
from sseclient import SSEClient
import asyncio
import json
import logging

logger = logging.getLogger()

DEFAULT_USER = "newbakery"
BLOCKING = "blocking"
STREAMING = "streaming"


def call_dify(endpoint, api_key, **kwargs):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    timeout = kwargs.get("timeout", 300)

    query = kwargs.get("query", "")
    inputs = kwargs.get("inputs", {})
    user = kwargs.get("user", DEFAULT_USER)
    response_mode = BLOCKING  
    conversation_id = kwargs.get("conversation_id", '')
    auto_generate_name = kwargs.get("auto_generate_name", False)
    streaming_callback = kwargs.get("streaming_callback", None)

    data = {
        "query": query,
        "inputs": inputs,
        "user": user,
        "conversation_id": conversation_id if conversation_id else None,
        "auto_generate_name": auto_generate_name,
        "response_mode": response_mode,
    }
    
    try:
        response = requests.post(endpoint, headers=headers, json=data, timeout=timeout)
        response.raise_for_status()  # 确保状态码 200
        return response.json()

    except requests.exceptions.HTTPError as http_err:
        error_details = response.content.decode() if "response" in locals() and response.content else str(http_err)
        raise Exception(f"HTTP error occurred: {error_details}") from http_err
    except Exception as ex:
        raise Exception(f"An error occurred: {str(ex)}") from ex




def stream_dify(endpoint, api_key, **kwargs):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    timeout = kwargs.get("timeout", 300)

    query = kwargs.get("query", "")
    inputs = kwargs.get("inputs", {})
    user = kwargs.get("user", DEFAULT_USER)
    response_mode = STREAMING # 避免 None
    conversation_id = kwargs.get("conversation_id", '')
    auto_generate_name = kwargs.get("auto_generate_name", False)
    streaming_callback = kwargs.get("streaming_callback", None)

    data = {
        "query": query,
        "inputs": inputs,
        "user": user,
        "conversation_id": conversation_id if conversation_id else None,
        "auto_generate_name": auto_generate_name,
        "response_mode": response_mode,
    }
    
    try:
        response = requests.post(endpoint, headers=headers, json=data, timeout=timeout, stream=True)
        response.raise_for_status()  # 确保状态码 200

        client = SSEClient(response)
        try:
            context = {}
            for event in client.events():
                if streaming_callback:
                    try:
                        streaming_callback(event, context)
                    except Exception as cb_err:
                        logger.error(str(cb_err))
                else:
                    yield event
        except Exception as ex:
            raise Exception(f"Error occurred while streaming SSE: {str(ex)}") from ex

    except requests.exceptions.HTTPError as http_err:
        error_details = response.content.decode() if "response" in locals() and response.content else str(http_err)
        raise Exception(f"HTTP error occurred: {error_details}") from http_err
    except Exception as ex:
        raise Exception(f"An error occurred: {str(ex)}") from ex
    
    


EVENT_WORKFLOW_STARTED = "workflow_started"
EVENT_WORKFLOW_FINISHED = "workflow_finished"
EVENT_NODE_STARTED = "node_started"
EVENT_NODE_FINISHED = "node_finished"


