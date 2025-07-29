import json
import os
import time
import logging
from typing import Literal, TypedDict, List, Union

from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, BaseMessage
from langchain_aws import ChatBedrock
from langgraph.graph import StateGraph, START, END
from lumigo_opentelemetry import tracer_provider
from opentelemetry.trace import SpanKind


logger = logging.getLogger()
logger.setLevel(logging.INFO)

MODEL_ID = os.environ.get("MODEL_ID", "us.anthropic.claude-3-7-sonnet-20250219-v1:0")
BEDROCK_REGION = os.environ.get("BEDROCK_REGION", "us-west-2")


@tool
def get_cities_data(query: str) -> str:
    """Search for information on a given topic"""
    print(f"Searching for information on: {query}")
    time.sleep(2)
    return json.dumps([
        {"city": "New York", "population": 8419600, "area": 789.43},
        {"city": "Los Angeles", "population": 3980400, "area": 1214.9},
        {"city": "Chicago", "population": 2716000, "area": 589.56},
        {"city": "Houston", "population": 2328000, "area": 1651.11},
    ])


tools = [get_cities_data]
tools_by_name = {t.name: t for t in tools}

class AgentState(TypedDict):
    messages: List[BaseMessage]

def run_agent(task: str) -> str:
    llm = ChatBedrock(
        model=MODEL_ID,
        region=BEDROCK_REGION,
        max_tokens=1000,
        temperature=0.1,
    )
    llm_with_tools = llm.bind_tools(tools)

    system_message = SystemMessage(
        content="""You are a versatile agent capable of both research and action tasks. Use the available tools to gather information, analyze data, and execute tasks effectively."""
    )

    # Node: LLM call
    def llm_call(state: AgentState):
        messages = state.get("messages", [])
        result = llm_with_tools.invoke([system_message] + messages)
        return {"messages": messages + [result]}

    # Node: Tool execution
    def tool_node(state: AgentState):
        messages = state["messages"]
        last_message = messages[-1]
        results = []
        for tool_call in getattr(last_message, "tool_calls", []):
            tool = tools_by_name[tool_call["name"]]
            observation = tool.invoke(tool_call["args"])
            results.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
        return {"messages": messages + results}

    # Conditional: Should continue or end
    def should_continue(state: AgentState) -> Literal["environment", "END"]:
        messages = state["messages"]
        last_message = messages[-1]
        if getattr(last_message, "tool_calls", []):
            return "environment"
        return "END"

    # Build the agent workflow
    agent_builder = StateGraph(AgentState)
    agent_builder.add_node("llm_call", llm_call)
    agent_builder.add_node("environment", tool_node)
    agent_builder.add_edge(START, "llm_call")
    agent_builder.add_conditional_edges(
        "llm_call", should_continue, {"environment": "environment", "END": END}
    )
    agent_builder.add_edge("environment", "llm_call")
    agent = agent_builder.compile()

    # Run the agent
    state = agent.invoke({"messages": [HumanMessage(content=task)]})
    # Return the last LLM message content
    for msg in reversed(state["messages"]):
        if hasattr(msg, "content") and msg.content:
            return msg.content
    return "No response."


if __name__ == "__main__":
    print(run_agent("What is the most populous city?"))

    tracer_provider.force_flush()
