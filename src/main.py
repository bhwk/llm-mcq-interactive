import dotenv
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

dotenv.load_dotenv()  # loads environment variables from .env file


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
        correct_option = self.current_question["cop"]  # type: ignore
        user_answer = f"User's answer: {answer[0]}\n{("User's explanation for answer: " + answer[1]) if answer[1] else ""}"  # type: ignore
        feedback = agent.run(task=user_answer)
        if agent.shared_variables["Persistent Memory"]["User Provided Correct Answer"]:
            feedback = agent.reply_user(stateful=True)
            return True, feedback
        else:
            feedback = agent.reply_user(stateful=True)
            return False, feedback


css = """
        .radio-group .wrap {
            display: grid !important;
            grid-template-columns: 1fr 1fr;
        }
        """
with gr.Blocks(css=css) as demo:
    questions = load_questions("questions.json")

    quiz = Quiz(questions)
    agent: Agent = create_agent(quiz.current_question)
    active_tab = gr.State("MCQ")

    with gr.Column():
        with gr.Tab("MCQ"):
            with gr.Row(equal_height=True):
                question_display = gr.Textbox(
                    scale=1, interactive=False, label="Question"
                )

            with gr.Row(equal_height=True):
                choices = gr.Radio(
                    [], label="Choices", scale=1, elem_classes="radio-group"
                )

        with gr.Tab("Open-ended"):
            with gr.Row(equal_height=True):
                open_question = gr.Textbox(scale=1, interactive=False, label="Question")

        with gr.Row():
            output = gr.Textbox(interactive=False, scale=1, label="Feedback")
            user_text = gr.Textbox(scale=1, label="User's text explanation")
            with gr.Column():
                submit_button = gr.Button("Submit")
                next_button = gr.Button("Next Question")

    def update_question():
        global agent
        question = quiz.get_question()
        if question is None:
            return (
                gr.update(value="No more questions available"),
                None,
                None,
                None,
                gr.update(value=""),
            )
        agent = create_agent(question)
        return (
            # change question display
            gr.update(value=question["question"]),
            # Populate choices
            gr.update(
                choices=[
                    (question["opa"]),
                    (question["opb"]),
                    (question["opc"]),
                    (question["opd"]),
                ]
            ),
            # Clear output box
            gr.update(value=""),
            # Set next_button to false
            gr.Button(interactive=False),
            # clear user input box
            gr.update(value=""),
        )

    def on_answer(choice, user_answer):
        answer = []
        answer.append(choice)
        answer.append(user_answer)
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

    submit_button.click(
        on_answer, inputs=[choices, user_text], outputs=[next_button, output]
    )
    next_button.click(
        update_question,
        outputs=[question_display, choices, output, next_button, user_text],
    )
    demo.load(
        update_question,
        outputs=[question_display, choices, output, next_button, user_text],
    )


demo.launch(quiet=False, show_error=True)
