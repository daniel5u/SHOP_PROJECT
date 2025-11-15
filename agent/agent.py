from openai import OpenAI
from agent.tools import *
from pydantic import BaseModel
import os
import json
import logging
from dotenv import load_dotenv
from agent.memory import SummarizationMemory
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing import TypedDict, Annotated, List
from accounts.models import User

load_dotenv()

client = OpenAI(
    api_key = os.environ.get("DEEPSEEK_API_KEY"),
    base_url = "https://api.deepseek.com/v1",
)

TOOLS = [
    {
        "type": "function",
        "function":{
            "name": "add_to_cart",
            "description": "Add a product to the cart",
            "parameters": AddToCartInput.model_json_schema(),
        }
    },
    {
        "type": "function",
        "function":{
            "name": "clear_cart",
            "description": "Clear the cart",
            "parameters": ClearCartInput.model_json_schema(),
        }
    },
    {
        "type": "function",
        "function":{
            "name": "list_cart",
            "description": "List the contents of the cart",
            "parameters": None,
        }
    },
    {
        "type": "function",
        "function":{
            "name": "search_products",
            "description": "Search for products by keyword",
            "parameters": SearchProductsInput.model_json_schema(),  
        }
    },
    {
        "type": "function",
        "function":{
            "name": "upload_product",
            "description": "Upload a product",
            "parameters": UploadProductInput.model_json_schema(),
        }
    },
    {
        "type": "function",
        "function":{
            "name": "update_product",
            "description": "Update a product",
            "parameters": UpdateProductInput.model_json_schema(),
        }
    },
    {
        "type": "function",
        "function":{
            "name": "delete_product",
            "description": "Delete a product",
            "parameters": DeleteProductInput.model_json_schema(),
        }
    },
    {
        "type": "function",
        "function":{
            "name": "change_user_name",
            "description": "Change the user name",
            "parameters": ChangeUserNameInput.model_json_schema(),
        }
    },
    {
        "type": "function",
        "function":{
            "name": "change_user_address",
            "description": "Change the user address",
            "parameters": ChangeUserAddressInput.model_json_schema(),
        }
    },
    {
        "type": "function",
        "function":{
            "name": "rag_retrieve",
            "description": "If the user is asking for some specific information about products, rather than searching for products by their name, you should use this function tool to retrieve information from the RAG",
            "parameters": RAGRetrieveInput.model_json_schema(),
        }
    }
]

memory = SummarizationMemory()

logger = logging.getLogger("ShoppingAgentLogger")
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

file_handler = logging.FileHandler("agent_run.log", mode="a", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S"
)

console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

if not logger.handlers:
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

class AgentState(TypedDict):
    messages: Annotated[List[dict], add_messages]
    user_info_dict: dict

def dispatch_tool(user_object, tool_call: dict) -> any:
    tool_name = tool_call.function.name
    raw_args = tool_call.function.arguments
    try:
        args = json.loads(raw_args)
    except json.JSONDecodeError:
        return f"Error: Invalid JSON arguments for tool {tool_name}: {raw_args}"

    logger.info(f"Dispatching tool '{tool_name}' with args: {args}")

    try:
        if tool_name == "add_to_cart":
            input_data = AddToCartInput(**args)
            tool_result = add_to_cart_tool(user_object, input_data)
        elif tool_name == "clear_cart":
            tool_result = clear_cart_tool(user_object, ClearCartInput())
        elif tool_name == "list_cart":
            tool_result = list_cart_tool(user_object)
        elif tool_name == "search_products":
            input_data = SearchProductsInput(**args)
            tool_result = search_products_tool(input_data.keyword)
        elif tool_name == "upload_product":
            input_data = UploadProductInput(**args)
            tool_result = upload_product_tool(user_object, input_data)
        elif tool_name == "update_product":
            input_data = UpdateProductInput(**args)
            tool_result = update_product_tool(user_object, input_data.product_id, input_data)
        elif tool_name == "delete_product":
            input_data = DeleteProductInput(**args)
            tool_result = delete_product_tool(user_object, input_data.product_id)
        elif tool_name == "change_user_name":
            input_data = ChangeUserNameInput(**args)
            tool_result = change_user_name_tool(user_object, input_data)
        elif tool_name == "change_user_address":
            input_data = ChangeUserAddressInput(**args)
            tool_result = change_user_address_tool(user_object, input_data)
        elif tool_name == "rag_retrieve":
            input_data = RAGRetrieveInput(**args)
            tool_result = rag_retrieve_tool(user_object, input_data)
        else:
            tool_result = f"Unknown tool: {tool_name}"

        return tool_result

    except Exception as e:
        logger.error(f"Error executing tool '{tool_name}': {e}", exc_info=True)
        return {f"Error executing tool '{tool_name}': {e}"}

def call_model_node(state: AgentState) -> dict:
    logger.info("Node: call_model_node")
    logger.info(f"Messages: {state['messages']}")
    
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=state["messages"],
        tools=TOOLS,
    )
    response_message = response.choices[0].message
    logger.info(f"Model response: {response_message}")
    return {"messages": [response_message.model_dump(exclude_none=True)]}
    
def execute_tools_node(state: AgentState) -> dict:
    logger.info("Node: execute_tools_node")

    user_info = state["user_info"]
    try:
        user_object = User.objects.get(uuid=user_info['uuid_id'])
    except User.DoseNotExist:
        logger.error(f"User with uuid: {user_info.get('uuid_id')} not found")
        return {"messages": [{"role":"system","content":"User not found"}]}
    except KeyError:
        logger.error("'uuid_id' not found in user_info dictionary")
        return {"messages": [{"role":"system","content":"User information is incomplete"}]}

    last_message = state["messages"][-1]
    tool_calls = last_message.get("tool_calls", [])

    tool_results = []
    for tool_call in tool_calls:
        tool_result = dispatch_tool(user_object, tool_call)
        tool_results.append({
            "tool_call_id":tool_call['id'],
            "role":"tool",
            "name":tool_call['function']['name'],
            "content":json.dumps(tool_result,ensure_ascii=False) if not isinstance(tool_result, str) else tool_result,
        })

    logger.info(f"Tool results: {tool_results}")
    return {"messages": tool_results}

def should_continue_router(state: AgentState) -> str:
    logger.info("Router: should_continue_router")
    last_message = state["messages"][-1]
    if "tool_calls" in last_message and last_message["tool_calls"]:
        logger.info("Decision: Continue to execute tools")
        return "continue"
    else:
        logger.info("Deicision: No Tool calls, returning model response")
        return "end"

workflow = StateGraph(AgentState)

workflow.add_node("agent",call_model_node)
workflow.add_node("action",execute_tools_node)

workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    "agent",
    should_continue_router,{
        "continue": "action",
        "end": END
    }
)

workflow.add_edge("action","agent")

app = workflow.compile()


def run_agent(user_info_dict: dict, message:str):
    logger.info("--- New Agent Run ---")
    logger.info(f"User: {user_info_dict.get('username')}, Message:{message}")

    memory.add_message({
        "role":"user",
        "content":message
    })

    initial_state = {
        "messages": memory.get_history(),
        "user_info": user_info_dict
    }
    
    final_state = app.invoke(initial_state)

    final_response_message = final_state["messages"][-1]
    agent_reply = final_response_message.get("content","")
    logger.info(f"Final agent reply: {agent_reply}")

    return agent_reply