import asyncio
import logging
import gradio as gr
from gradio import ChatMessage
from pydantic import BaseModel
from openai import OpenAI
from typing import Any, Generator

from config import ARK_API_KEY, API_ADDR, API_BOT_ID, SEARCH_ENGINE

client = OpenAI(base_url=API_ADDR, api_key=ARK_API_KEY)

logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s][%(levelname)s] %(message)s"
)
LOGGER = logging.getLogger(__name__)

# store the search records
search_records = []

global_css = """
.search-panel {
  height: 800px;
  overflow: auto;
  border: 1px solid #ccc;
  padding: 10px;
}

.chat-col {
  height: 100%;
}
"""


def update_search_panel():
    """生成右侧搜索面板的HTML内容"""
    html = "<div class='search-panel'>"
    for i, record in enumerate(search_records, 1):
        if isinstance(record, BaseModel):
            record = record.model_dump(exclude_none=True, exclude_unset=True)
        html += f"""
        <div class='search-result-container'>
            <strong>🔍search [{record.get('query')}]</strong>
            <div class='results'>
                <strong>📖results: ({len(record.get('search_references', []))}):</strong>
                <ol>{"".join([f"<li><a href={res.get('url', '')}>{res.get('title', '')}</a></li>"
                              for res in record.get('search_references', [])])}</ol>
            </div>
        </div>
        """
    html += "</div>"
    return gr.HTML(value=html)


def stream_chat(message: str,
                history: list,
                search_engine: str,
                ) -> Generator[list[tuple[str, str]], Any, None]:
    global search_records
    history.clear()
    search_records = []

    sum_reasoning_content = ""
    sum_content = ""
    sum_search_content = ""
    planning_rounds = 0

    thinking_msg = ChatMessage(content=sum_reasoning_content,
                               metadata={"title": f"🤔 thinking round {planning_rounds}",
                                         "id": f"thinking-round-{planning_rounds}", "status": "pending"})

    searching_msg = ChatMessage(content="",
                                metadata={"title": f"🔍 searching round {planning_rounds}",
                                          "id": f"searching-round-{planning_rounds}", "status": "pending"})
    history.append(thinking_msg)

    for rsp in client.chat.completions.create(
            model=API_BOT_ID,
            messages=[
                {
                    "role": "user",
                    "content": message,
                }
            ],
            stream=True,
            extra_body={"metadata": {"search_engine": search_engine}},
    ):
        # round vars
        reasoning_content = rsp.choices[0].delta.reasoning_content if hasattr(rsp.choices[0].delta,
                                                                              'reasoning_content') else ''
        content = rsp.choices[0].delta.content if hasattr(rsp.choices[0].delta, 'content') else ''
        metadata = getattr(rsp, 'metadata', {})

        if metadata:
            logging.info(f"metadata: {rsp.metadata}")
            search_state = metadata.get('search_state', '')
            search_keywords = metadata.get('search_keywords', [])
            search_results = metadata.get('search_results', [])

            if search_state == 'searching':
                # think round ended
                thinking_msg.metadata.update({"status": "done"})
                yield history, update_search_panel()
                # clear thinking content
                sum_reasoning_content = ""

                # search round started
                sum_search_content += "\n【搜索关键词】\n" + "\n\n".join(search_keywords) + "\n"
                searching_msg.content = sum_search_content
                history.append(searching_msg)
                yield history, update_search_panel()
            elif search_state == 'searched':
                sum_search_content += "\n【搜索总结】\n\n"
                for search_result in search_results:
                    sum_search_content += f"\n {search_result.get('summary_content')} \n"
                searching_msg.content = sum_search_content
                searching_msg.metadata.update({"status": "done"})
                search_records += search_results
                yield history, update_search_panel()
                sum_search_content = ""
                sum_reasoning_content = ""
                planning_rounds += 1
                # new msgs
                thinking_msg = ChatMessage(content=sum_reasoning_content,
                                           metadata={"title": f"🤔 thinking round {planning_rounds}",
                                                     "id": f"thinking-round-{planning_rounds}", "status": "pending"})
                searching_msg = ChatMessage(content="",
                                            metadata={"title": f"🔍 searching round {planning_rounds}",
                                                      "id": f"searching-round-{planning_rounds}", "status": "pending"})
                history.append(thinking_msg)
                yield history, update_search_panel()

        if reasoning_content:
            sum_reasoning_content += reasoning_content
            thinking_msg.content = sum_reasoning_content
            thinking_msg.metadata.update({"status": "pending"})
            yield history, update_search_panel()
        elif content:
            thinking_msg.metadata.update({"status": "done"})
            sum_content += content
            yield [*history, ChatMessage(
                content=sum_content,
                role="assistant",
            )], update_search_panel()


if __name__ == "__main__":
    with gr.Blocks(css=global_css) as demo:
        references = gr.HTML(render=False)
        with gr.Row(min_height=900, height=900):
            with gr.Column(scale=2, elem_classes='chat-col'):
                gr.Markdown("<center><h2>🤖 Deep Research</h2></center>")
                gr.Markdown("> **please use single round chat**")
                # 选项 (显示名, 实际传给后端的值)。volc_bot 暂时隐藏；ask_echo 显示为 BytePlusAskEchoSearchAgent
                _engine_choices = [
                    ("tavily", "tavily"),
                    ("you", "you"),
                    ("BytePlusAskEchoSearchAgent", "ask_echo"),
                ]
                _default_engine = SEARCH_ENGINE if SEARCH_ENGINE != "volc_bot" else "ask_echo"
                search_engine_dropdown = gr.Dropdown(
                    choices=_engine_choices,
                    value=_default_engine,
                    label="搜索引擎",
                )
                gr.ChatInterface(
                    fn=stream_chat,
                    additional_inputs=[search_engine_dropdown],
                    additional_outputs=[references],
                    type="messages",
                    fill_height=True,
                    css="height: 100%;",
                )
            with gr.Column(scale=1):
                gr.Markdown("<center><h2>📔 Search Records</h2></center>")
                gr.Markdown("> **searched content will by displayed here**")
                references.render()

    demo.launch()
