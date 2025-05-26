import logging
import json
import zlib
import base64

import dify
from schemas.conversation import ChatSSEResponse


logger = logging.getLogger()


def _as_status_message(message, role="agent"):
    logger.info(f"{role}: {message}")
    return ChatSSEResponse(role=role, status="succeeded", error = "", content_type = "status_message", content=message, thought_process="")

def _as_markdown(message, role="agent"):
    logger.info(f"{role}: {message}")
    return ChatSSEResponse(role=role, status="succeeded", error = "", content_type = "markdown", content=message, thought_process="")

def _as_error(ex, message = None, role="agent"):
    if message is None:
        message = str(ex)
    logger.error(f"{role}: {str(ex)}")
    return ChatSSEResponse(role=role, status="failed", error = str(ex), content_type = "error", content=message, thought_process="")

def _as_signal(signal, role="agent"):
    logger.info(f"{role}: {str(signal)}")
    return ChatSSEResponse(role=role, status="succeeded", error = "", content_type = "signal", content=signal, thought_process="")

def _as_goal(data, role="agent"):
    logger.info(f"{role}: {data}")
    return ChatSSEResponse(role=role, status="succeeded", error = "", content_type = "goal", content=data, thought_process="")

def _as_plan(data, role="agent"):
    logger.info(f"{role}: {data}")
    return ChatSSEResponse(role=role, status="succeeded", error = "", content_type = "plan", content=data, thought_process="")

def _as_data(data, role="agent", thought_process=""):
    logger.info(f"{role}: {data}, {thought_process}")
    return ChatSSEResponse(role=role, status="succeeded", error = "", content_type = "data", content=data, thought_process=thought_process)

def _as_plot(data, role="agent", thought_process=""):
    logger.info(f"{role}: {data}, {thought_process}")
    return ChatSSEResponse(role=role, status="succeeded", error = "", content_type = "plot", content=data, thought_process=thought_process)



def _sse_response(sseres, chat_id):
    sseres.chat_id = chat_id
    return sseres


StartSignal = lambda chat_id : _sse_response(_as_signal('START'), chat_id)
DoneSignal = lambda chat_id : _sse_response(_as_signal('DONE'), chat_id)
AsError = lambda ex, chat_id :  _sse_response(_as_error(ex), chat_id)
AsPlot = lambda data, thought_process, chat_id : _sse_response(_as_plot(data, thought_process=thought_process), chat_id)

def goal_generator_finished(event, ctx):
    status = event.get("data", {}).get('status', '')
    error = event.get("data", {}).get('error')
    if status == "succeeded":
        text = event.get("data", {}).get('outputs', {}).get('text', '')
        return _as_goal(text)
    else:
        return _as_error(error)


def plan_generator_finished(event, ctx):
    status = event.get("data", {}).get('status', '')
    error = event.get("data", {}).get('error')
    if status == "succeeded":
        text = event.get("data", {}).get('outputs', {}).get('text', '')
        try:
            tasks = json.loads(text)
            return _as_plan(tasks)
        except Exception as error:
            return _as_error(error)
    else:
        return _as_error(error)


def sql_agent_finished(event, ctx):
    status = event.get("data", {}).get('status', '')
    error = event.get("data", {}).get('error')
    if status == "succeeded":
        results = event.get("data", {}).get('outputs', {}).get('json', [])
        if results and len(results) > 0:
            result = results[0]
            is_error = result.get('is_error', 'false') == 'true'
            error_message = result.get('error_message', '')
            role = result.get('role', '')
            jsons = result.get('jsons', [])
            thought_process = result.get('thought_process', [])
            if is_error:
                return _as_error(error_message, role=role)
            else:
                return _as_data(jsons, role=role, thought_process=thought_process)
        else:
            return _as_error("empty results of sql_agent")
    else:
        return _as_error(error, role="sql_agent")


def chat_agent_finished(event, ctx):
    status = event.get("data", {}).get('status', '')
    error = event.get("data", {}).get('error')
    if status == "succeeded":
        results = event.get("data", {}).get('outputs', {}).get('json', [])
        if results and len(results) > 0:
            result = results[0]
            role = result.get('role', '')
            markdowns = result.get('markdowns', [])
            return _as_markdown(markdowns, role = role)
        else:
            return _as_error("empty results of chat_agent")
    else:
        return _as_error(error, role="chat_agent")

    

