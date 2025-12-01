import logging
import os
from telegram import InlineKeyboardMarkup, Update, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler

from dotenv import load_dotenv

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

STATE = 1

QUESTIONS = [
    {
        "id": "q1_gula",
        "text": "Seberapa sering kamu makan gula dalam sehari?",
        "options": [("Sering", "high"), ("Jarang", "low")],
    },
    
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['current_question'] = 0
    context.user_data['answers'] = {}
    
    await send_question(update, context)
    return STATE

async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    index = context.user_data['current_question']
    q_data = QUESTIONS[index]
    
    keyboard = []
    row = []
    
    for label, value in q_data['options']:
        row.append(InlineKeyboardButton(label, callback_data=value))
    keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(q_data['text'], reply_markup=reply_markup)
    else:
        await update.message.reply_text(q_data['text'], reply_markup=reply_markup)

async def answer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    index = context.user_data['current_question']
    current_qdata = QUESTIONS[index]['id']
    selected_option = query.data
    
    context.user_data['answers'][current_qdata] = selected_option
    
    context.user_data['current_question'] += 1
    next_q = context.user_data['current_question']
    
    if next_q < len(QUESTIONS):
        await send_question(update, context)
        return STATE
    else:
        return await finish(update, context)

async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answers = context.user_data['answers']
    
    # score = 0
    # if answers.get("q1_gula") == "":
    #     score += 10 
    
    result_text = "Terima kasih telah menyelesaikan kuis!"
    
    # if score >= 30:
    #     result_text += "\nHasil: Kamu memiliki risiko tinggi terhadap diabetes."
    # else:
    #     result_text += "\nHasil: Kamu memiliki risiko rendah terhadap diabetes."
    
    await update.callback_query.edit_message_text(result_text)
    return ConversationHandler.END

def main():
    load_dotenv()
    TOKEN = os.getenv('TOKEN')
    
    application = ApplicationBuilder().token(TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            STATE: [CallbackQueryHandler(answer_handler)]},
        fallbacks=[]
    )
    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()