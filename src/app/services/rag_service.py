import json
import asyncio
import logging

from fastapi import Request
from langchain_groq import ChatGroq

from .pdf_service import get_vector_store

logger = logging.getLogger(__name__)

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.2,
    streaming=True,
)


async def retrieve_documents(query: str):
    """
    تشغيل البحث داخل Thread حتى لا نحجب الـ event loop.
    """
    vector_store = get_vector_store()

    retriever = vector_store.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 3,
            "fetch_k": 10,
        },
    )

    return await asyncio.to_thread(
        retriever.invoke,
        query,
    )


async def generate_answer(prompt: str):
    """
    Streaming من LLM.
    """
    async for chunk in llm.astream(prompt):
        if chunk.content:
            yield chunk.content


async def generate_rag_stream(request: Request, query: str):

    retrieval_task = None
    llm_task = None

    try:

        # =========================
        # 1. Start Thinking
        # =========================

        if await request.is_disconnected():
            return

        yield (
            f"data: {json.dumps({
                'type': 'thought',
                'content': '🤔 جاري التفكير...'
            }, ensure_ascii=False)}\n\n"
        )

        await asyncio.sleep(0.3)

        if await request.is_disconnected():
            return

        # =========================
        # 2. Search in chunk vector  by query
        # =========================

        yield (
            f"data: {json.dumps({
                'type': 'thought',
                'content': '🔍 جاري البحث ...'
            }, ensure_ascii=False)}\n\n"
        )

        retrieval_task = asyncio.create_task(
            retrieve_documents(query)
        )

        # ننتظر البحث وفي نفس الوقت نراقب disconnect
        while not retrieval_task.done():

            if await request.is_disconnected():

                logger.info(
                    "⚠️ Client disconnected during retrieval"
                )

                retrieval_task.cancel()

                try:
                    await retrieval_task
                except asyncio.CancelledError:
                    pass

                return

            await asyncio.sleep(0.1)

        docs = await retrieval_task

        # =========================
        # 3. found data
        # =========================

        if await request.is_disconnected():
            return

        context = "\n\n".join(
            d.page_content
            for d in docs
        )

        yield (
            f"data: {json.dumps({
                'type': 'thought',
                'content': '💡 تم العثور على بعض النتائج...'
            }, ensure_ascii=False)}\n\n"
        )

        # =========================
        # 4. Prompt
        # =========================

        prompt = f"""
أجب عن سؤال العميل بدقة استناداً إلى السياق التالي فقط:

السياق:
{context}

السؤال:
{query}
"""

        if await request.is_disconnected():
            return

        # =========================
        # 5. LLM Streaming
        # =========================

        llm_stream = llm.astream(prompt)

        try:

            async for chunk in llm_stream:

                if await request.is_disconnected():

                    logger.info(
                        "⚠️ Client disconnected during LLM generation"
                    )

                    break

                if chunk.content:

                    yield (
                        f"data: {json.dumps({
                            'type': 'answer',
                            'content': chunk.content
                        }, ensure_ascii=False)}\n\n"
                    )

        finally:
            await llm_stream.aclose()

    except asyncio.CancelledError:

        logger.info(
            "⚠️ RAG task cancelled"
        )

        if retrieval_task and not retrieval_task.done():
            retrieval_task.cancel()

        if llm_task and not llm_task.done():
            llm_task.cancel()

        raise

    except Exception as e:

        logger.exception(
            "❌ RAG Stream Error"
        )

        if not await request.is_disconnected():

            yield (
                f"data: {json.dumps({
                    'type': 'error',
                    'content': str(e)
                }, ensure_ascii=False)}\n\n"
            )

    finally:

        if retrieval_task and not retrieval_task.done():
            retrieval_task.cancel()

        if llm_task and not llm_task.done():
            llm_task.cancel()