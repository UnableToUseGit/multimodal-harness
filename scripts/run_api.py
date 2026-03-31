import requests
import json

question = """设实数 (a,b,c) 都大于 0，且满足
[
abc=1.
]
证明：
[
\\frac{{1}}{a^3(b+c)}+\\frac{1}{b^3(c+a)}+\\frac{1}{c^3(a+b)}\\ge \\frac{3}{2}.
]
"""

# First API call with reasoning
response = requests.post(
  url="https://api.key77qiqi.com/v1/chat/completions",
  headers={
    "Authorization": "Bearer sk-watd8xzj2vsqAVwLMNviyGno7l6z8s3J8EhdKR0i6uvKAT6y",
    "Content-Type": "application/json",
  },
  data=json.dumps({
    "model": "gpt-5.1",
    "messages": [
        {
          "role": "user",
          "content": question
        }
      ],
    "reasoning_effort": "none"
  })
)


# Extract the assistant message with reasoning_details
response = response.json()
# response = response['choices'][0]['message']
print(response)

