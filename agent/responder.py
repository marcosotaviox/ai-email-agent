"""
Email reply generation chain.
Uses GPT-4o to produce professional, human-like responses.
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a professional email assistant.
Write a concise, human-like reply to the email below.

Rules:
- Category context provided: {category}
- Use Australian English spelling (organise, colour, authorise)
- Never start with "I hope this email finds you well"
- Never mention you are an AI
- Be direct and professional
- Maximum 150 words unless the email requires more detail
- Sign off as: Kind regards,\\nThe Team"""),
    ("human", "From: {sender}\nSubject: {subject}\n\nOriginal email:\n{body}"),
])


def build_responder(api_key: str):
    """Return a callable responder chain."""
    llm = ChatOpenAI(model="gpt-4o", temperature=0.4, api_key=api_key)
    chain = _PROMPT | llm | StrOutputParser()

    def respond(email: dict, category: str) -> str:
        return chain.invoke({
            "category": category,
            "sender": email["from"],
            "subject": email["subject"],
            "body": email["body"][:2000],
        })

    return respond