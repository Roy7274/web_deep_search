import asyncio
import time
from datetime import datetime
from typing import List, AsyncIterable, Generator

import volcenginesdkarkruntime.types.chat.chat_completion_chunk as completion_chunk

from arkitect.core.component.llm.llm import ArkMessage, ArkChatCompletionChunk


def cast_content_to_reasoning_content(
        chunk: ArkChatCompletionChunk,
) -> ArkChatCompletionChunk:
    new_chunk = ArkChatCompletionChunk(**chunk.__dict__)
    new_chunk.choices[0].delta.reasoning_content = chunk.choices[0].delta.content
    new_chunk.choices[0].delta.content = ""
    return new_chunk


def cast_reference_to_chunks(keyword: str, raw_content: str) -> ArkChatCompletionChunk:
    new_chunk = ArkChatCompletionChunk(
        id="",
        object="chat.completion.chunk",
        created=0,
        model="",
        choices=[],
        metadata={
            "reference": raw_content,
            "keyword": keyword,
        },
    )
    return new_chunk


def get_last_message(messages: List[ArkMessage], role: str):
    """Finds the last ArkMessage of a specific role, given the role."""
    for message in reversed(messages):
        if message.role == role:
            return message
    return None


def get_current_date() -> str:
    return datetime.now().strftime("%Y年%m月%d日")


def gen_metadata_chunk(metadata: dict) -> ArkChatCompletionChunk:
    return ArkChatCompletionChunk(
        id='',
        created=int(time.time()),
        model='',
        object='chat.completion.chunk',
        choices=[completion_chunk.Choice(
            index=0,
            delta=completion_chunk.ChoiceDelta(
                content="",
                reasoning_content=""
            ),
        )],
        metadata=metadata,
    )


def sync_wrapper(async_generator: AsyncIterable) -> Generator:
    loop = asyncio.new_event_loop()
    try:
        gen = async_generator
        _aiter = gen.__aiter__()
        while True:
            try:
                item = loop.run_until_complete(_aiter.__anext__())
                yield item
            except StopAsyncIteration:
                break
    finally:
        loop.close()
