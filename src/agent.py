import os
from agentjo import Agent
from rag import search_web

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


def create_agent(
    current_question: dict[str, str] | None, functions: list = [search_web]
) -> Agent:
    global answer_map
    if current_question is not None:
        question = current_question["question"]
        correct_answer = current_question.get(answer_map.get(current_question["cop"]))  # type: ignore
        explanation = current_question["exp"]
        shared_variables = {
            "question": question,  # type: ignore
            "correct_answer": correct_answer,  # type: ignore
            "explanation": explanation,  # type: ignore
        }
        global_context = "Question: <question>\nCorrect answer: <correct_answer>\nExplanation: <explanation>"
    else:
        shared_variables = {}
        global_context = ""

    agent = Agent(
        "Tutor",
        """Based on the answer given by the user, guide the user towards the correct answer without giving away the answer.
        Think why the user would give this answer.
        Never give the actual answer to the user.
        Some questions may provide an explanation of the correct answer. You may make use of this explanation to guide the user towards the correct answer.
        Do not mention anything about an explanation in your answer.
        You may want to search for information about either the answer or question that could help you explain better to the user.
        Ensure that you do not mention the correct answer in your reply.""",
        llm=llm,
        shared_variables=shared_variables,
        global_context=global_context,
    ).assign_functions(functions)
    return agent
