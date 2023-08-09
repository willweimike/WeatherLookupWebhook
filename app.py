import os
import re
import json
import requests
from flask import Flask, request, Response
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage


app = Flask(__name__)

line_bot_api = LineBotApi('')
handler = WebhookHandler('')

weather_auth_token = ''
weather_base_url = f'https://opendata.cwb.gov.tw/fileapi/v1/opendataapi/F-C0032-001?Authorization={weather_auth_token}&downloadType=WEB&format=JSON'
areaApi_8hr = {"宜蘭縣":"F-D0047-001","桃園市":"F-D0047-005","新竹縣":"F-D0047-009","苗栗縣":"F-D0047-013",
            "彰化縣":"F-D0047-017","南投縣":"F-D0047-021","雲林縣":"F-D0047-025","嘉義縣":"F-D0047-029",
            "屏東縣":"F-D0047-033","臺東縣":"F-D0047-037","花蓮縣":"F-D0047-041","澎湖縣":"F-D0047-045",
            "基隆市":"F-D0047-049","新竹市":"F-D0047-053","嘉義市":"F-D0047-057","臺北市":"F-D0047-061",
            "高雄市":"F-D0047-065","新北市":"F-D0047-069","臺中市":"F-D0047-073","臺南市":"F-D0047-077",
            "連江縣":"F-D0047-081","金門縣":"F-D0047-085"}


# (今日)八小時預報函式
def today_forecast(address):
    area_lst = {}
    msg = '找不到天氣預報資訊。'  
    try:
        weather_data = requests.get(weather_base_url)
        weather_data_json = weather_data.json()
        """
        print(weather_data_json)
        with open('weather_data.json', 'w') as wfh:
            json.dump(weather_data_json, wfh, indent=2)
        """
        location = weather_data_json['cwbopendata']['dataset']['location']
        for i in location:
            city = i['locationName']
            wx = i['weatherElement'][0]['time'][0]['parameter']['parameterName']
            min_t = i['weatherElement'][1]['time'][0]['parameter']['parameterName']
            max_t = i['weatherElement'][2]['time'][0]['parameter']['parameterName']
            rain = i['weatherElement'][2]['time'][0]['parameter']['parameterName']
            area_lst[city] = f'天氣{wx}，\n預估最高溫{max_t}度，最低溫{min_t}度，\n降雨機率{rain}%'
        
        for i in area_lst: 
            if i in address:
                msg = area_lst[i]
                url = f'https://opendata.cwb.gov.tw/api/v1/rest/datastore/{areaApi_8hr[i]}?Authorization={weather_auth_token}&elementName=WeatherDescription'
                f_data = requests.get(url)
                f_data_json = f_data.json()
                location = f_data_json['records']['locations'][0]['location']
                break
        
        for i in location:
            city = i['locationName']
            wd = i['weatherElement'][0]['time'][1]['elementValue'][0]['value']
            if city in address:
                msg = f'天氣{wd}'
                break
        return msg
    except:
        return msg


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return Response(status=400)
    except LineBotApiError:
        return Response(status=500)
    return Response(status=200)


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    received = str(event.message.text)
    if "台" in received:
        received = received.replace("台", "臺")
    message = received.strip().split()

    if re.search('天氣', received):
        msg = today_forecast(message[0])
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
        return
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=
        "搜尋的格式如下：\n【縣市(鄉鎮市區)】空格【天氣】\n（鄉鎮市區為選填選項）\n範例：\n台北市大安區  天氣   或  台北市  天氣\nps.鄉鎮選項能給您更明確的天氣資訊唷"))
        return



if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)