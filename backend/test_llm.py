from llm_client import call_llm

response = call_llm(
    "kimi-k2-instruct-0905",
    "Say hello"
)

print(response)
