# Telegram-бот для строительной компании

Это простой MVP Telegram-бота на Python. Он отвечает клиентам на частые вопросы по строительству и ремонту, использует базу знаний из markdown-файла и умеет собирать заявки на консультацию, замер или расчет стоимости.

Бот работает без базы данных. База знаний хранится в `data/knowledge_base.md`, заявки сохраняются в `data/leads.csv`.

## Что умеет бот

- Отвечает на команды `/start`, `/help`, `/contacts`, `/cancel`.
- Показывает кнопки: `Услуги`, `Цены`, `Сроки`, `Контакты`, `Оставить заявку`.
- Отвечает на текстовые вопросы клиентов по базе знаний.
- Не выдумывает точные цены, сроки и гарантии, если их нет в базе знаний.
- Собирает заявку клиента: имя, телефон, город/район, услугу и описание задачи.
- Сохраняет заявки в CSV-файл.
- Отправляет уведомление админу, если указан `BOT_ADMIN_IDS`.

## Как создать Telegram-бота через BotFather

1. Откройте Telegram.
2. Найдите официальный бот `@BotFather`.
3. Отправьте команду `/newbot`.
4. Укажите название бота.
5. Укажите username бота. Он должен заканчиваться на `bot`, например `my_company_bot`.
6. BotFather выдаст токен. Сохраните его и никому не показывайте.
7. Этот токен нужно вставить в `.env` как `TELEGRAM_BOT_TOKEN`.

## Как получить OpenRouter API key

1. Откройте сайт [OpenRouter](https://openrouter.ai/).
2. Войдите в аккаунт или зарегистрируйтесь.
3. Перейдите в раздел API Keys: [openrouter.ai/keys](https://openrouter.ai/keys).
4. Создайте новый ключ.
5. Скопируйте ключ и вставьте его в `.env` как `OPENROUTER_API_KEY`.

## Как создать `.env`

1. Скопируйте файл `.env.example`.
2. Переименуйте копию в `.env`.
3. Заполните значения.

Пример:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=openai/gpt-oss-120b:free
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
BOT_ADMIN_IDS=
```

Не добавляйте настоящий `.env` в git. В нем лежат секреты.

## Переменные окружения

`TELEGRAM_BOT_TOKEN` - токен Telegram-бота от BotFather.

`OPENROUTER_API_KEY` - API-ключ OpenRouter.

`OPENROUTER_MODEL` - модель для ответов. По умолчанию используется `openai/gpt-oss-120b:free`.

`OPENROUTER_BASE_URL` - адрес OpenRouter OpenAI-compatible API. Для этого проекта: `https://openrouter.ai/api/v1`.

`BOT_ADMIN_IDS` - Telegram ID админов для уведомлений о заявках. Можно оставить пустым. Если админов несколько, укажите через запятую:

```env
BOT_ADMIN_IDS=123456789,987654321
```

## Как установить зависимости

Создайте виртуальное окружение:

```bash
python -m venv .venv
```

Активируйте окружение в Windows:

```powershell
.venv\Scripts\activate
```

Установите зависимости:

```bash
pip install -r requirements.txt
```

## Как запустить бота

Запуск из папки проекта:

```bash
python -m app.main
```

Если все настроено правильно, бот начнет принимать сообщения в Telegram.

## Как редактировать базу знаний

База знаний находится здесь:

```text
data/knowledge_base.md
```

Этот файл можно редактировать без изменения кода. Добавляйте туда реальные услуги, контакты, условия оплаты, гарантии, примеры ответов и правила расчета стоимости.

Важно: если в базе знаний нет точной цены, срока или гарантии, бот должен предложить уточнить информацию у менеджера.

## Где сохраняются заявки

Заявки сохраняются в файл:

```text
data/leads.csv
```

Формат CSV:

```csv
created_at,telegram_id,username,name,phone,location,service,description
```

Файл создается автоматически после первой заявки.

## Как задеплоить на хостинг

Общий порядок:

1. Загрузите проект на сервер или хостинг.
2. Установите Python 3.11 или новее.
3. Установите зависимости:

```bash
pip install -r requirements.txt
```

4. Добавьте переменные окружения из `.env.example` в настройках хостинга.
5. Укажите команду запуска:

```bash
python -m app.main
```

6. Убедитесь, что процесс бота работает постоянно. На хостинге для этого обычно используют сервис, worker, background process или process manager.

## Частые ошибки

### Неправильный токен Telegram

Если токен неверный, бот не сможет подключиться к Telegram. Проверьте `TELEGRAM_BOT_TOKEN` и при необходимости создайте новый токен через BotFather.

### Не заполнен `.env`

Если обязательной переменной нет, приложение остановится с ошибкой вида:

```text
Missing required env var: TELEGRAM_BOT_TOKEN
```

Заполните `.env` или добавьте переменные окружения на хостинге.

### OpenRouter не отвечает

Если OpenRouter временно недоступен или ключ неверный, бот вернет пользователю сообщение:

```text
Сейчас не получилось получить ответ. Пожалуйста, попробуйте позже или свяжитесь с менеджером.
```

Проверьте `OPENROUTER_API_KEY`, `OPENROUTER_MODEL` и `OPENROUTER_BASE_URL`.

### Не установлены зависимости

Если появляется ошибка вроде `ModuleNotFoundError`, установите зависимости:

```bash
pip install -r requirements.txt
```

### Бот не отвечает на заявки админу

Проверьте `BOT_ADMIN_IDS`. Там должны быть Telegram ID админов, а не username.

## Полезные ссылки

- Telegram BotFather и создание бота: [официальная документация Telegram](https://core.telegram.org/bots/features#botfather).
- Telegram tutorial по получению токена: [From BotFather to Hello World](https://core.telegram.org/bots/tutorial).
- OpenRouter API: [официальная документация OpenRouter](https://openrouter.ai/docs/api-reference/overview).
- OpenRouter API keys: [openrouter.ai/keys](https://openrouter.ai/keys).
