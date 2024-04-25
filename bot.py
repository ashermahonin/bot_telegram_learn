
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters, ConversationHandler
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = ''
CHANNEL_ID = '@go_python_learn'

(CODE, DIFFICULTY, ANSWERS, POSTING) = range(4)

code_snippet = None
difficulty_level = None
answer_options = []
correct_answer_index = None
hint = None

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Привет :) Выбери действие:",
                              reply_markup=InlineKeyboardMarkup([
                                  [InlineKeyboardButton("Send Code", callback_data='send_code')],
                                  [InlineKeyboardButton("Cancel", callback_data='cancel')]
                              ]))
    return CODE

def receive_code(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    query.edit_message_text("Пожалуйста, отправь код который нужно опубликовать.")
    return CODE

def actual_code(update: Update, context: CallbackContext):
    global code_snippet
    code_snippet = update.message.text
    update.message.reply_text("Выбери уровень сложности:",
                              reply_markup=InlineKeyboardMarkup([
                                  [InlineKeyboardButton("Noob", callback_data='noob')],
                                  [InlineKeyboardButton("Junior", callback_data='junior')],
                                  [InlineKeyboardButton("Middle", callback_data='middle')],
                                  [InlineKeyboardButton("Senior", callback_data='senior')],
                              ]))
    return DIFFICULTY

def set_difficulty(update: Update, context: CallbackContext):
    global difficulty_level
    query = update.callback_query
    query.answer()
    difficulty_level = query.data
    query.edit_message_text(text=f" Сложность: {difficulty_level}. Теперь отправьте варианты ответов через новую строку. 
                                    В конце добавьте строку 'Correct: $номер_строки_верного_ответа, 
                                    а для подсказки укажите:'Hint: $ваш_текст_подсказки.")
    return ANSWERS

def receive_answers(update: Update, context: CallbackContext):
    global answer_options, correct_answer_index, hint

    answers_text = update.message.text
    options = answers_text.split('\n')

    correct_line = None
    hint_line = None
    filtered_options = []

    for line in options:
        if line.lower().startswith('correct:'):
            correct_line = line
        elif line.lower().startswith('hint:'):
            hint_line = line
        else:
            filtered_options.append(line.strip())

    if correct_line is None or hint_line is None:
        update.message.reply_text("[ОШИБКА]: Пожалуйста, убедись что в 'Correct:' строка и в 'Hint:' строка.")
        return ANSWERS

    try:
        correct_answer_index = int(correct_line.split(':', 1)[1].strip()) - 1
        hint = hint_line.split(':', 1)[1].strip()
        answer_options = filtered_options

        if correct_answer_index < 0 or correct_answer_index >= len(answer_options):
            update.message.reply_text("[ОШИБКА]: Неправильное количество верных ответов.")
            return ANSWERS

    except ValueError:
        update.message.reply_text("[ОШИБКА]: Корректный ответ должен быть цифрой.")
        return ANSWERS

    update.message.reply_text("Нажми Post  для публикации или Cancel  для отмены.",
                              reply_markup=InlineKeyboardMarkup([
                                  [InlineKeyboardButton("Post", callback_data='post')],
                                  [InlineKeyboardButton("Cancel", callback_data='cancel')]
                              ]))
    return POSTING


def post(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    bot = context.bot
    message_with_code = f"```{code_snippet}```\n\n#{difficulty_level}\n\n[Python & GO | Тесты](https://t.me/go_python_learn)"
    bot.send_message(chat_id=CHANNEL_ID, text=message_with_code, parse_mode=ParseMode.MARKDOWN)
    poll_message = bot.send_poll(
        chat_id=CHANNEL_ID, 
        question="Результат выполнения кода:", 
        options=answer_options, 
        is_anonymous=True, 
        type='quiz', 
        correct_option_id=correct_answer_index, 
        explanation=hint, 
        explanation_parse_mode=ParseMode.MARKDOWN
    )
    query.edit_message_text("Викторина успешо создана!")
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    query.edit_message_text('Публикация отменена. Нажми /start для перезагрузки.')
    return ConversationHandler.END

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CODE: [CallbackQueryHandler(receive_code, pattern='^send_code$'), 
                   MessageHandler(Filters.text & ~Filters.command, actual_code)],
            DIFFICULTY: [CallbackQueryHandler(set_difficulty)],
            ANSWERS: [MessageHandler(Filters.text & ~Filters.command, receive_answers)],
            POSTING: [CallbackQueryHandler(post, pattern='^post$'), 
                      CallbackQueryHandler(cancel, pattern='^cancel$')]
        },
        fallbacks=[CallbackQueryHandler(cancel, pattern='^cancel$')]
    )

    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
