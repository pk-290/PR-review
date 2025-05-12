# from langchain.tools import Tool
# from langchain.prompts import PromptTemplate
# from langchain.agents import initialize_agent, AgentType
# import asyncio
# from dotenv import load_dotenv
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain.prompts import PromptTemplate

# load_dotenv()


# # 1. Define a simple linter tool that returns a static linting result for demonstration
# def linter_tool(code_hunk: str) -> str:
#     """
#     A mock linting tool that analyzes a code hunk and returns lint comments.
#     """
#     return (
#         "Lint Report:\n"
#         "- Line 1: Missing module docstring.\n"
#         "- Line 3: Variable name 'x' is too short.\n"
#         "- Line 5: Line too long (85 > 79 characters)."
#     )

# def initialize_llm():
#     llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
#     return llm
# # 2. Wrap it as a LangChain Tool
# tool_linter = Tool(
#     name="linter",
#     func=linter_tool,
#     description="Analyzes a code hunk and returns linting suggestions."
# )


# # 4. Define an async chain executor that can call the linter tool
# async def aexecute_chain(prompt_template: str, input_vars: dict, parser=None) -> str:
#     # If parser is provided, include format instructions in the prompt
#     partial_vars = {}
#     if parser:
#         prompt_template += "\n{format_instructions}"
#         partial_vars = {"format_instructions": parser.get_format_instructions()}

#     # Build the prompt
#     prompt = PromptTemplate(
#         template=prompt_template,
#         input_variables=list(input_vars.keys()),
#         partial_variables=partial_vars
#     )

#     # Initialize LLM and Agent to use our linter tool
#     llm = initialize_llm()
#     agent = initialize_agent(
#         tools=[tool_linter],
#         llm=llm,
#         verbose=False
#     )

#     # Render template and let agent decide to call tool
#     formatted = prompt.format(**input_vars)
#     # Agent will call the linter tool as needed
#     response = await agent.ainvoke(formatted)
#     return response


# # 5. Static code hunk and prompt
# static_hunk = '''
# import os
# x= 1
# print(    "Hello, world!" )  
# '''
# prompt_tmpl = """You are a code review assistant.review the code hunk and provide feeback, also use linter tools hunk: {hunk}"""

# # 6. Run the async executor
# async def main():
#     result = await aexecute_chain(
#         prompt_template=prompt_tmpl,
#         input_vars={"hunk": static_hunk}
#     )
#     print("----- Agent + Linter Output -----")
#     print(result)

# # Entry point

# asyncio.run(main())