import logging
import os
from telegram import InlineKeyboardMarkup, Update, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler

from dotenv import load_dotenv

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

WELCOME, QUIZ = 1, 2

QUESTIONS = [
    {
        "id": "q1_gula",
        "text": "Bagaimana konsumsi gula pada anak anda?",
        "options": [("Banyak", 1), ("Cukup", 0)],
    },
    {
        "id": "q2_dot",
        "text": "Apakah anak anda masih memiliki kebiasaan mengunyah dot sambil tidur?",
        "options": [("Sering", 1), ("Berhenti", 0)],
    },
    {
        "id": "q3_ngemil",
        "text": "Apakah anak anda sering ngemil?",
        "options": [("Sering", 1), ("Jarang", 0)],
    },
    {
        "id": "q4_sikat",
        "text": "Berapa banyak anak anda sikat gigi dalam sehari?",
        "options": [("1 kali", 1), ("2 kali", 0)],
    },
    {
        "id": "q5_flouride",
        "text": "Apakah anak anda sering menggunakan pasta gigi yang mengandung flouride?",
        "options": [("Jarang", 1), ("Sering", 0)],
    },
    {
        "id": "q6_riwayat_keluarga",
        "text": "Apakah dalam keluarga anda memiliki riwayat sakit gigi?",
        "options": [("Ada", 1), ("Tidak ada", 0)],
    },
    {
        "id": "q7_riwayat_anak",
        "text": "Apakah anak anda punya riwayat sakit gigi?",
        "options": [("Ada", 1), ("Tidak ada", 0)],
    },
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menampilkan welcome message dengan tombol Mulai dan Cancel"""
    welcome_text = (
        "🦷 *Selamat datang di Sistem Analisis Kesehatan Gigi Anak!*\n\n"
        "Bot ini akan membantu Anda menganalisis kondisi kesehatan gigi anak "
        "melalui beberapa pertanyaan sederhana.\n\n"
        "Klik *Mulai* untuk memulai analisis atau *Cancel* untuk mengakhiri chat."
    )
    
    keyboard = [
        [
            InlineKeyboardButton("Mulai", callback_data="start_quiz"),
            InlineKeyboardButton("Cancel", callback_data="cancel")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text, 
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return WELCOME

async def welcome_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk tombol di welcome message"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "start_quiz":
        # Inisialisasi data quiz
        context.user_data['current_question'] = 0
        context.user_data['answers'] = {}
        
        await send_question(update, context)
        return QUIZ
    elif query.data == "cancel":
        await query.edit_message_text(
            "❌ Chat dibatalkan. Terima kasih!\n\n"
            "Ketik /start untuk memulai lagi."
        )
        return ConversationHandler.END

async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    index = context.user_data['current_question']
    q_data = QUESTIONS[index]
    
    keyboard = []
    row = []
    
    for label, value in q_data['options']:
        row.append(InlineKeyboardButton(label, callback_data=str(value)))
    keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Tambahkan nomor pertanyaan
    question_text = f"*Pertanyaan {index + 1}/{len(QUESTIONS)}*\n\n{q_data['text']}"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(question_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(question_text, reply_markup=reply_markup, parse_mode='Markdown')

async def answer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    index = context.user_data['current_question']
    current_qdata = QUESTIONS[index]['id']
    selected_option = int(query.data)  
    
    context.user_data['answers'][current_qdata] = selected_option
    
    context.user_data['current_question'] += 1
    next_q = context.user_data['current_question']
    
    if next_q < len(QUESTIONS):
        await send_question(update, context)
        return QUIZ
    else:
        return await finish(update, context)

async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answers = context.user_data['answers']
    
    # Hitung total skor
    total_score = sum(answers.values())
    
    # Tentukan hasil berdasarkan skor
    if 1 <= total_score <= 3:
        status = "TINGGI"
        emoji = "😄"
        result_text = f"{emoji} *Hasil Analisis: Kesehatan Gigi {status}*\n\n"
        result_text += "✅ **Anak Anda terindikasi tinggi giginya sehat!**\n\n"
        result_text += "Pertahankan kebiasaan baik ini dan lakukan kontrol rutin ke dokter gigi."
        
    elif total_score == 4:
        status = "SEDANG"
        emoji = "😐"
        result_text = f"{emoji} *Hasil Analisis: Kesehatan Gigi {status}*\n\n"
        result_text += "⚠️ **Anak Anda terindikasi sedang giginya sehat.**\n\n"
        result_text += "Lebih baik lakukan pencegahan berkala dan perbaiki kebiasaan yang kurang baik."
        
    elif 5 <= total_score <= 7:
        status = "RENDAH"
        emoji = "😟"
        result_text = f"{emoji} *Hasil Analisis: Kesehatan Gigi {status}*\n\n"
        result_text += "🚨 **Anak Anda terindikasi rendah giginya sehat.**\n\n"
        result_text += "Segera periksakan ke dokter gigi dan perbaiki kebiasaan sehari-hari!"
    
    # Ini untuk perhitungan skornya yagesya
    result_text += f"\n\n📊 **Skor Total: {total_score}/7**"
    result_text += f"\n\n💡 *Ketik /start untuk analisis baru*"
    
    await update.callback_query.edit_message_text(result_text, parse_mode='Markdown')
    return ConversationHandler.END

def main():
    load_dotenv()
    TOKEN = os.getenv('TOKEN')
    
    application = ApplicationBuilder().token(TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            WELCOME: [CallbackQueryHandler(welcome_handler)],
            QUIZ: [CallbackQueryHandler(answer_handler)]
        },
        fallbacks=[]
    )
    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()