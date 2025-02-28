from rag import search_web
from agentjo import Agent, ConversationWrapper
from llm import llm, llm_async


def create_agent(current_question: dict[str, str] | None) -> Agent:
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
        Some questions may provide an explanation of the correct answer. You may make use of this explanation to guide the user towards the correct answer.
        Do not mention the context in your answer.
        Do not mention anything about an explanation in your answer.
        If needed, search for additional information related to either the user's answer of the question to help guide them better.
        If the user answers correctly, update accordingly.""",
        llm=llm,
        shared_variables=shared_variables,
        global_context=global_context,
        verbose=True,
    ).assign_functions([search_web])

    convo_agent = ConversationWrapper(
        agent, persistent_memory={"User Provided Correct Answer": "type:bool"}
    )
    return convo_agent
