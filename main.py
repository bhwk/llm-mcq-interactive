import json
import os
import random

import gradio as gr

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
        correct_option = self.current_question["cop"]  # type: ignore
        if answer == correct_option:
            return True, f"Correct!\nExplanation:{self.current_question["exp"]}"  # type: ignore
        else:
            return False, "Incorrect answer!"


questions = load_questions("train.json")

quiz = Quiz(questions)

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
        question = quiz.get_question()
        if question is None:
            return (gr.update(value="No more questions available"), None, None, None)
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
            # set next button to false, update output box
            return (gr.Button(), gr.update(value=feedback))

    submit_button.click(on_answer, inputs=[choices], outputs=[next_button, output])
    next_button.click(
        update_question, outputs=[question_display, choices, output, next_button]
    )
    demo.load(update_question, outputs=[question_display, choices, output, next_button])


demo.launch()
