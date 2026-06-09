"""Bài Tập 2: Tools và Knowledge Base.

Ví dụ hoàn chỉnh về cách thêm tool và knowledge base entry mới.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool

from common.llm import get_llm

# Knowledge base
LEGAL_KNOWLEDGE = [
    {
        "id": "ucc_breach",
        "keywords": ["breach", "contract", "remedies", "damages", "ucc"],
        "text": (
            "Under the Uniform Commercial Code (UCC) Article 2, remedies for breach of contract "
            "include: (1) expectation damages; (2) consequential damages; (3) specific performance; "
            "(4) cover damages. Statute of limitations is typically 4 years (UCC § 2-725)."
        ),
    },
    {
        "id": "labor_law",
        "keywords": ["lao động", "sa thải", "hợp đồng lao động", "người lao động", "bộ luật lao động"],
        "text": (
            "Theo Bộ luật Lao động Việt Nam, việc chấm dứt hợp đồng lao động phải có căn cứ "
            "hợp pháp, tuân thủ thời hạn báo trước và thanh toán đầy đủ lương, trợ cấp, bảo hiểm "
            "cùng các quyền lợi liên quan. Sa thải trái luật có thể dẫn đến nghĩa vụ nhận người "
            "lao động trở lại, bồi thường tiền lương và các khoản thiệt hại phát sinh."
        ),
    },
]


@tool
def search_legal_knowledge(query: str) -> str:
    """Tìm kiếm trong knowledge base pháp lý."""
    query_lower = query.lower()
    for entry in LEGAL_KNOWLEDGE:
        if any(kw in query_lower for kw in entry["keywords"]):
            return f"[{entry['id']}] {entry['text']}"
    return "Không tìm thấy thông tin liên quan."


@tool
def check_statute_of_limitations(case_type: str) -> str:
    """Kiểm tra thời hiệu khởi kiện theo loại vụ việc."""
    case_lower = case_type.lower()
    if any(kw in case_lower for kw in ["contract", "hợp đồng", "breach"]):
        return "Tranh chấp hợp đồng: thời hiệu thường là 3 năm theo pháp luật Việt Nam; UCC Article 2 thường là 4 năm tại Hoa Kỳ."
    if any(kw in case_lower for kw in ["labor", "lao động", "sa thải"]):
        return "Tranh chấp lao động: thường là 1 năm kể từ ngày phát hiện quyền, lợi ích hợp pháp bị xâm phạm."
    if any(kw in case_lower for kw in ["tort", "bồi thường", "thiệt hại"]):
        return "Yêu cầu bồi thường thiệt hại ngoài hợp đồng: thường là 3 năm kể từ ngày biết hoặc phải biết quyền lợi bị xâm phạm."
    return "Chưa có dữ liệu thời hiệu cho loại vụ việc này. Cần kiểm tra luật áp dụng và tình tiết cụ thể."


async def main():
    load_dotenv()
    llm = get_llm()
    
    tools = [search_legal_knowledge, check_statute_of_limitations]
    llm_with_tools = llm.bind_tools(tools)
    
    question = "Thời hiệu khởi kiện vụ vi phạm hợp đồng là bao lâu?"
    
    messages = [
        SystemMessage(content="Bạn là chuyên gia pháp lý. Sử dụng tools để tra cứu thông tin."),
        HumanMessage(content=question),
    ]
    
    print(f"Câu hỏi: {question}\n")
    
    # First LLM call - decide which tools to use
    response = await llm_with_tools.ainvoke(messages)
    messages.append(response)
    
    # Execute tools if requested
    if response.tool_calls:
        for tool_call in response.tool_calls:
            print(f"🔧 Gọi tool: {tool_call['name']}")
            tool_result = None
            
            if tool_call["name"] == "search_legal_knowledge":
                tool_result = search_legal_knowledge.invoke(tool_call["args"])
            elif tool_call["name"] == "check_statute_of_limitations":
                tool_result = check_statute_of_limitations.invoke(tool_call["args"])
            
            if tool_result:
                messages.append(ToolMessage(content=tool_result, tool_call_id=tool_call["id"]))
        
        # Second LLM call - synthesize final answer
        final_response = await llm_with_tools.ainvoke(messages)
        print(f"\n✅ Kết quả:\n{final_response.content}")
    else:
        print(f"\n✅ Kết quả:\n{response.content}")


if __name__ == "__main__":
    asyncio.run(main())
