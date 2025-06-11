# handlers.py
import logging
from datetime import datetime
import aiohttp

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes

from config import BTN_SETTINGS, BTN_KNOWLEDGE, BTN_CHANGE, BTN_BACK, ADMIN_GROUP_ID, F5AI_API_KEY
from db import save_user, get_user, save_history_message, get_history, get_user_by_thread, set_bot_enabled

# Клавиатура основного меню с двумя кнопками
def get_main_menu_reply_keyboard():
    keyboard = [[BTN_SETTINGS, BTN_KNOWLEDGE]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

# Клавиатура подменю с кнопками «Изменить» и «Назад»
def get_update_menu_reply_keyboard():
    keyboard = [[BTN_CHANGE, BTN_BACK]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.id == ADMIN_GROUP_ID:
        return

    user = update.effective_user
    user_id = user.id

    user_data_db = await get_user(user_id)
    admin_thread_id = user_data_db.get("admin_thread_id") if user_data_db else None

    if not admin_thread_id:
        try:
            topic = await context.bot.create_forum_topic(
                chat_id=ADMIN_GROUP_ID,
                name=f"Диалог с {user.full_name}"
            )
            admin_thread_id = topic.message_thread_id
        except Exception as e:
            logging.error(f"Ошибка создания темы: {e}")
            msg = await context.bot.send_message(
                chat_id=ADMIN_GROUP_ID,
                text=f"Новый диалог с {user.full_name}"
            )
            admin_thread_id = msg.message_id

        await save_user(user_id, admin_thread_id=admin_thread_id)

    await context.bot.send_message(
        chat_id=ADMIN_GROUP_ID,
        text=f"Начат новый диалог с пользователем: {user.full_name} (ID: {user.id})",
        message_thread_id=admin_thread_id,
        reply_markup=ReplyKeyboardRemove()
    )

    welcome_message = (
        "Привет! 👋\n\n"
        "Здесь ты можешь создать свою демо-версию ИИ-бота и протестировать её прямо в этом чате! 🚀  \n\n"
        "Просто загрузи информацию о том, кто твой бот и что он должен делать, а затем добавь область знаний, по которой он будет отвечать.  \n"
        "🔧 Настройки — задают стиль общения, язык и правила работы бота.  \n"
        "📚 Знания — определяют, на какие вопросы бот сможет отвечать.  \n\n"
        "Попробуй задать вопрос — бот ответит, используя загруженные данные. Создавай, тестируй, экспериментируй! 🤖✨"
    )

    await update.message.reply_text(
        welcome_message,
        reply_markup=get_main_menu_reply_keyboard(),
        parse_mode='Markdown'
    )

async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.id == ADMIN_GROUP_ID:
        return

    user_id = update.effective_user.id
    text = update.message.text

    if text == BTN_SETTINGS:
        user_data = await get_user(user_id)
        settings = user_data.get("settings") if user_data else None

        if settings:
            await update.message.reply_text(
                f"Текущие настройки:\n{settings}"
            )
            instruction_text = (
                "🔧 Изменить настройки действующего бота\n\n"
                "Ты можешь обновить параметры работы уже созданного бота, чтобы он отвечал ещё точнее и соответствовал твоим нуждам.\n\n"
                "Измени или добавь:\n"
                "✅ Стиль общения\n"
                "✅ Язык\n"
                "✅ Правила поведения\n"
                "✅ Дополнительные параметры\n\n"
                "Все изменения будут сразу отражены в работе бота! 🚀"
            )
        else:
            await update.message.reply_text("Настройки не установлены.")
            instruction_text = (
                "🔧 Настройки бота\n\n"
                "Здесь ты можешь задать основные параметры, которые определяют, как будет общаться твой ИИ-бот.\n\n"
                "Что можно настроить?\n"
                "✅ Стиль общения — дружелюбный, формальный, экспертный и т. д.\n"
                "✅ Язык — на каком языке бот будет отвечать.\n"
                "✅ Правила поведения — какие темы затрагивать, а какие избегать.\n"
                "✅ Дополнительные параметры — индивидуальные особенности работы бота.\n\n"
                "Настрой бота так, как тебе нужно, и переходи к добавлению знаний! 🚀\n\n"
                "⭐️ Чем больше и структурированнее информация, тем точнее будут ответы!"
            )

        await update.message.reply_text(
            instruction_text,
            reply_markup=get_update_menu_reply_keyboard()
        )
        context.user_data['current_view'] = 'settings'

    elif text == BTN_KNOWLEDGE:
        user_data = await get_user(user_id)
        knowledge = user_data.get("knowledge") if user_data else None

        if knowledge:
            await update.message.reply_text(
                f"Текущие знания:\n{knowledge}"
            )
            instruction_text = (
                "📚 Изменить или обновить знания действующего бота\n\n"
                "Ты можешь легко обновить информацию, на основе которой работает твой бот. Это поможет ему давать ещё более точные и полезные ответы.\n\n"
                "Что можно изменить или добавить:\n"
                "✅ Обновить существующие знания\n"
                "✅ Добавить новые темы или вопросы\n"
                "✅ Исправить неточные данные\n"
                "✅ Удалить устаревшую информацию\n\n"
                "Внеси изменения, и твой бот сразу начнёт использовать актуальные знания! 🚀"
            )
        else:
            await update.message.reply_text("Знания не установлены.")
            instruction_text = (
                "📚 Добавление знаний для бота\n\n"
                "Теперь пришло время загрузить информацию, на основе которой твой бот будет отвечать. Чем больше и точнее ты заполнишь данные, тем более полезные ответы он будет давать!\n\n"
                "Добавь знания по темам, по которым бот должен быть экспертом, например:\n"
                "✅ Общие сведения\n"
                "✅ Технические или специализированные знания\n"
                "✅ Часто задаваемые вопросы и ответы\n"
                "✅ Полезные рекомендации и советы\n\n"
                "После добавления знаний, бот будет готов отвечать на твои запросы! 🚀"
            )

        await update.message.reply_text(
            instruction_text,
            reply_markup=get_update_menu_reply_keyboard()
        )
        context.user_data['current_view'] = 'knowledge'

async def handle_update_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.id == ADMIN_GROUP_ID:
        return

    text = update.message.text
    if text == BTN_CHANGE:
        current_view = context.user_data.get('current_view')
        if current_view == 'settings':
            context.user_data['awaiting_update_settings'] = True
            await update.message.reply_text(
                "Введите новые настройки:",
                reply_markup=ReplyKeyboardRemove()
            )
        elif current_view == 'knowledge':
            context.user_data['awaiting_update_knowledge'] = True
            await update.message.reply_text(
                "Введите новую базу знаний:",
                reply_markup=ReplyKeyboardRemove()
            )
    elif text == BTN_BACK:
        context.user_data.pop('current_view', None)
        await update.message.reply_text(
            "Главное меню:",
            reply_markup=get_main_menu_reply_keyboard()
        )

# Универсальный обработчик текстовых сообщений:
# если ожидается ввод нового значения – обновляем настройки/базу знаний,
# иначе – считаем сообщение вопросом и обрабатываем через F5AI API.
async def handle_update_input(update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.id == ADMIN_GROUP_ID:
        return

    user_id = update.effective_user.id
    text = update.message.text

    if context.user_data.get("awaiting_update_settings"):
        prefix = "[Обновление настроек]\nНовые настройки:\n"
        max_allowed = 4096 - len(prefix)
        if len(text) > max_allowed:
            await update.message.reply_text(
                f"Текст слишком длинный. Пожалуйста, отправьте текст длиной не более {max_allowed} символов.",
                reply_markup=get_main_menu_reply_keyboard()
            )
            context.user_data.pop("awaiting_update_settings", None)
            return

    if context.user_data.get("awaiting_update_knowledge"):
        prefix = "[Обновление базы знаний]\nНовая база знаний:\n"
        max_allowed = 4096 - len(prefix)
        if len(text) > max_allowed:
            await update.message.reply_text(
                f"Текст слишком длинный. Пожалуйста, отправьте текст длиной не более {max_allowed} символов.",
                reply_markup=get_main_menu_reply_keyboard()
            )
            context.user_data.pop("awaiting_update_knowledge", None)
            return

    # Если это сообщение длинное уведомляем пользователя
    if not (context.user_data.get("awaiting_update_settings") or context.user_data.get("awaiting_update_knowledge")):
        if len(text) > 4096:
            await update.message.reply_text(
                "Текст слишком длинный. Вы можете отправить только текст размером в 1 сообщение (4096 символов).",
                reply_markup=get_main_menu_reply_keyboard()
            )
            return

    if context.user_data.get("awaiting_update_settings"):
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        await save_user(user_id, settings=text, last_reset=now)
        context.user_data['settings'] = text
        await update.message.reply_text(
            "✅ Настройки обновлены!\n\n"
            "Теперь бот будет отвечать согласно новым параметрам. Чем точнее настройки, тем лучше результат! 🚀\n\n"
            "Не забудьте проверить и дополнить знания бота, чтобы ответы были максимально точными. 📚",
            reply_markup=get_main_menu_reply_keyboard()
        )
        user_data_db = await get_user(user_id)
        admin_thread_id = user_data_db.get("admin_thread_id") if user_data_db else None
        if admin_thread_id:
            await context.bot.send_message(
                chat_id=ADMIN_GROUP_ID,
                text=f"[Обновление настроек]\nНовые настройки:\n{text}",
                message_thread_id=admin_thread_id,
                reply_markup=ReplyKeyboardRemove()
            )
        context.user_data.pop("awaiting_update_settings", None)
        context.user_data.pop("current_view", None)
        return
    if context.user_data.get("awaiting_update_knowledge"):
        await save_user(user_id, knowledge=text)
        context.user_data['knowledge'] = text
        await update.message.reply_text(
            "✅ Знания обновлены!\n\n"
            "Теперь бот будет отвечать согласно новым параметрам. Чем точнее настройки, тем лучше результат! 🚀\n\n"
            "Не забудьте проверить и дополнить настройки бота, чтобы ответы были максимально точными. 📚",
            reply_markup=get_main_menu_reply_keyboard()
        )
        user_data_db = await get_user(user_id)
        admin_thread_id = user_data_db.get("admin_thread_id") if user_data_db else None
        if admin_thread_id:
            await context.bot.send_message(
                chat_id=ADMIN_GROUP_ID,
                text=f"[Обновление базы знаний]\nНовая база знаний:\n{text}",
                message_thread_id=admin_thread_id,
                reply_markup=ReplyKeyboardRemove()
            )
        context.user_data.pop("awaiting_update_knowledge", None)
        context.user_data.pop("current_view", None)
        return

    await answer_query(update, context)

async def answer_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.id == ADMIN_GROUP_ID:
        return

    user_id = update.effective_user.id
    user_query = update.message.text

    user_data = await get_user(user_id)

    if not user_data:
        await update.message.reply_text(
            "Сначала настрой бот, выбрав раздел «Настройки» или «Знания».",
            reply_markup=get_main_menu_reply_keyboard()
        )
        return

    if user_data.get("bot_enabled") == 0:
        admin_thread_id = user_data.get("admin_thread_id")
        if admin_thread_id:
            await context.bot.send_message(
                chat_id=ADMIN_GROUP_ID,
                text=f"[Пользователь] {user_query}",
                message_thread_id=admin_thread_id,
                reply_markup=ReplyKeyboardRemove()
            )
        return

    if not user_data.get("settings") or not user_data.get("knowledge"):
        await update.message.reply_text(
            "Сначала настрой бот, выбрав раздел «Настройки» или «Знания».",
            reply_markup=get_main_menu_reply_keyboard()
        )
        return

    settings = user_data["settings"]
    knowledge = user_data["knowledge"]
    last_reset = user_data.get("last_reset")
    history = await get_history(user_id, last_reset)

    system_message = (
        "Ты — чат-бот, который должен отвечать на вопросы, основываясь только на следующих настройках и базе знаний. "
        "Не используй никакую дополнительную информацию или знания, кроме предоставленных.\n\n"
        f"Настройки: {settings}\n\n"
        f"База знаний: {knowledge}"
    )

    messages = [{"role": "system", "content": system_message}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_query})

    payload = {
        "model": "gpt-4o-mini",
        "max_tokens": "16383",
        "messages": messages
    }

    headers = {
        "Content-Type": "application/json",
        "X-Auth-Token": F5AI_API_KEY
    }

    api_url = "https://api.f5ai.ru/v1/chat/completions"

    async with aiohttp.ClientSession() as session:
        async with session.post(api_url, json=payload, headers=headers) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                await update.message.reply_text(
                    f"Ошибка при запросе: {resp.status} {error_text}",
                    reply_markup=get_main_menu_reply_keyboard()
                )
                return

            response_json = await resp.json()
            try:
                answer = response_json["choices"][0]["message"]["content"]
                await update.message.reply_text(answer, reply_markup=get_main_menu_reply_keyboard())
            except Exception as e:
                await update.message.reply_text(
                    f"Ошибка обработки ответа: {e}",
                    reply_markup=get_main_menu_reply_keyboard()
                )
                return

    await save_history_message(user_id, "user", user_query)
    await save_history_message(user_id, "assistant", answer)

    admin_thread_id = user_data.get("admin_thread_id")
    if admin_thread_id:
        await context.bot.send_message(
            chat_id=ADMIN_GROUP_ID,
            text=f"[Пользователь] {user_query}",
            message_thread_id=admin_thread_id,
            reply_markup=ReplyKeyboardRemove()
        )
        await context.bot.send_message(
            chat_id=ADMIN_GROUP_ID,
            text=f"[Бот] {answer}",
            message_thread_id=admin_thread_id,
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await context.bot.send_message(
            chat_id=ADMIN_GROUP_ID,
            text=f"[Пользователь] {user_query}",
            reply_markup=ReplyKeyboardRemove()
        )
        await context.bot.send_message(
            chat_id=ADMIN_GROUP_ID,
            text=f"[Бот] {answer}",
            reply_markup=ReplyKeyboardRemove()
        )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Процесс отменён. Для начала отправьте /start.",
        reply_markup=ReplyKeyboardRemove()
    )
    return -1

async def admin_toggle_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.id != ADMIN_GROUP_ID:
        return
    thread_id = update.message.message_thread_id
    if thread_id is None:
        return

    user_data = await get_user_by_thread(thread_id)
    if not user_data:
        await update.message.reply_text("Пользователь не найден для этого треда.")
        return
    user_id = user_data["user_id"]

    if update.message.text.startswith("/disable"):
        await set_bot_enabled(user_id, False)
        await update.message.reply_text("Бот отключен для данного пользователя.")
    elif update.message.text.startswith("/enable"):
        await set_bot_enabled(user_id, True)
        await update.message.reply_text("Бот включен для данного пользователя.")

async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.id != ADMIN_GROUP_ID:
        return
    thread_id = update.message.message_thread_id
    if thread_id is None:
        return
    if update.message.text.startswith("/"):
        return

    user_data = await get_user_by_thread(thread_id)
    if not user_data:
        await update.message.reply_text("Не найден пользователь для этого треда.")
        return
    user_id = user_data["user_id"]

    message_text = update.message.text

    await context.bot.send_message(
        chat_id=user_id,
        text=f"{message_text}",
        reply_markup=ReplyKeyboardRemove()
    )
    await save_history_message(user_id, "developer", message_text)