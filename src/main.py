import json
import random
from agentjo import Agent

from agent import create_agent

import gradio as gr

answer_map = {
    "1": "opa",
    "2": "opb",
    "3": "opc",
    "4": "opd",
}


def load_questions(json_path) -> list[dict[str, str]]:
    with open(json_path) as f:
        question_list = [json.loads(line.strip()) for line in f]
    return question_list


class Quiz:
    def __init__(self, questions: list[dict[str, str]]):
        self.questions = questions
        self.remaining_questions = questions.copy()
        self.current_question = None

    def get_question(self) -> dict[str, str] | None:
        if len(self.remaining_questions) == 0:
            return None
        self.current_question = random.choice(self.remaining_questions)
        self.remaining_questions.remove(self.current_question)
        return self.current_question

    def check_answer(self, answer):
        global answer_map, agent
        user_answer = self.current_question.get(answer_map["answer"])  # type: ignore
        correct_option = self.current_question["cop"]  # type: ignore
        if answer == correct_option:
            return True, f"Correct!\nExplanation:{self.current_question["exp"]}"  # type: ignore
        else:
            feedback = agent.reply_user(query=user_answer)  # type: ignore
            return False, feedback


questions = load_questions("train.json")


quiz = Quiz(questions)
agent: Agent = create_agent(quiz.current_question)

with gr.Blocks() as demo:
    with gr.Row(equal_height=True):
        question_display = gr.Textbox(scale=1, interactive=False, label="Question")

    choices = gr.Radio([], label="Choices")

    with gr.Row():
        output = gr.Textbox(interactive=False, scale=1, label="Feedback")
        with gr.Column():
            submit_button = gr.Button("Submit")
            next_button = gr.Button("Next Question")

    def update_question():
        global agent
        question = quiz.get_question()
        if question is None:
            return (gr.update(value="No more questions available"), None, None, None)
        agent = create_agent(question)
        return (
            # change question display
            gr.update(value=question["question"]),
            # Populate choices
            gr.update(
                choices=[
                    (question["opa"], 1),
                    (question["opb"], 2),
                    (question["opc"], 3),
                    (question["opd"], 4),
                ]
            ),
            # Clear output box
            gr.update(value=""),
            # Set next_button to false
            gr.Button(interactive=False),
        )

    def on_answer(answer):
        correct, feedback = quiz.check_answer(answer)
        if correct:
            return (
                # set next_button to interactive
                gr.Button(interactive=True),
                # update output box to show answer explanation
                gr.update(value=feedback),
            )
        else:
            # update output box
            return (gr.Button(), gr.update(value=feedback))

    submit_button.click(on_answer, inputs=[choices], outputs=[next_button, output])
    next_button.click(
        update_question, outputs=[question_display, choices, output, next_button]
    )
    demo.load(update_question, outputs=[question_display, choices, output, next_button])


demo.launch()
