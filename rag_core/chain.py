import logging
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from config import PROMPT_TEMPLATE, TOP_K

log = logging.getLogger("studentrag.chain")

def format_docs(docs):
    return "\n\n".join(
        f"[Source: {d.metadata.get('source','unknown')} | Page {d.metadata.get('page_num','N/A')}]\n{d.page_content}"
        for d in docs)

def build_qa_chain(vectorstore, llm):
    prompt = PromptTemplate(template=PROMPT_TEMPLATE, input_variables=["context", "question"])
    retriever = vectorstore.as_retriever(search_kwargs={"k": TOP_K})
    chain = ({"context": retriever | format_docs, "question": RunnablePassthrough()}
             | prompt | llm | StrOutputParser())
    log.info("QA chain built (top_k=%d)", TOP_K)
    return chain, retriever
