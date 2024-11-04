#!/usr/bin/python3

import os
import json
import urllib.request
from datetime import datetime, timezone
import socket
import sys
from time import sleep
import ssl
import gzip
import logging

# 配置日志记录
logging.basicConfig(filename='aprs.log', level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

ssl._create_default_https_context = ssl._create_unverified_context

Callsign = 'callsigbin/python3

import os
import json
import urllib.request
from datetime import datetime, timezone
import socket
import sys
from time import sleep
import ssl
import gzip
import logging

# 配置日志记录
logging.basicConfig(filename='aprs.log', level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

ssl._create_default_https_context = ssl._create_unverified_context

Callsign = 'CallSign'    #CallSign+SSID
Passcode = 'xxxxx'       #aprs passcode
Server = 'asia.aprs2.net:14580'  # 调整服务器地址
Protocol = 'any'
City = '101110110'      # 替换为和风天气的城市代码
Key = 'xxxxxxxxxxx'     # 替换为和风天气的api key
Lat = '34.0000'         # 替换为城市的纬度
Lng = '108.0000'        # 替换为城市的经度

def send_aprsframe(aprs_frame):
    sended = False
    Aprs_Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while not sended:
        try:
            Aprs_Sock.connect((Server.split(':')[0], int(Server.split(':')[1])))
            login_message = f'user {Callsign} pass {Passcode}\n'
            logging.info(f"Sending login message: {login_message.strip()}")
            Aprs_Sock.send(login_message.encode())
            sReturn = Aprs_Sock.recv(4096).decode()
            if sReturn.startswith("#"):
                logging.info(f"Succesfully logged to APRS-IS! {sReturn.strip()}")
                logging.info(f"Sending APRS frame: {aprs_frame.decode()}")
                Aprs_Sock.send(f'{aprs_frame.decode()}\n'.encode())
                sended = True
            else:
                logging.error(f"Failed to log in to APRS-IS: {sReturn.strip()}")
        except Exception as e:
            logging.error(f"Connection error: {e}")
        finally:
            sleep(1)
    Aprs_Sock.shutdown(0)
    Aprs_Sock.close()

class APRSFrame:
    def __init__(self):
        self.source = None
        self.dest = None
        self.path = []
        self.payload = ''

    def export(self, encode=True):
        tnc2 = f"{self.source}>{self.dest},{','.join(self.path)}:{self.payload}"
        if len(tnc2) > 510:
            tnc2 = tnc2[:510]
        if encode:
            tnc2 = tnc2.encode('ISO-8859-1')
        return tnc2

def bc():
    bcargs_weather = {
        'callsign': Callsign,
        'weather': f'https://devapi.qweather.com/v7/weather/now?location={City}&key={Key}',
    }
    while True:
        frame = get_weather_frame(**bcargs_weather)
        if frame:
            send_aprsframe(frame)
        sleep(300)  # 此处为查询和发送间隔，默认为300秒，即5分钟

def process_ambiguity(pos, ambiguity):
    num = bytearray(pos, 'utf-8')
    for i in range(0, ambiguity):
        if i > 1:
            i += 1
        i += 2
        num[-i] = ord(' ')
    return num.decode()

def encode_lat(lat):
    lat_dir = 'N' if lat >= 0 else 'S'
    lat_abs = abs(lat)
    lat_deg = int(lat_abs)
    lat_min = (lat_abs % 1) * 60
    return f"{lat_deg:02}{lat_min:05.2f}{lat_dir}"

def encode_lng(lng):
    lng_dir = 'E' if lng >= 0 else 'W'
    lng_abs = abs(lng)
    lng_deg = int(lng_abs)
    lng_min = (lng_abs % 1) * 60
    return f"{lng_deg:03}{lng_min:05.2f}{lng_dir}"

def mkframe(callsign, payload):
    frame = APRSFrame()
    frame.source = callsign
    frame.dest = 'APRS'
    frame.path = ['TCPIP*', 'qAC']  # 移除了 T2PANAMA
    frame.payload = payload
    return frame.export()

def get_weather_frame(callsign, weather):
    try:
        req = urllib.request.Request(weather)
        with urllib.request.urlopen(req) as response:
            content_encoding = response.headers.get('Content-Encoding')
            if content_encoding == 'gzip':
                wea_str = gzip.decompress(response.read()).decode('utf-8')
            else:
                wea_str = response.read().decode('utf-8')
            
            logging.info(f"Received weather data from API: {wea_str}")
            
            w = json.loads(wea_str)['now']
            utc_now = datetime.now(timezone.utc)
            timestamp = utc_now.strftime('%H%M%S')  # UTC时间
            datestamp = utc_now.strftime('%y%m%d')
            enc_lat = process_ambiguity(encode_lat(float(Lat)), 0)
            enc_lng = process_ambiguity(encode_lng(float(Lng)), 0)
            wenc = f"@{datestamp}z{enc_lat}/{enc_lng}_"
            wind = w.get('wind360', 0)
            wind_speed = float(w.get('windSpeed', 0))  # 风速单位已经是米/秒
            wenc += f"{int(wind):03d}/{int(wind_speed):03d}g000"
            temp_c = int(w.get('temp', 0))  # 温度单位已经是摄氏度
            wenc += f"t{temp_c:03d}"
            precip_mm = float(w.get('precip', 0))
            wenc += f"r{int(precip_mm):03d}"
            wenc += f"p000"  # 24小时雨量，假设为0
            wenc += f"P000"  # 自午夜以来雨量，假设为0
            wenc += f"h{int(w.get('humidity', 0)):02d}"
            pressure_pa = float(w.get('pressure', 0))
            wenc += f"b{int(pressure_pa * 10):05d}"
            wenc += " Weather data from QWeather API"
            payload = wenc
            raw_frame = mkframe(callsign, payload)
            logging.info(f"Generated APRS frame: {raw_frame.decode()}")
            return raw_frame
    except Exception as e:
        logging.error(f"Weather decode error: {e}")
        return None

if __name__ == "__main__":
    bc()
