import dotenv
import random
from agent import create_agent, create_async_agent


dotenv.load_dotenv()  # loads environment variables from .env file


class AsyncQuiz:
    def __init__(self, questions: list[dict[str, str]], agent):
        self.questions = questions
        self.remaining_questions = questions.copy()
        self.current_question = None
        self.agent = agent

    @classmethod
    async def create(cls, questions: list[dict[str, str]]):
        instance = cls(questions, None)
        instance.current_question = instance.get_question()
        instance.agent = await create_async_agent(instance.current_question)
        return instance

    def get_question(self) -> dict[str, str] | None:
        if len(self.remaining_questions) == 0:
            return None
        self.current_question = random.choice(self.remaining_questions)
        self.remaining_questions.remove(self.current_question)
        return self.current_question

    async def update_agent(self):
        self.agent = await create_async_agent(self.current_question)

    def check_answer(self, answer):
        user_answer = f"User's answer: {answer[0]}\n{('User\'s Explanation: ' + answer[1]) if answer[1] else ''}"
        feedback = self.agent.chat(user_answer)  # type: ignore
        if self.agent.shared_variables["Persistent Memory"][
            "User Provided Correct Answer"
        ]:
            return True, feedback
        else:
            return False, feedback


class Quiz:
    def __init__(self, questions: list[dict[str, str]]):
        self.questions = questions
        self.remaining_questions = questions.copy()
        self.current_question = None
        self.agent = create_agent(self.current_question)

    def get_question(self) -> dict[str, str] | None:
        if len(self.remaining_questions) == 0:
            return None
        self.current_question = random.choice(self.remaining_questions)
        self.remaining_questions.remove(self.current_question)
        return self.current_question

    def update_agent(self):
        self.agent = create_agent(self.current_question)

    def check_answer(self, answer):
        user_answer = f"User's answer: {answer[0]}\n{("User's Explanation: "+answer[1]) if answer[1] else ""}"
        feedback = self.agent.chat(user_answer)  # type: ignore
        # if answer == correct_option:
        if self.agent.shared_variables["Persistent Memory"][
            "User Provided Correct Answer"
        ]:
            return True, feedback
        else:
            return False, feedback
