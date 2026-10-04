"""Chainlit session history and visible tool I/O; graph logic lives in agent.py."""

import json
import os

import chainlit as cl
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from agent import build_agent


@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("messages", [])
    if not os.getenv("OPENAI_API_KEY") or not os.getenv("OPENAI_MODEL"):
        await cl.Message(
            content="Set OPENAI_API_KEY and OPENAI_MODEL in .env, then restart Chainlit. "
            "See .env.example and README.md for setup."
        ).send()
        return
    cl.user_session.set("agent", build_agent())
    await cl.Message(
        content="Ask about Cedar University's fictional 20-course catalog. "
        "You can use course names. Try: **What are the prerequisites for Deep Learning?** "
        "Tool steps show the catalog evidence behind each answer."
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    agent = cl.user_session.get("agent")
    if agent is None:
        await cl.Message(content="Configure .env and restart Chainlit to enable GPT replies.").send()
        return

    history = list(cl.user_session.get("messages"))
    history.append(HumanMessage(content=message.content))
    calls = {}
    final_answer = None

    # Stream node updates, not model tokens or reasoning content.
    async for update in agent.astream({"messages": history}, stream_mode="updates"):
        for state_update in update.values():
            for item in state_update["messages"]:
                history.append(item)
                if isinstance(item, AIMessage):
                    for call in item.tool_calls:
                        calls[call["id"]] = call
                    if not item.tool_calls:
                        final_answer = item.text
                elif isinstance(item, ToolMessage):
                    call = calls[item.tool_call_id]
                    async with cl.Step(name=call["name"], type="tool", show_input="json") as step:
                        step.input = call["args"]
                        step.output = json.loads(item.content)

    cl.user_session.set("messages", history)
    await cl.Message(content=final_answer).send()