luna_event_handlers = {
    f"{dify.EVENT_WORKFLOW_STARTED}>": lambda event, ctx: _as_signal('START'), 
    f"{dify.EVENT_WORKFLOW_FINISHED}>": lambda event, ctx: _as_signal('DONE'), 
    "node_started>#start": lambda event, ctx: _as_status_message('Thinking ...'),
    "node_started>#get_conversation": lambda event, ctx: _as_status_message('Referencing conversation history ...'),
    "node_started>#get_sources_descriptions": lambda event, ctx:  _as_status_message('Searching related table descriptions...'),
    "node_started>#goal_generator": lambda event, ctx:  _as_status_message('Generating goal ...'),
    "node_finished>#goal_generator": goal_generator_finished,
    "node_started>#plan_generator": lambda event, ctx:  _as_status_message('Making plans ...'),
    "node_finished>#plan_generator": plan_generator_finished,
    "iteration_next>#iteration": lambda event, ctx: logger.info("loop started ..."),
    "node_started>#sql_agent": lambda event, ctx:  _as_status_message('Executing SQL ...'),
    "node_finished>#sql_agent": sql_agent_finished,
    "node_started>#chat_agent": lambda event, ctx: _as_status_message('Summrizing ...'),
    "node_finished>#chat_agent": chat_agent_finished,
    "node_finished>#end": lambda event, ctx:  _as_status_message('Finalizing ...'),
}



luna2_event_handlers = {
    # f"{dify.EVENT_WORKFLOW_STARTED}>": lambda event, ctx: _as_signal('START'), 
    # f"{dify.EVENT_WORKFLOW_FINISHED}>": lambda event, ctx: _as_signal('DONE'), 
    "node_started>#start": lambda event, ctx: _as_status_message('Thinking ...'),
    "node_started>#get_conversation": lambda event, ctx: _as_status_message('Referencing conversation history ...'),
    "node_started>#get_sources_descriptions": lambda event, ctx:  _as_status_message('Searching related table descriptions...'),
    "node_started>#goal_generator": lambda event, ctx:  _as_status_message('Generating goal ...'),
    "node_finished>#goal_generator": goal_generator_finished,
    "node_started>#plan_generator": lambda event, ctx:  _as_status_message('Making plans ...'),
    "node_finished>#plan_generator": plan_generator_finished,
    "node_finished>#end": lambda event, ctx:  _as_status_message('Finalizing ...'),
}




def sql_runner_finished(event, ctx):
    status = event.get("data", {}).get('status', '')
    error = event.get("data", {}).get('error')
    if status == "succeeded":
        results = event.get("data", {}).get('outputs', {}).get('json', [])
        if results and len(results) > 0:
            result = results[0]
            is_error = result.get('is_error', 'false') == 'true'
            error_message = result.get('error_message', '')
            role = result.get('role', 'sql-agent')
            results = result.get('results', [])
            thought_process = result.get('sql', "")
            if is_error:
                return _as_error(error_message, role=role)
            else:
                return _as_data(results, role='sql-agent', thought_process=thought_process)
        else:
            return _as_error("empty results of sql runner")
    else:
        return _as_error(error, role="sql_agent")


sqlagent_event_handlers = {
    # f"{dify.EVENT_WORKFLOW_STARTED}>": lambda event, ctx: _as_signal('START'), 
    # f"{dify.EVENT_WORKFLOW_FINISHED}>": lambda event, ctx: _as_signal('DONE'), 
    "node_started>#start": lambda event, ctx: _as_status_message('Thinking ...'),
    "node_started>#get_conversation": lambda event, ctx: _as_status_message('Referencing conversation history ...'),
    "node_started>#get_query_schema": lambda event, ctx:  _as_status_message('Searching related table schemas...'),
    "node_started>#sql_writer": lambda event, ctx:  _as_status_message('Generating SQL...'),
    "node_started>#sql_runner": lambda event, ctx:  _as_status_message('Running SQL...'),
    "node_finished>#sql_runner": sql_runner_finished,
    "node_started>#sql_rewriter": lambda event, ctx:  _as_status_message('Retry! Generating SQL...'),
    "node_started>#sql_runner_again": lambda event, ctx:  _as_status_message('Retry! Running SQL...'),
    "node_finished>#sql_runner_again": sql_runner_finished,
    "node_finished>#end": lambda event, ctx:  _as_status_message('Finalizing ...'),
}


