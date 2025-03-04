# TODO: Generate questions here
from pdf import extract_pdf_text
from agentjo import strict_json, strict_json_async
from llm import llm, llm_async


def questions_from_pdf(file: str):
    extracted_text = extract_pdf_text(file)
    res = strict_json(
        system_prompt="Generate 5 multiple choice questions from the extracted text.",
        user_prompt=extracted_text,
        output_format={
            "Questions": "The list of questions, type: List[Dict['Question', 'Options', 'Correct Answer', 'Explanation']]",
        },
        llm=llm,
    )

    return res


async def async_questions_from_pdf(file: str):
    extracted_text = extract_pdf_text(file)
    res = strict_json_async(
        system_prompt="Generate 5 multiple choice questions from the extracted text.",
        user_prompt=extracted_text,
        output_format={
            "Questions": "The list of questions, type: List[Dict['Question', 'Options', 'Correct Answer', 'Explanation']]",
        },
        llm=llm_async,
    )

    return res
