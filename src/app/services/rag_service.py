import json
import asyncio
from fastapi import Request
from langchain_groq import ChatGroq
from .pdf_service import get_vector_store
import logging

logger = logging.getLogger(__name__)

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.2,
    streaming=True,
)

async def generate_rag_stream(request: Request, query: str):
    try:
        yield f"data: {json.dumps({'type': 'thought', 'content': '🤔 جاري التفكير...'})}\n\n"
        await asyncio.sleep(0.3)

        if await request.is_disconnected(): return

        yield f"data: {json.dumps({'type': 'thought', 'content': '🔍 جاري البحث ...'})}\n\n"
        
        vector_store = get_vector_store()
        retriever = vector_store.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 3, "fetch_k": 10}
        )        
        # جلب النصوص المناسبة
        docs = retriever.invoke(query)
        context = "\n\n".join([d.page_content for d in docs])

        if await request.is_disconnected(): return

        yield f"data: {json.dumps({'type': 'thought', 'content': '💡 تم العثور على بعض النتائج...'})}\n\n"

        prompt = f"""أجب عن سؤال العميل بدقة استناداً إلى السياق التالي فقط:
        
        السياق:
        {context}

        السؤال: {query}
        """

        # البث الحقيقي
        async for chunk in llm.astream(prompt):
            if await request.is_disconnected():
                print("⚠️ [Client Disconnected] Aborting stream...")
                break
            
            if chunk.content:
                yield f"data: {json.dumps({'type': 'answer', 'content': chunk.content})}\n\n"

    except Exception as e:
        logger.exception("❌ RAG Stream Error")
        yield f"data: {json.dumps({
            'type': 'error',
            'content': str(e),
        }, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"