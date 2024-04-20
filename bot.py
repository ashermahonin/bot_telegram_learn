from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters, ConversationHandler
import logging

#logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

#token + channel_id to post polls
TOKEN = '$bot_token'
CHANNEL_ID = '@$cnahhel_id' 

#state of discuss
(CODE, DIFFICULTY, ANSWERS, POSTING) = range(4)

#variables for 
code_snippet = None
difficulty_level = None
answer_options = []
correct_answer_index = None

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Отправьте код, который нужно опубликовать.")
    return CODE

def receive_code(update: Update, context: CallbackContext):
    global code_snippet
    code_snippet = update.message.text
    update.message.reply_text("Выберите уровень сложности: noob, junior, middle, senior.",
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
    query.edit_message_text(text=f" Уровень сложности установлен: {difficulty_level}\nТеперь отправьте варианты ответов через новую строку. 
                                    В конце добавьте строку 'Correct: $номер_строки_верного_ответа, а для подсказки укажите:
                                    'Hint: $ваш_текст_подсказки")
    return ANSWERS

def receive_answers(update: Update, context: CallbackContext):
    global answer_options, correct_answer_index, hint

    answers_text = update.message.text
    *options, correct, hint_line = answers_text.split('\n')
    answer_options = [option.strip() for option in options]
    correct_answer_index = int(correct.split(': ')[1]) - 1 
    hint = hint_line.split(': ', 1)[1]
    update.message.reply_text("Отправьте /post для публикации задания.")
    return POSTING

def post(update: Update, context: CallbackContext):
    bot = context.bot

    message_with_code = f"```{code_snippet}```\n\n#{difficulty_level}\n\n[Python & GO | Тесты]($channel_url)"
    bot.send_message(chat_id=CHANNEL_ID, text=message_with_code, parse_mode=ParseMode.MARKDOWN)
    poll_message = bot.send_poll(
        chat_id=CHANNEL_ID, 
        question="Выберите правильный ответ:", 
        options=answer_options, 
        is_anonymous=True, 
        type='quiz', 
        correct_option_id=correct_answer_index, 
        explanation=hint, 
        explanation_parse_mode=ParseMode.MARKDOWN
    )
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext):
    update.message.reply_text('Отмена. Для начала отправьте /start.')
    return ConversationHandler.END

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CODE: [MessageHandler(Filters.text & ~Filters.command, receive_code)],
            DIFFICULTY: [CallbackQueryHandler(set_difficulty)],
            ANSWERS: [MessageHandler(Filters.text & ~Filters.command, receive_answers)],
            POSTING: [CommandHandler('post', post)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
