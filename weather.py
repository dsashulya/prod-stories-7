import requests
import json
from pymorphy2 import MorphAnalyzer
from datetime import datetime
import pickle

WEATHER_TOKEN = '42dcd4bf97be2967b026517b86c3b7a1'
WEEKDAYS = ['понедельник', 'вторник', 'сред', 'четверг', 'пятниц', 'суббот', 'воскресенье']


def parse_weather_request(message):
    weather = Weather(WEATHER_TOKEN)
    city = None
    now = True
    week = False
    day = None
    if 'недел' in message.text.lower():
        now = False
        week = True

    # checking weekdays
    for day_ind, weekday in enumerate(WEEKDAYS):
        if weekday in message.text.lower():
            day = day_ind
            break

    if " в " in message.text.lower() or " во " in message.text.lower():
        mes = message.text.lower().split()
        try:
            ind = mes.index("в")
        except:
            ind = mes.index("во")
        if len(mes) >= ind + 2:
            city = mes[ind + 1].lower().capitalize()
    return weather, city, now, week, day


class Weather:
    def __init__(self, token):
        self.token = token
        self.root_request = 'https://api.openweathermap.org/data/2.5/onecall?units=metric'
        self.root_coord_request = 'https://api.openweathermap.org/data/2.5/weather?'
        with open('city_nicknames.pkl', 'rb') as file:
            self.city_nicknames = pickle.load(file)
        self.morph = MorphAnalyzer()
        self.day_map = {
            'Monday': "Понедельник",
            'Tuesday': "Вторник",
            'Wednesday': "Среда",
            'Thursday': "Четверг",
            'Friday': "Пятница",
            'Saturday': "Суббота",
            'Sunday': "Воскресенье"
        }
        self.day_map_reversed = {value: key for key, value in self.day_map.items()}
        self.day_index = {i: value for i, value in enumerate(self.day_map.values())}
        self.day_index_reversed = {value.lower(): key for key, value in self.day_index.items()}

    def parse_response(self, response, city_name, now, week, day):
        response = json.loads(response.text)
        city_name = self._inflect(city_name, 'loct')
        output = f'ПОГОДА В {city_name.upper()}'
        if day is not None:
            weekday = self._inflect(self.day_index[day], 'accs')
            today = self.day_index_reversed[self.day_map[datetime.today().strftime("%A")].lower()]
            target_idx = (day - today) % 7 + 1 # days between today and target day
            info = response['daily'][target_idx]
            output += f'\nво {weekday}' if weekday == "Вторник" else f'\nв {weekday}'
            output += self._day_output(info)
            now, week = False, False
        if now:
            cur = response['current']
            temp = round(cur['temp'], 1)
            feels = round(cur['feels_like'], 1)
            weather = cur['weather'][0]['description']
            output += f'\nсейчас {weather}' \
                      f'\n🌡️температура {temp} по Цельсию' \
                      f'\n🌡️ощущается как {feels}'
        if week:
            daily = response['daily']
            output += f'\n🗓️на неделю🗓️'
            for d in daily:
                dt = d['dt']
                output += '\nСегодня' if datetime.utcfromtimestamp(dt).date() == datetime.today().date() else \
                    f'\n{self.day_map[datetime.utcfromtimestamp(dt).strftime("%A")]}:'  # getting d name
                output += self._day_output(d)
        return output

    @staticmethod
    def _day_output(info):
        day_temp = round(info['temp']['day'], 1)
        night_temp = round(info['temp']['night'], 1)
        weather = info['weather'][0]['description']
        return f' будет {weather}' \
               f'\n🌡️температура днем {day_temp}' \
               f'\n🌡️температура ночью {night_temp} градусов по Цельсию\n'

    def _inflect(self, word, case):
        word = self.morph.parse(word)[0]
        word = word.inflect({case}).word.capitalize()
        return word

    def get_coords(self, city):
        response = requests.get(self.root_coord_request + f'q={city}&appid={self.token}', verify=False)
        response = json.loads(response.text)
        return response['coord']['lon'], response['coord']['lat']

    def get_weather(self, city, now=True, week=True, day: int = None):
        if city.lower() in self.city_nicknames:
            city = self.city_nicknames[city.lower()]
        try:
            lon, lat = self.get_coords(city)
        except KeyError:
            return "Я не знаю такой населенный пункт :с"
        response = requests.get(self.root_request + f'&lat={lat}&lon={lon}&exclude=minutely,hourly,alerts' +
                                f'&lang=ru&appid={self.token}', verify=False)
        return self.parse_response(response, city, now, week, day)