def chat_generator_finished(event, ctx):
    status = event.get("data", {}).get('status', '')
    error = event.get("data", {}).get('error')
    if status == "succeeded":
        text = event.get("data", {}).get('outputs', {}).get('text', '')
        try:
            result = json.loads(text)
            answer = result.get('answer', '')
            return _as_markdown(answer, role="chat-agent")
        except Exception as error:
            return _as_error(error, role="chat-agent")
    else:
        return _as_error(error, role="chat-agent")


chatagent_event_handlers = {
    # f"{dify.EVENT_WORKFLOW_STARTED}>": lambda event, ctx: _as_signal('START'), 
    # f"{dify.EVENT_WORKFLOW_FINISHED}>": lambda event, ctx: _as_signal('DONE'), 
    "node_started>#start": lambda event, ctx: _as_status_message('Thinking ...'),
    "node_started>#get_conversation_history": lambda event, ctx: _as_status_message('Referencing conversation history ...'),
    "node_started>#chat_generator": lambda event, ctx:  _as_status_message('Generating Text ...'),
    "node_finished>#chat_generator": chat_generator_finished,
    "node_finished>#end": lambda event, ctx:  _as_status_message('Finalizing ...'),
}

def get_python_data_execution_result_finished(event, ctx):
    status = event.get("data", {}).get('status', '')
    error = event.get("data", {}).get('error')
    if status == "succeeded":
        res = event.get("data", {}).get('outputs', {})
        is_error = res.get('is_error', '')
        error = res.get('error', '')
        result = res.get('result', '')
        try:
            if is_error == 'true':
                return _as_error(error, role="python-data-agent")
            else:
                if isinstance(result, str):
                    result = json.loads(result)
                return _as_data(result, role="python-data-agent")
        except Exception as error:
            return _as_error(error, role="python-data-agent")
    else:
        return _as_error(error, role="python-data-agent")


python_data_agent_event_handlers = {
    # f"{dify.EVENT_WORKFLOW_STARTED}>": lambda event, ctx: _as_signal('START'), 
    # f"{dify.EVENT_WORKFLOW_FINISHED}>": lambda event, ctx: _as_signal('DONE'), 
    "node_started>#start": lambda event, ctx: _as_status_message('Thinking ...'),
    "node_started>#python_generator": lambda event, ctx: _as_status_message('Writing Python Code ...'),
    "node_started>#python3_code_runner": lambda event, ctx:  _as_status_message('Running Python Code ...'),
    "node_finished>#get_python_execution_result": get_python_data_execution_result_finished,
    "node_finished>#end": lambda event, ctx:  _as_status_message('Finalizing ...'),
}


# def get_plotly_execution_result_finished(event, ctx):
#     status = event.get("data", {}).get('status', '')
#     error = event.get("data", {}).get('error')
#     if status == "succeeded":
#         res = event.get("data", {}).get('outputs', {})
#         is_error = res.get('is_error', '')
#         error = res.get('error', '')
#         result = res.get('result', '')
#         try:
#             if is_error == 'true':
#                 return _as_error(error, role="plot-agent")
#             else:
#                 compressed_data = base64.b64decode(result)
#                 input_bytes = zlib.decompress(compressed_data)
#                 restored = input_bytes.decode('utf-8')
#                 return _as_plot(restored, role="plot-agent", thought_process=restored)
#         except Exception as error:
#             return _as_error(error, role="plot-agent")
#     else:
#         return _as_error(error, role="plot-agent")

plotly_agent_event_handlers = {
    # f"{dify.EVENT_WORKFLOW_STARTED}>": lambda event, ctx: _as_signal('START'), 
    # f"{dify.EVENT_WORKFLOW_FINISHED}>": lambda event, ctx: _as_signal('DONE'), 
    "node_started>#start": lambda event, ctx: _as_status_message('Thinking ...'),
    "node_started>#python_generator": lambda event, ctx: _as_status_message('Writing Python Code ...'),
    "node_started>#python3_code_runner": lambda event, ctx:  _as_status_message('Running Python Code ...'),
    # "node_finished>#get_python_execution_result": get_plotly_execution_result_finished,
    "node_finished>#end": lambda event, ctx:  _as_status_message('Finalizing ...'),
}

