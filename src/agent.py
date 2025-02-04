import os
from agentjo import Agent

answer_map = {
    "1": "opa",
    "2": "opb",
    "3": "opc",
    "4": "opd",
}

OLLAMA_URL = os.environ.get("OLLAMA_URL")


def llm(system_prompt: str, user_prompt: str) -> str:
    from openai import OpenAI

    client = OpenAI(
        base_url=(OLLAMA_URL if OLLAMA_URL is not None else "http://localhost:11434")
        + "/v1",
        api_key="ollama",
    )

    response = client.chat.completions.create(
        model="qwen2.5:32b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content  # type: ignore


def create_agent(current_question: dict[str, str] | None) -> Agent:
    global answer_map
    if current_question is not None:
        question = current_question["question"]
        correct_answer = answer_map.get(current_question["cop"])
        explanation = current_question["exp"]
        shared_variables = {
            "question": question,  # type: ignore
            "correct_answer": correct_answer,  # type: ignore
            "explanation": explanation,  # type: ignore
        }
    else:
        shared_variables = {}

    agent = Agent(
        "Tutor",
        """Based on the answer given by the user, guide the user towards the correct answer without giving away the answer.
        Never give the actual answer to the user.
        Some questions may provide an explanation of the correct answer.
        You may use this explanation to guide the user towards answering correctly.""",
        llm=llm,
        shared_variables=shared_variables,
    )
    return agent
