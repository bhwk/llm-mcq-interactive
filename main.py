import json
import random
import gradio as gr


def load_questions(json_path) -> list[dict[str, str]]:
    with open(json_path) as f:
        question_list = [json.loads(line.strip()) for line in f]
    return question_list


def random_question(question_list: list[dict[str, str]]) -> dict[str, str]:
    return random.choice(question_list)


def next_question():
    global question, correct_option, options, explanation
    question_object = random_question(questions)
    question = question_object["question"]
    correct_option = question_object["cop"]
    options = [question_object["op" + chr(op)] for op in range(ord("a"), ord("d") + 1)]
    explanation = question_object["exp"]

    return (
        gr.Button(interactive=False),
        gr.update(value=question),
        gr.Radio(
            [(options[i], i + 1) for i in range(len(options))],
        ),
    )


def handle_answer(choice):
    global correct
    if choice == correct_option:
        correct = True
        return (
            gr.Textbox(
                f"""
            Correct!
            {explanation if explanation else ""}"""
            ),
            gr.Button(interactive=correct),
        )
    else:
        return (f"You selected {choice}", gr.Button(interactive=correct))


questions = load_questions("train.json")
question_object = random_question(questions)

question = question_object["question"]
correct_option = question_object["cop"]
options = [question_object["op" + chr(op)] for op in range(ord("a"), ord("d") + 1)]
explanation = question_object["exp"]

selected_option = ""


correct = False

with gr.Blocks() as demo:
    with gr.Row(equal_height=True):
        question_display = gr.Textbox(
            value=question,
            scale=1,
            interactive=False,
        )
        next_button = gr.Button("Next Question", scale=0, interactive=correct)

    radio = gr.Radio(
        [(options[i], i + 1) for i in range(len(options))], label="Select an Option"
    )
    output = gr.Textbox()
    button = gr.Button("Submit")

    button.click(fn=handle_answer, inputs=[radio], outputs=[output, next_button])
    next_button.click(fn=next_question, outputs=[next_button, question_display, radio])


demo.launch()
