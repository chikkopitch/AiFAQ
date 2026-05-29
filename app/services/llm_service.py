import logging

from openai import AsyncOpenAI, OpenAIError

logger = logging.getLogger(__name__)

OPENROUTER_TIMEOUT_SECONDS = 30.0
MAX_ANSWER_LENGTH = 1200
OPENROUTER_ERROR_MESSAGE = (
    "Сейчас не получилось получить ответ. "
    "Пожалуйста, попробуйте позже или свяжитесь с менеджером."
)

SYSTEM_PROMPT = """
Ты AI-ассистент строительной компании.

Правила:
1. Отвечай только на основе базы знаний.
2. Если точной информации нет, честно скажи: "Точную информацию лучше уточнить у менеджера."
3. Не называй точные цены, если в базе знаний есть только примерные.
4. Не обещай сроки и гарантии, если они не указаны.
5. Не давай инженерные заключения, технические расчеты и юридические гарантии.
6. Если клиент спрашивает про стоимость, объясни факторы цены и предложи оставить заявку.
7. Если клиент спрашивает про материалы, объясни общо и предложи консультацию специалиста.
8. Если вопрос не относится к строительству, вежливо скажи, что бот отвечает только по строительным услугам.
9. Отвечай как менеджер: коротко, понятно, доброжелательно.
10. Не используй markdown-таблицы в Telegram-ответах.
""".strip()


class LLMService:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout_seconds: float = OPENROUTER_TIMEOUT_SECONDS,
    ) -> None:
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout_seconds,
        )

    async def answer_client_question(self, question: str, knowledge_base: str) -> str:
        user_prompt = f"""
БАЗА ЗНАНИЙ:
{knowledge_base}

ВОПРОС КЛИЕНТА:
{question}

Сформируй ответ клиенту.
""".strip()

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                max_tokens=550,
                timeout=self.timeout_seconds,
            )
        except OpenAIError:
            logger.warning("OpenRouter request failed")
            return OPENROUTER_ERROR_MESSAGE
        except Exception:
            logger.warning("Unexpected OpenRouter request error")
            return OPENROUTER_ERROR_MESSAGE

        answer = response.choices[0].message.content
        if not answer:
            return "Точной информации в базе знаний нет. Пожалуйста, свяжитесь с менеджером."

        return self._trim_answer(answer.strip())

    @staticmethod
    def _trim_answer(answer: str) -> str:
        if len(answer) <= MAX_ANSWER_LENGTH:
            return answer

        trimmed = answer[:MAX_ANSWER_LENGTH].rstrip()
        sentence_end = max(
            trimmed.rfind("."),
            trimmed.rfind("!"),
            trimmed.rfind("?"),
        )

        if sentence_end >= MAX_ANSWER_LENGTH * 0.6:
            return trimmed[: sentence_end + 1]

        return f"{trimmed.rstrip(' .,;:')}..."
