# TODO: Generate questions here
from pdf import extract_pdf_text
from agentjo import strict_json
from llm import llm


def questions_from_pdf(file: str):
    extracted_text = extract_pdf_text(file)
    res = strict_json(
        system_prompt="You are a multiple choice question generator that generates questions from a user's text.",
        user_prompt=extracted_text,
        output_format={
            "Questions": [
                {
                    "Question": "The question to ask",
                    "Options": "A list of 4 possible answers to this question with only 1 correct answer, type: List[str]",
                    "Correct Answer": "The correct answer from the 4 possible answers, type: str",
                    "Explanation": "The explanation for why the answer is correct",
                }
            ]
        },
        llm=llm,
    )

    return res
