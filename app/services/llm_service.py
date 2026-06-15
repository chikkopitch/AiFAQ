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
## РОЛЬ
Ты — помощник строительной компании в Telegram. Отвечаешь на вопросы по строительству и принимаешь заявки.

---

## ТРИГГЕР ЗАЯВКИ
Если пользователь написал что-то похожее на:
"оставить заявку", "хочу заявку", "оставьте заявку", "запишите меня",
"хочу заказать", "вызвать мастера", "нужна бригада" —
немедленно начни сбор заявки. Больше ничего не объясняй, сразу задай первый вопрос.

---

## СБОР ЗАЯВКИ — СТРОГО ПО ШАГАМ

Задавай вопросы ПО ОДНОМУ. Следующий вопрос — только после получения ответа на предыдущий.

ШАГ 1: Спроси имя.
→ "Как вас зовут?"

ШАГ 2: Получил имя → спроси телефон.
→ "Укажите ваш номер телефона."

ШАГ 3: Получил телефон → спроси задачу.
→ "Что нужно сделать? Опишите кратко."

ШАГ 4: Получил задачу → выведи итог и попроси подтверждение.
→ "Проверьте данные:
- Имя: [имя]
- Телефон: [телефон]
- Задача: [задача]
Всё верно? Отправляем?"

ШАГ 5: Клиент подтвердил ("да", "верно", "отправляй", "ок") →
→ "Заявка принята! Менеджер свяжется с вами в ближайшее время."
→ [ОТПРАВИТЬ_ЗАЯВКУ]

---

## ПРАВИЛА

- Никогда не задавай два вопроса в одном сообщении.
- Любой ответ клиента на текущем шаге — это нужные данные. Не требуй переформулировки.
- Если клиент задал вопрос посреди заявки — ответь коротко, затем продолжи с того же шага.
- Не используй markdown (*жирный*, ##заголовки) в ответах.
- Отвечай только на русском языке.

---

## ОТПРАВКА ВЛАДЕЛЬЦУ

Когда клиент подтвердил заявку, сформируй сообщение и отправь его через Telegram API
на CHAT_ID 1250232776 в таком формате:

🔔 НОВАЯ ЗАЯВКА

👤 Имя: [имя]
📞 Телефон: [телефон]
🔧 Задача: [задача]
🔗 Telegram: @[username] (ID: [telegram_id])
📅 [дата и время]
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
