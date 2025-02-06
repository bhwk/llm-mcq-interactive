import os

OLLAMA_URL = os.environ.get("OLLAMA_URL")


def llm(system_prompt: str, user_prompt: str) -> str:
    from openai import OpenAI

    client = OpenAI(
        base_url=(OLLAMA_URL if OLLAMA_URL is not None else "http://localhost:11434")
        + "/v1",
        api_key="ollama",
    )

    response = client.chat.completions.create(
        model="qwen2.5:32k_ctx",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content  # type: ignore
