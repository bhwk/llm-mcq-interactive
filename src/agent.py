from rag import search_web
from agentjo import Agent, ConversationWrapper
from llm import llm

answer_map = {
    "1": "opa",
    "2": "opb",
    "3": "opc",
    "4": "opd",
}


def create_agent(
    current_question: dict[str, str] | None, functions: list = [search_web]
) -> Agent:
    global answer_map
    if current_question is not None:
        question = current_question["Question"]
        correct_answer = current_question["Correct Answer"]
        explanation = current_question["Explanation"]
        shared_variables = {
            "question": question,  # type: ignore
            "correct_answer": correct_answer,  # type: ignore
            "explanation": explanation,  # type: ignore
            "information": [],
        }
        global_context = "Question: <question>\nCorrect answer: <correct_answer>\nExplanation: <explanation>\nInformation Searched: <information>"
    else:
        shared_variables = {
            "information": [],
        }
        global_context = "Information Searched: <information>"

    agent = Agent(
        "Tutor",
        """Based on the answer given by the user, guide the user towards the correct answer without giving away the answer.
        Think why the user would give this answer.
        Never give the actual answer to the user.
        Some questions may provide an explanation of the correct answer. You may make use of this explanation to guide the user towards the correct answer.
        Do not mention the context in your answer.
        Do not let the user know that you have access to extra context.
        Your answer should not contain any mentions of a "context".
        Do not mention anything about an explanation in your answer.
        If needed, search for additional information related to either the user's answer of the question to help guide them better.
        Ensure that you do not mention the correct answer in your reply.""",
        llm=llm,
        shared_variables=shared_variables,
        global_context=global_context,
        verbose=True,
    ).assign_functions(functions)

    convo_agent = ConversationWrapper(
        agent, persistent_memory={"User Provided Correct Answer": "type:bool"}
    )
    return convo_agent
