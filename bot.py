import telebot
import pandas as pd
import ast

print("✅ Бот запускается...")

bot = telebot.TeleBot("7614342196:AAGsADl2r1ioP-WjMcwJLIiMQo46AOoQgvs")

print("✅ Бот активен. Ожидаю команду /start...")

# Загружаем вопросы и баллы
questions_df = pd.read_excel("crypto_test_questions.xlsx")
types_df = pd.read_excel("crypto_trading_personality_types.xlsx")

questions = []
scores = []

for i, row in questions_df.iterrows():
    question_text = str(row["Вопрос"]).replace('"', "'")
    options = [row.get(col, "") for col in ["A", "B", "C", "D", "E"] if pd.notna(row.get(col))]
    score_list = [row.get(col + "_score") for col in ["A", "B", "C", "D", "E"] if pd.notna(row.get(col + "_score"))]
    scores.append(score_list)
    questions.append({"text": question_text, "options": options})

profiles = []
for _, row in types_df.iterrows():
    profiles.append({
        "type": row["Тип"],
        "desc": row["Краткое описание"],
        "style": row["Подходящие стили трейдинга"]
    })

user_data = {}

@bot.message_handler(commands=['start'])
def start_handler(message):
    print(f"📥 Получена команда /start от chat_id: {message.chat.id}")
    if message.chat.id in user_data:
        bot.send_message(message.chat.id, "Ты уже проходишь тест. Напиши /stop чтобы сбросить и начать заново.")
        return
    user_data[message.chat.id] = {"index": 0, "results": []}
    send_question(message.chat.id)

def send_question(chat_id):
    data = user_data[chat_id]
    q = questions[data["index"]]
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for opt in q["options"]:
        markup.add(opt)
    bot.send_message(chat_id, f"Вопрос {data['index'] + 1}/{len(questions)}:\n" + q["text"], reply_markup=markup)

@bot.message_handler(commands=['stop'])
def stop_handler(message):
    user_data.pop(message.chat.id, None)
    bot.send_message(message.chat.id, "Прогресс сброшен. Напиши /start чтобы начать заново.")

@bot.message_handler(func=lambda m: m.chat.id in user_data)
def handle_answer(message):
    data = user_data[message.chat.id]
    q_index = data["index"]
    q = questions[q_index]
    if message.text not in q["options"]:
        bot.send_message(message.chat.id, "Пожалуйста, выбери вариант из предложенных.")
        return
    selected_index = q["options"].index(message.text)
    raw = scores[q_index][selected_index]
    score = ast.literal_eval(raw) if isinstance(raw, str) else raw
    data["results"].append(score)
    data["index"] += 1
    if data["index"] < len(questions):
        send_question(message.chat.id)
    else:
        summarize(message.chat.id)

def summarize(chat_id):
    result_vector = [0]*5
    for s in user_data[chat_id]["results"]:
        for i in range(5):
            result_vector[i] += s[i]
    max_index = result_vector.index(max(result_vector))
    profile = profiles[max_index]
    bot.send_message(chat_id, f"🧠 Ваш психотип: {profile['type']}\n\n📄 {profile['desc']}\n\n💼 Подходящие стили трейдинга:\n{profile['style']}")
    del user_data[chat_id]


@bot.message_handler(commands=['debug'])
def debug_handler(message):
    if message.chat.id not in user_data:
        bot.send_message(message.chat.id, "Сначала начните тест с /start.")
        return
    result_vector = [0]*5
    for s in user_data[message.chat.id]["results"]:
        for i in range(5):
            result_vector[i] += s[i]
    bot.send_message(message.chat.id, f"🔍 Текущий балльный вектор: {result_vector}")
bot.polling()
