# BotForLearningEnglish

Telegram-бот для практики разговорного английского: voice-диалог, разбор
ошибок с diff'ом (было/стало), акустическая оценка произношения и
геймификация баллами. Архитектура — функциональный аналог ботов вида
"Supreme Speak Teacher" / Practik Bot.

## Архитектура

```
Telegram (voice/text)
    │
    ▼
aiogram-бот (bot/)
    │
    ├─► Azure Speech Pronunciation Assessment (unscripted)
    │       → Accuracy, Fluency, Prosody + транскрипт
    │
    ├─► LLM-грейдинг (Claude, bot/services/grading.py)
    │       → Grammar, Vocabulary, diff "было/стало", совет
    │
    ├─► Azure TTS → следующая voice-реплика бота
    │
    └─► Postgres (assessments, user_points)
              │
              ▼
      FastAPI Mini App (webapp/)
              │
              ▼
   Telegram WebView: экраны "Объяснение ошибок" и "Оценка произношения"
```

### Почему именно так

- **Pronunciation Assessment вместо просто Whisper** — Whisper даёт только
  транскрипт. Accuracy/Fluency/Prosody — акустические метрики, их считает
  только специализированный сервис (Azure, ELSA, SpeechAce). Azure выбран
  как самый документированный и с гибким pay-as-you-go.
- **Content-оценка (Grammar/Vocabulary) через LLM, а не Azure** — нативная
  content-assessment в Azure Speech SDK retired начиная с версии 1.46+;
  Microsoft сама рекомендует считать это через LLM поверх транскрипта.
- **Mini App, а не инлайн-сообщения** — прогресс-бары и построчный diff
  визуально не влезают в обычное текстовое сообщение Telegram; WebApp даёт
  полноценный HTML/CSS.

## Что уже реализовано

- [x] FSM-диалог, onboarding, voice-ответ бота
- [x] Конвертация Telegram voice (ogg/opus) → WAV 16kHz для Azure SDK
- [x] Интеграция Azure Pronunciation Assessment (unscripted mode)
- [x] LLM-грейдинг грамматики/вокабуляра + генерация diff через Claude
- [x] Синтез voice-реплик бота через Azure TTS
- [x] Начисление баллов, хранение в Postgres
- [x] Mini App: экран разбора ошибок + экран оценки произношения
- [x] Docker Compose для локального запуска (bot + webapp + postgres + redis)

## Что осталось доделать (roadmap)

- [ ] Диалоговый LLM-собеседник — сейчас следующая реплика бота захардкожена
      (`NEXT_QUESTION` в `bot/handlers/voice.py`), нужен полноценный движок
      диалога с контекстом и выбором темы (экран "Меню" с бота ещё не
      реверс-инжинирен)
- [ ] Оплата/подписка и лимит бесплатных сообщений
- [ ] HTTPS-домен для Mini App — Telegram WebApp требует публичный HTTPS,
      локальный `localhost` не подойдёт даже для тестирования на телефоне
- [ ] Кнопка "Текст" под voice-сообщением (просмотр транскрипта с
      переводом по клику на слово) — в этом скелете не реализована
- [ ] Rate limiting / защита от abuse на Azure Speech и LLM вызовах

## Запуск

1. Скопируй `.env.example` в `.env`, заполни ключи (Telegram Bot Token,
   Azure Speech key+region, Anthropic API key)
2. Подними HTTPS-туннель для Mini App на время разработки (например,
   `ngrok http 8000`) и пропиши публичный URL в `WEBAPP_BASE_URL`
3. `docker compose up --build`

## Стек

| Слой | Технология |
|---|---|
| Bot framework | aiogram 3.x |
| Pronunciation scoring | Azure AI Speech — Pronunciation Assessment |
| TTS | Azure AI Speech |
| Content grading (grammar/vocab/diff) | Claude API (Anthropic) |
| Mini App backend | FastAPI |
| БД | PostgreSQL |
| FSM storage | Redis |
