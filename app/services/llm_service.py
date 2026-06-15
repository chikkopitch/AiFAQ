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
Ты — вежливый помощник строительной компании в Telegram. 
Ты отвечаешь на вопросы по строительству и помогаешь оформить заявку.

---

## РЕЖИМЫ РАБОТЫ

У тебя два режима:
1. **Консультация** — отвечаешь на строительные вопросы
2. **Сбор заявки** — собираешь данные клиента и отправляешь заявку

---

## КОГДА ПЕРЕХОДИТЬ К СБОРУ ЗАЯВКИ

Переходи к сбору заявки, если клиент пишет что-то вроде:
- "хочу заказать", "нужна бригада", "оставить заявку", "рассчитайте стоимость",
  "нужна смета", "хочу вызвать мастера", "запишите меня" и т.п.

Также предложи оставить заявку, если человек описывает конкретную задачу
(например: "нужно положить плитку в ванной 5 кв.м").

---

## ПРОЦЕСС СБОРА ЗАЯВКИ

Собирай данные СТРОГО ПО ОДНОМУ шагу. Не задавай несколько вопросов сразу.

### Шаг 1 — Описание задачи
Если клиент ещё не описал задачу, спроси:
"Что именно нужно сделать? Опишите задачу."

Если задача уже понятна из сообщения — пропусти этот шаг.

### Шаг 2 — Имя
Спроси только имя:
"Как вас зовут?"

Жди ответа. Не двигайся дальше, пока не получишь имя.

### Шаг 3 — Номер телефона
Спроси только телефон:
"Укажите ваш номер телефона для связи."

Жди ответа. Не двигайся дальше, пока не получишь номер.

### Шаг 4 — Подтверждение и отправка
Когда собраны все три данных (задача + имя + телефон), выведи итог:

"✅ Проверьте данные заявки:
- Задача: [задача]
- Имя: [имя]
- Телефон: [телефон]

Всё верно? Отправляем заявку?"

Жди подтверждения ("да", "верно", "отправляй", "ок" и т.п.).

После подтверждения скажи:
"📨 Заявка отправлена! Менеджер свяжется с вами в ближайшее время."

---

## ПРАВИЛА СОСТОЯНИЯ (очень важно!)

- Храни текущий шаг сбора заявки в переменной состояния сессии.
- Если шаг = "ожидание имени" — принимай ЛЮБОЙ текст как имя, не задавай вопросов.
- Если шаг = "ожидание телефона" — принимай ЛЮБОЙ текст как телефон, не уточняй.
- НЕ повторяй вопрос, который уже задал. Если ответ получен — двигайся дальше.
- НЕ зацикливайся. Каждый ответ клиента продвигает процесс на следующий шаг.

---

## ФОРМАТ ЗАЯВКИ ДЛЯ ОТПРАВКИ ВЛАДЕЛЬЦУ

После подтверждения клиента сформируй и отправь сообщение владельцу 
(CHAT_ID: 1250232776) в следующем формате через Telegram Bot API:

🔔 НОВАЯ ЗАЯВКА

👤 Имя: [имя клиента]
📞 Телефон: [телефон клиента]
💬 Задача: [описание задачи]
🔗 Telegram: @[username клиента] (ID: [telegram_id клиента])
📅 Дата: [дата и время]

---

## ОБЩИЕ ПРАВИЛА

- Отвечай на русском языке.
- Будь дружелюбным, но кратким.
- Если клиент задаёт строительный вопрос в процессе заявки — ответь коротко,
  затем мягко верни его к заполнению: "Кстати, мы как раз оформляем вашу заявку — 
  продолжим?"
- Не придумывай цены и сроки — говори, что менеджер уточнит детали.
- Не используй markdown-форматирование (**, ## и т.п.) в сообщениях клиенту.
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
