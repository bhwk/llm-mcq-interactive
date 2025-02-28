import dotenv
from questions import questions_from_pdf
from quiz import Quiz

import gradio as gr

dotenv.load_dotenv()  # loads environment variables from .env file


css = """
        .radio-group .wrap {
            display: grid !important;
            grid-template-columns: 1fr 1fr;
        }
        """
with gr.Blocks(css=css) as demo:
    questions: list[dict] = questions_from_pdf("test.pdf")["Questions"]  # type: ignore

    quiz = Quiz(questions)
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
        question = quiz.get_question()
        if question is None:
            return (
                gr.update(value="No more questions available"),
                None,
                None,
                None,
                gr.update(value=""),
            )
        quiz.update_agent()
        return (
            # change question display
            gr.update(value=question["question"]),
            # Populate choices
            gr.update(choices=[option for option in question["Options"]]),
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
