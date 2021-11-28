import re

import requests
import telebot

from weather import *

TOKEN = ''
HUGGINGFACE = ''


API_URL = "https://api-inference.huggingface.co/models/Grossmend/rudialogpt3_medium_based_on_gpt2"
headers = {"Authorization": f"Bearer {HUGGINGFACE}"}

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id,
                     f'Привет! Приятно познакомиться, {message.from_user.first_name}. Я бот, и я могу:\n\n'
                     f"- общаться на разные свободные темы\n"
                     f"- подсказать прогноз погоды в интересующем тебя месте.\n"
                     f"Чтобы попрощаться со мной, используй команду <i>/exit</i>\n",
                     parse_mode='HTML')


@bot.message_handler(commands=['help'])
def send_welcome(message):
    bot.send_message(message.chat.id,
                     f'{message.from_user.first_name}, тут ты можешь больше узнать обо мне, о моих способностях и ограничениях.\n\n'
                     f'Я бот в телеграме, поддерживающий запросы <i>только</i> на русском языке!\n'

                     f'Чтобы узнать погоду, используй указание города ("<i>в</i> Москве") и дня ("сегодня"/"<i>на</i> понедельник") (Обрати внимание на то, что предлоги важны<b>!</b>).  '
                     f'Учти, что прогноз можно получить максимум на одну неделю вперед. '
                     f'Без уточнения дня недели (или указания "на неделю") я дам прогноз на текущий день.\n\n',
                     parse_mode='HTML')


@bot.message_handler(commands=['exit'])
def end_message(message):
    bot.send_message(message.chat.id, f"Всего хорошего и до новых встреч!")


def weather_city(message, weather, now, week, day):
    mes = message.text.lower()
    if mes.startswith("в"):
        mes = ' '.join(mes.split()[1:])
    city = weather._inflect(mes.capitalize(), 'nomn')
    output = weather.get_weather(city, now, week, day)
    bot.send_message(message.from_user.id, output)
    bot.send_message(message.from_user.id, "Чем я могу еще быть полезен?")


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    weath = re.compile("погод(а|у|е|ой|ы)")
    if re.search(weath, message.text.lower()):
        weather, city, now, week, day = parse_weather_request(message)
        if city is None:
            msg = bot.send_message(message.from_user.id, "В каком населенном пункте?")
            bot.register_next_step_handler(msg, weather_city, weather=weather, now=now, week=week, day=day)
        else:
            output = weather.get_weather(weather._inflect(city, 'nomn'), now=now, week=week, day=day)
            bot.send_message(message.from_user.id, output)
            bot.send_message(message.from_user.id, "Чем я могу еще быть полезен?")
    elif (("пока" in message.text.lower()) or ("свидан" in message.text.lower())):
       bot.send_message(message.from_user.id, 'Всего хорошего и до новых встреч!')
    
    else:
        def query(payload):
            response = requests.post(API_URL, headers=headers, json=payload)
            return response.json()

        output = query({
            "inputs": {
                "text": message.text,
            },
        })
        try:
            output = output['generated_text']
        except KeyError:
            output = "Я тебя не понял."
        bot.send_message(message.from_user.id, output)


bot.polling(none_stop=True)
