from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from app.logging_wrapper import log_async_exceptions,log_exceptions

load_dotenv()

rate_limiter = InMemoryRateLimiter(
    requests_per_second=0.2,    
    check_every_n_seconds=0.1,   # check every 100 ms
    max_bucket_size=5            # allow small bursts
)

@log_async_exceptions
async def aexecute_chain(prompt_template, input_vars, parser=None):
    try:
        if parser:
            prompt_template += "\n {format_instructions} "
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=list(input_vars.keys()),
            partial_variables={} if parser is None else {"format_instructions": parser.get_format_instructions()}
        )
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash",rate_limiter=rate_limiter)
        chain = prompt | llm | (parser if parser else lambda x: x)
        response = await chain.ainvoke(input_vars)
        return response
    except Exception as e:
        raise RuntimeError("Failed to execute LLM chain") from e
    
@log_exceptions
def execute_chain(prompt_template, input_vars, parser=None):
        if parser:
            prompt_template += "\n {format_instructions} "
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=list(input_vars.keys()),
            partial_variables={} if parser is None else {"format_instructions": parser.get_format_instructions()}
        )
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash",rate_limiter=rate_limiter)
        chain = prompt | llm | (parser if parser else lambda x: x)
        response = chain.invoke(input_vars)
        if parser:
             return response
        return response.content

