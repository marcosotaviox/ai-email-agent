"""
Email classification chain.
Uses GPT-4o with structured JSON output to categorise incoming emails.
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from config.settings import EMAIL_CATEGORIES


class ClassificationResult(BaseModel):
    category: str = Field(description=f"One of: {EMAIL_CATEGORIES}")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")
    reasoning: str = Field(description="Brief rationale for the classification")


_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an email classification engine.
Classify the incoming email into exactly one of these categories: {categories}.
Respond ONLY with valid JSON — no preamble, no markdown, no explanation outside the JSON.

Required JSON format:
{{
  "category": "<category>",
  "confidence": <float between 0.0 and 1.0>,
  "reasoning": "<one sentence explanation>"
}}"""),
    ("human", "From: {sender}\nSubject: {subject}\n\nBody:\n{body}"),
])

_parser = JsonOutputParser(pydantic_object=ClassificationResult)


def build_classifier(api_key: str):
    """Return a callable classifier chain."""
    llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=api_key)
    chain = _PROMPT | llm | _parser

    def classify(email: dict) -> dict:
        return chain.invoke({
            "categories": ", ".join(EMAIL_CATEGORIES),
            "sender": email["from"],
            "subject": email["subject"],
            "body": email["body"][:2000],
        })

    return classify