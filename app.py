# app.py
# SPIDER GENERATOR - COMPLETE WEB APPLICATION
# Backend: app.py engine + Flask server + WebSocket streaming + Download

import os
import sys
import json
import time
import random
import string
import hashlib
import threading
import subprocess
import base64
import codecs
import re
import hmac
import signal
import socket
from datetime import datetime
from urllib.parse import unquote
from colorama import Fore, Style, init
init(autoreset=True)

from flask import Flask, render_template, request, jsonify, Response, stream_with_context, send_file
from flask_cors import CORS
import queue
import logging

# Disable Flask default logging for cleaner output
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

try:
    from cfonts import render
    CFONTS = True
except:
    CFONTS = False

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'spider_generator_secret_key_2024'

# Global state for live streaming
generation_queue = queue.Queue()
is_generating = False
generation_thread = None
current_generation_id = None

# ============================================================
# ENGINE CONFIGURATION - FROM app.py
# ============================================================

ReGiOn = "IND"
NiCkNaMe = "SPIDER"
PaSsWoRd = "SPIDY"
ToTaL = 100
ThReAdS = 50
GhOsT = False
AuToAcT = True

aEsKeY = bytes([89,103,38,116,99,37,68,69,117,104,54,37,90,99,94,56])
aEsIv = bytes([54,111,121,90,68,114,50,50,69,51,121,99,104,106,77,37])
cLiEnTsEcReT = "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"

rEgIoNlAnG = {
    "ME": "ar", "IND": "hi", "ID": "id", "VN": "vi", "TH": "th",
    "BD": "bn", "PK": "ur", "TW": "zh", "EUROPE": "fr", "RU": "ru",
    "NA": "na", "SAC": "es", "BR": "pt", "SG": "ms", "US": "us"
}
rEgIoNlIsT = ["IND", "ID", "TH", "ME", "EUROPE", "VN", "BD", "PK", "TW", "RU", "NA", "SAC", "BR", "SG", "US"]

nIcKXoR = b'1e5898ccb8dfdd921f9bdea848768b64a201'

cOnSeCuTiVe = 0
pRiNtLoCk = threading.Lock()
iPlOcK = threading.Lock()

INDIAN_CARRIERS = [
    "Jio", "Airtel", "Vodafone Idea", "BSNL", "MTNL", 
    "Reliance Jio", "Bharti Airtel", "Vi", "Idea Cellular"
]

INDIAN_CITIES = [
    "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", 
    "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Lucknow", 
    "Kanpur", "Nagpur", "Indore", "Bhopal", "Visakhapatnam",
    "Patna", "Vadodara", "Surat", "Rajkot", "Chandigarh"
]

INDIAN_DEVICES = [
    "Asus ASUS_AI2401_A", "Samsung SM-G998B", "OnePlus 9 Pro", 
    "Xiaomi Mi 11", "Google Pixel 6", "Realme GT", "Vivo X70 Pro",
    "Oppo Find X3", "Motorola Edge 20", "Samsung SM-M515F",
    "Samsung SM-A525F", "Redmi Note 10", "OnePlus Nord 2"
]

tor_process = None
IP_ROTATION_INTERVAL = 15
ACCOUNT_COUNTER_FOR_IP_ROTATION = 0

# ============================================================
# TOR FUNCTIONS - FROM app.py
# ============================================================

def start_tor():
    global tor_process
    try:
        subprocess.run(['pkill', '-9', 'tor'], capture_output=True, check=False)
        time.sleep(0.5)
        tor_process = subprocess.Popen(
            ['tor'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        for i in range(10):
            time.sleep(0.5)
            result = subprocess.run(['pgrep', '-x', 'tor'], capture_output=True)
            if result.returncode == 0:
                return True
        return False
    except:
        return False

def renew_tor_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect(('127.0.0.1', 9051))
        s.send(b'AUTHENTICATE ""\r\n')
        s.send(b'SIGNAL NEWNYM\r\n')
        s.send(b'QUIT\r\n')
        s.close()
        time.sleep(1)
        return True
    except:
        return False

def get_proxies():
    return {
        'http': 'socks5h://127.0.0.1:9050',
        'https': 'socks5h://127.0.0.1:9050'
    }

session_pool = []
SESSION_POOL_SIZE = 50

def init_session_pool():
    global session_pool
    session_pool = []
    for _ in range(SESSION_POOL_SIZE):
        session = requests.Session()
        session.proxies.update(get_proxies())
        session.verify = False
        session.timeout = 10
        session_pool.append(session)

def get_pool_session():
    return random.choice(session_pool)

# ============================================================
# PROTOBUF ENCODING - FROM app.py
# ============================================================

def FF(value):
    out = []
    while True:
        b = value & 0x7F
        value >>= 7
        if value:
            out.append(b | 0x80)
        else:
            out.append(b)
            break
    return bytes(out)

def GayRena(field_num, value):
    if isinstance(value, int):
        tag = (field_num << 3) | 0
        return FF(tag) + FF(value)
    elif isinstance(value, str):
        data = value.encode('utf-8')
        tag = (field_num << 3) | 2
        return FF(tag) + FF(len(data)) + data
    elif isinstance(value, bytes):
        tag = (field_num << 3) | 2
        return FF(tag) + FF(len(value)) + value
    elif isinstance(value, dict):
        sub_payload = xPro(value)
        tag = (field_num << 3) | 2
        return FF(tag) + FF(len(sub_payload)) + sub_payload
    else:
        raise TypeError(f"Unsupported type for field {field_num}: {type(value)}")

def xPro(fields_dict):
    payload = b''
    for key, value in fields_dict.items():
        field_num = int(key)
        if isinstance(value, list):
            if value and all(isinstance(v, int) for v in value):
                packed = b''.join(FF(v) for v in value)
                tag = (field_num << 3) | 2
                payload += FF(tag) + FF(len(packed)) + packed
            else:
                for elem in value:
                    payload += GayRena(field_num, elem)
        else:
            payload += GayRena(field_num, value)
    return payload

def Noob(packet):
    cipher = AES.new(aEsKeY, AES.MODE_CBC, aEsIv)
    pad_len = 16 - (len(packet) % 16)
    if pad_len == 0:
        pad_len = 16
    plaintext_padded = packet + bytes([pad_len]) * pad_len
    return cipher.encrypt(plaintext_padded)

def Pro(data):
    from google.protobuf.internal.decoder import _DecodeVarint, _DecodeVarint32
    pos = 0
    length = len(data)
    fields = {}
    while pos < length:
        key, pos = _DecodeVarint(data, pos)
        field_num = key >> 3
        wire_type = key & 7
        if wire_type == 0:
            value, pos = _DecodeVarint(data, pos)
        elif wire_type == 2:
            size, pos = _DecodeVarint32(data, pos)
            raw = data[pos:pos+size]
            pos += size
            try:
                value = Pro(raw)
            except:
                try:
                    value = raw.decode('utf-8')
                except:
                    value = raw.hex()
        elif wire_type == 5:
            value = int.from_bytes(data[pos:pos+4], "little")
            pos += 4
        elif wire_type == 1:
            value = int.from_bytes(data[pos:pos+8], "little")
            pos += 8
        else:
            raise Exception(f"Unsupported wire type: {wire_type}")
        if field_num in fields:
            if not isinstance(fields[field_num], list):
                fields[field_num] = [fields[field_num]]
            fields[field_num].append(value)
        else:
            fields[field_num] = value
    return fields

# ============================================================
# HELPER FUNCTIONS - FROM app.py
# ============================================================

def RoFl(session, password):
    url = "https://100067.connect.garena.com/api/v2/oauth/guest:register"
    payload = {"app_id": 100067, "client_type": 2, "password": password, "source": 2}
    json_body = json.dumps(payload, separators=(',', ':'))
    data_to_sign = cLiEnTsEcReT + json_body
    signature = hashlib.sha256(data_to_sign.encode()).hexdigest()
    headers = {
        "User-Agent": "GarenaMSDK/4.0.39(FRL-AN00a ;Android 10;nu;HK;)",
        "Authorization": f"Signature {signature}",
        "Content-Type": "application/json; charset=utf-8"
    }
    resp = session.post(url, data=json_body, headers=headers, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        if data.get("code") == 0:
            return str(data["data"]["uid"])
        else:
            raise Exception(f"Register failed: {data}")
    else:
        resp.raise_for_status()
        raise Exception(f"Unexpected response: {resp.text}")

def yEet(length=6, chars=string.ascii_uppercase + string.digits + "-_."):
    return ''.join(random.choice(chars) for _ in range(length))

def pWe():
    try:
        return requests.get('https://api.ipify.org', timeout=3).text
    except:
        return "0.0.0.0"

def sUs():
    return "GarenaMSDK/4.0.39(FRL-AN00a ;Android 10;nu;HK;)"

def bRuH():
    return "okhttp/3.12.1"

def fInE(original):
    keystream = [0x30,0x30,0x30,0x32,0x30,0x31,0x37,0x30,0x30,0x30,0x30,0x30,0x32,0x30,0x31,0x37,
                 0x30,0x30,0x30,0x30,0x30,0x32,0x30,0x31,0x37,0x30,0x30,0x30,0x30,0x30,0x32,0x30]
    encoded = ""
    for i in range(len(original)):
        orig_byte = ord(original[i])
        key_byte = keystream[i % len(keystream)]
        result_byte = orig_byte ^ key_byte
        encoded += chr(result_byte)
    return encoded

def yAy(s):
    return ''.join(c if 32 <= ord(c) <= 126 else f'\\u{ord(c):04x}' for c in s)

def nOp(nick_b64):
    if not nick_b64:
        return ""
    try:
        decoded_bytes = base64.b64decode(nick_b64)
        key_len = len(nIcKXoR)
        xored = bytes([decoded_bytes[i] ^ nIcKXoR[i % key_len] for i in range(len(decoded_bytes))])
        return xored.decode('utf-8', errors='ignore')
    except:
        return nick_b64

def wOw(func, session, *args, max_retries=3, **kwargs):
    for attempt in range(max_retries):
        try:
            return func(session, *args, **kwargs)
        except:
            if attempt == max_retries - 1:
                raise
            time.sleep(0.5)
    return None

def hAhA(session, password):
    return RoFl(session, password)

def lMaO(session, uid, password):
    url = "https://100067.connect.garena.com/api/v2/oauth/guest/token:grant"
    payload = {
        "client_id":100067, "client_secret":cLiEnTsEcReT, "client_type":2,
        "password":password, "response_type":"token", "uid":uid
    }
    headers = {"User-Agent": sUs(), "Content-Type": "application/json"}
    resp = session.post(url, json=payload, headers=headers, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise Exception(f"Token grant failed: {data}")
    return data["data"]["access_token"], data["data"]["open_id"]

def gG(session, name, access_token, open_id, region, is_ghost=False):
    global cOnSeCuTiVe
    url = "https://loginbp.ggpolarbear.com/MajorRegister"
    host = "loginbp.ggpolarbear.com"
    exp_digits = {'0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹'}
    num = random.randint(1,99999)
    exp = ''.join(exp_digits[d] for d in f"{num:05d}")
    name = name[:7] + exp
    lang_code = "pt" if is_ghost else rEgIoNlAnG.get(region.upper(), "en")
    encoded_result = fInE(open_id)
    field_unicode = yAy(encoded_result)
    field_bytes = codecs.decode(field_unicode, 'unicode_escape').encode('latin1')
    fields_dict = {
        "1": name, "2": access_token, "3": open_id,
        "5": 102000007, "6": 4, "7": 1, "13": 1,
        "14": field_bytes, "15": lang_code, "16": 2
    }
    plaintext = xPro(fields_dict)
    encrypted_payload = Noob(plaintext)
    headers = {
        "Accept-Encoding": "gzip", "Authorization": "Bearer", "Connection": "Keep-Alive",
        "Content-Type": "application/x-www-form-urlencoded", "Expect": "100-continue",
        "Host": host, "ReleaseVersion": "OB54",
        "User-Agent": bRuH(), "X-GA": "v1 1", "X-Unity-Version": "2018.4."
    }
    try:
        resp = session.post(url, headers=headers, data=encrypted_payload, timeout=15)
        resp.raise_for_status()
        with iPlOcK:
            cOnSeCuTiVe = 0
        return Pro(resp.content)
    except Exception as e:
        with iPlOcK:
            cOnSeCuTiVe += 1
            if cOnSeCuTiVe >= 10:
                renew_tor_ip()
                time.sleep(1)
                cOnSeCuTiVe = 0
        raise

def nIcE(session, access_token, open_id, region, lang_code):
    url = "https://loginbp.ggpolarbear.com/MajorLogin"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ip = pWe()
    if region.upper() == "IND":
        device_model = random.choice(INDIAN_DEVICES)
        carrier = random.choice(INDIAN_CARRIERS)
        city = random.choice(INDIAN_CITIES)
    else:
        device_model = "Asus ASUS_AI2401_A"
        carrier = "GrameenPhone"
        city = "Dhaka"
    gpu = "Adreno (TM) 640"
    
    def qT(n):
        out = []
        while True:
            b = n & 0x7F
            n >>= 7
            if n: b |= 0x80
            out.append(b)
            if not n: break
        return bytes(out)
    
    def zZ(f, v):
        return qT((f << 3) | 0) + qT(v)
    
    def xX(f, v):
        data = v.encode() if isinstance(v, str) else v
        return qT((f << 3) | 2) + qT(len(data)) + data
    
    fields = {
        3: now_str,
        4: "free fire",
        5: 1,
        7: "1.126.5",
        8: "Android OS 5.1.1 / API-22 (LMY48Z/rel.se.infra.20220128.171448)",
        9: "Handheld",
        10: carrier,
        11: "WIFI",
        17: gpu,
        18: "OpenGL ES 3.0",
        19: "Google|4645e530-e790-4be2-ae7c-6f64d1259603",
        20: ip,
        21: lang_code,
        22: open_id,
        23: 4,
        24: "Handheld",
        25: device_model,
        26: region.upper(),
        29: access_token,
        33: carrier,
        34: "WIFI",
        37: "7428b253defc164018c604a1ebbfebdf",
        73: "/data/app/com.dts.freefireth-1/lib/arm",
        75: "H4c322aeb56444feaa151d1ea91a8f7f2|/data/app/com.dts.freefireth-1/base.apk",
        76: 2,
        78: 2,
        79: 2,
        83: "OpenGLES2",
        85: city,
        87: "android",
        88: "KqsHTywQqGHMgPbDY9P2mhkxXj/beObk/TFNpmgaucQwxyLu9hA478WEQCV0Mgaz9UivYUPpKNwPzgZhvDhSsUDMAFY=",
        90: '{"cur_rate":null,"support_etc2":false}',
        97: 1,
        98: 1,
        99: "4",
        100: "4"
    }
    
    packet = b''
    for f, v in fields.items():
        if isinstance(v, int): 
            packet += zZ(f, v)
        elif isinstance(v, str): 
            packet += xX(f, v)
        elif isinstance(v, bytes): 
            packet += xX(f, v)
    
    encrypted = Noob(packet)
    headers = {
        "Accept-Encoding": "gzip", 
        "Connection": "Keep-Alive",
        "Content-Type": "application/x-www-form-urlencoded", 
        "Expect": "100-continue",
        "ReleaseVersion": "OB54", 
        "User-Agent": bRuH(),
        "X-GA": "v1 1", 
        "X-Unity-Version": "2018.4."
    }
    resp = session.post(url, headers=headers, data=encrypted, timeout=15)
    resp.raise_for_status()
    decoded = Pro(resp.content)
    jwt_token = decoded.get(8)
    if isinstance(jwt_token, list):
        jwt_token = jwt_token[0] if jwt_token else None
    return decoded, jwt_token

def dUdE(session, region_code, jwt_token):
    url = "https://loginbp.ggpolarbear.com/ChooseRegion"
    if region_code.upper() == "CIS":
        region_code = "ru"
    else:
        region_code = region_code.upper()
    fields_dict = {"1": region_code}
    plaintext = xPro(fields_dict)
    encrypted_payload = Noob(plaintext)
    headers = {
        "Accept-Encoding": "gzip", "Authorization": f"Bearer {jwt_token}",
        "Connection": "Keep-Alive", "Content-Type": "application/x-www-form-urlencoded",
        "Expect": "100-continue", "ReleaseVersion": "OB54",
        "User-Agent": bRuH(), "X-GA": "v1 1", "X-Unity-Version": "2018.4."
    }
    resp = session.post(url, headers=headers, data=encrypted_payload, timeout=10)
    return resp.status_code == 200

def bYe(session, jwt_token, client_url):
    url = f"https://{client_url}/GetLoginData"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ip = pWe()
    device_model = random.choice(INDIAN_DEVICES)
    carrier = random.choice(INDIAN_CARRIERS)
    city = random.choice(INDIAN_CITIES)
    gpu = "Adreno (TM) 640"
    open_id = "24adf2d6806cf61bd95d4cd3b57a0bd9"
    
    def qT(n):
        out = []
        while True:
            b = n & 0x7F
            n >>= 7
            if n: b |= 0x80
            out.append(b)
            if not n: break
        return bytes(out)
    
    def zZ(f, v):
        return qT((f << 3) | 0) + qT(v)
    
    def xX(f, v):
        data = v.encode() if isinstance(v, str) else v
        return qT((f << 3) | 2) + qT(len(data)) + data
    
    fields = {
        3: now_str,
        4: "free fire",
        5: 1,
        7: "1.126.5",
        8: "Android OS 5.1.1 / API-22 (LMY48Z/rel.se.infra.20220128.171448)",
        9: "Handheld",
        10: carrier,
        11: "WIFI",
        17: gpu,
        18: "OpenGL ES 3.0",
        19: "Google|4645e530-e790-4be2-ae7c-6f64d1259603",
        20: ip,
        21: "en",
        22: open_id,
        23: 4,
        24: "Handheld",
        25: device_model,
        26: "IND",
        29: jwt_token,
        33: carrier,
        34: "WIFI",
        37: "7428b253defc164018c604a1ebbfebdf",
        73: "/data/app/com.dts.freefireth-1/lib/arm",
        75: "H4c322aeb56444feaa151d1ea91a8f7f2|/data/app/com.dts.freefireth-1/base.apk",
        83: "OpenGLES2",
        85: city,
        87: "android",
        88: "KqsHT8nWdkA7u/m7k8vg2H5FgrCGa4lfww3nHBGRHRPwDFV4LyCj8sT23O/P6K06qC3MOLZRThwWwul+g2goHwtQJy8=",
        90: '{"cur_rate":null,"support_etc2":false}'
    }
    
    packet = b''
    for f, v in fields.items():
        if isinstance(v, int): 
            packet += zZ(f, v)
        elif isinstance(v, str): 
            packet += xX(f, v)
        elif isinstance(v, bytes): 
            packet += xX(f, v)
    
    encrypted_payload = Noob(packet)
    
    headers = {
        'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 12)",
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip",
        'Content-Type': "application/x-www-form-urlencoded",
        'Authorization': f"Bearer {jwt_token}",
        'X-Unity-Version': "2018.4.11f1",
        'X-GA': "v1 1",
        'ReleaseVersion': "OB54"
    }
    
    try:
        resp = session.post(url, headers=headers, data=encrypted_payload, timeout=10)
        return resp.status_code == 200
    except:
        return False

def hElLo(jwt_token):
    try:
        parts = jwt_token.split('.')
        if len(parts) != 3:
            return None, None
        payload = parts[1]
        payload += '=' * (4 - len(payload) % 4)
        data = json.loads(base64.b64decode(payload))
        lock_region = data.get("lock_region") or data.get("noti_region")
        raw_nick = data.get("nickname")
        if raw_nick:
            nickname = nOp(raw_nick)
        else:
            nickname = ""
        return lock_region, nickname
    except:
        return None, None

# ============================================================
# ACCOUNT CREATOR CLASS - FROM app.py
# ============================================================

class AcCoUnTcReAtOr:
    def __init__(self, region, nickname_prefix, password_prefix, password_mode, auto_activate, total_target, ghost=False):
        self.region = region
        self.nickname_prefix = nickname_prefix[:7]
        self.password_prefix = password_prefix.upper()
        self.password_mode = password_mode
        self.auto_activate = auto_activate
        self.total_target = total_target
        self.ghost = ghost
        self.results = []
        self.lock = threading.Lock()
        self.created_count = 0
        self.fail_counter = 0
        self.ip_blocked = False
        self.stop = False
        self.results_lock = threading.Lock()
        self.saved_uids = set()
        self.file_lock = threading.Lock()
        self.log_callback = None

    def set_log_callback(self, callback):
        self.log_callback = callback

    def log(self, message, msg_type="info"):
        if self.log_callback:
            self.log_callback(message, msg_type)

    def load_existing_uids(self):
        if self.ghost:
            folder = "GEN/GHOST"
        else:
            folder = f"GEN/{self.region}"
        txt_path = os.path.join(folder, f"Accounts-{self.region}.txt")
        try:
            if os.path.exists(txt_path):
                with open(txt_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        match = re.search(r'UiD = (\d+)', line)
                        if match:
                            self.saved_uids.add(match.group(1))
        except:
            pass

    def gEnPaSs(self):
        r1 = yEet(6)
        r2 = yEet(6)
        plain = f"{self.password_prefix}_{r1}-SPIDER{r2}"
        return plain, plain

    def save_single_account(self, acc):
        if self.ghost:
            folder = "GEN/GHOST"
        else:
            folder = f"GEN/{self.region}"
        try:
            os.makedirs(folder, exist_ok=True)
        except:
            folder = "."
        txt_path = os.path.join(folder, f"Accounts-{self.region}.txt")
        
        with self.file_lock:
            try:
                uid = acc.get('uid', '')
                existing_uids = set()
                if os.path.exists(txt_path):
                    with open(txt_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            match = re.search(r'UiD = (\d+)', line)
                            if match:
                                existing_uids.add(match.group(1))
                
                if uid not in existing_uids:
                    with open(txt_path, 'a', encoding='utf-8') as f:
                        line = f"BOT = {acc.get('game_uid', '')} | UiD = {uid} | PassWord = {acc.get('password', '')} | NamE = {acc.get('nickname', '')} | ReGioN = {acc.get('region', '')}\n"
                        f.write(line)
                    with self.results_lock:
                        self.saved_uids.add(uid)
                    return True
            except:
                pass
        return False

    def cReAtE(self, thread_id):
        if self.stop or self.ip_blocked:
            return None
        session = get_pool_session()
        try:
            store_pass, api_pass = self.gEnPaSs()
            uid = wOw(hAhA, session, api_pass)
            
            with self.results_lock:
                if uid in self.saved_uids:
                    return None
            
            access_token, open_id = wOw(lMaO, session, uid, api_pass)
            reg_resp = wOw(gG, session, self.nickname_prefix, access_token, open_id, self.region, self.ghost)
            account_id = reg_resp.get(3)
            if not account_id:
                raise Exception("No account_id")
            account_id = str(account_id)
            lang_code = rEgIoNlAnG.get(self.region, "en") if not self.ghost else "pt"
            login_resp, jwt_token = wOw(nIcE, session, access_token, open_id, self.region, lang_code)
            if not jwt_token:
                raise Exception("No JWT")
            lock_region, nickname = hElLo(jwt_token)
            if not nickname:
                nickname = self.nickname_prefix
            need_lock = False
            final_jwt = jwt_token
            client_url = None
            if not self.ghost:
                if lock_region and lock_region not in (None, 'None', '..', ''):
                    if lock_region != self.region.upper():
                        need_lock = True
                else:
                    need_lock = True
                if need_lock:
                    dUdE(session, self.region, jwt_token)
                    login_resp2, jwt_token2 = wOw(nIcE, session, access_token, open_id, self.region, lang_code)
                    if jwt_token2:
                        final_jwt = jwt_token2
                        lock_region2, nickname2 = hElLo(jwt_token2)
                        if nickname2:
                            nickname = nickname2
                        lock_region = lock_region2
                    else:
                        lock_region = None
                last_resp = login_resp2 if need_lock and 'login_resp2' in locals() else login_resp
                client_url_raw = last_resp.get(10)
                if isinstance(client_url_raw, str):
                    client_url = client_url_raw
                elif isinstance(client_url_raw, list):
                    client_url = client_url_raw[0] if client_url_raw else None
                if client_url and client_url.startswith("https://"):
                    client_url = client_url[8:]
                if not client_url:
                    if self.region.upper() == "IND":
                        client_url = "client.ind.freefiremobile.com"
                    elif self.region.upper() in ["BR","US","NA","SAC"]:
                        client_url = "client.us.freefiremobile.com"
                    else:
                        client_url = "clientbp.ggpolarbear.com"
            else:
                client_url = "clientbp.ggpolarbear.com"
                lock_region = "GHOST"
            activated = False
            if self.auto_activate and final_jwt and client_url and not self.ghost:
                activated = wOw(bYe, session, final_jwt, client_url)
            final_region = lock_region if lock_region and not self.ghost else "GHOST"
            stored_password = store_pass
            
            acc = {
                "nickname": nickname,
                "game_uid": account_id,
                "region": final_region,
                "uid": str(uid),
                "password": stored_password,
                "activated": activated
            }
            
            with self.results_lock:
                self.saved_uids.add(uid)
            
            return acc
        except:
            return None

    def wOrKeR(self, thread_id):
        global ACCOUNT_COUNTER_FOR_IP_ROTATION
        threading.current_thread().name = f"T{thread_id}"
        while not self.stop:
            if self.created_count >= self.total_target:
                break
            with iPlOcK:
                ACCOUNT_COUNTER_FOR_IP_ROTATION += 1
                if ACCOUNT_COUNTER_FOR_IP_ROTATION >= IP_ROTATION_INTERVAL:
                    ACCOUNT_COUNTER_FOR_IP_ROTATION = 0
                    renew_tor_ip()
                    time.sleep(0.5)
            acc = self.cReAtE(thread_id)
            if acc:
                with self.lock:
                    self.created_count += 1
                self.save_single_account(acc)
                output_line = f"BOT = {acc.get('game_uid', '')} | UiD = {acc.get('uid', '')} | PassWord = {acc.get('password', '')} | NamE = {acc.get('nickname', '')} | ReGioN = {acc.get('region', '')}"
                self.log(output_line, "account")
                
                # Check rarity
                is_rare, rarity_type, reason, rarity_score = check_account_rarity(acc)
                if is_rare:
                    self.log(f"💎 RARE: {acc['game_uid']} - Score: {rarity_score}", "rare")
                    save_rare_account(acc, rarity_type, reason, rarity_score, self.ghost)
                
                # Check couples
                is_couple, couple_reason, partner_data = check_account_couples(acc, thread_id)
                if is_couple and partner_data:
                    self.log(f"💑 COUPLE: {acc['game_uid']} & {partner_data['game_uid']}", "couple")
                    save_couples_account(acc, partner_data, couple_reason, self.ghost)
            else:
                time.sleep(0.1)
        if self.created_count >= self.total_target:
            self.stop = True

    def rUn(self):
        self.load_existing_uids()
        start_tor()
        time.sleep(1)
        init_session_pool()
        
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=ThReAdS) as executor:
            futures = []
            for i in range(ThReAdS):
                futures.append(executor.submit(self.wOrKeR, i+1))
            
            while self.created_count < self.total_target and not self.stop:
                time.sleep(0.5)
            
            self.stop = True
            for future in futures:
                try:
                    future.cancel()
                except:
                    pass

# ============================================================
# RARITY & COUPLES FUNCTIONS - FROM STAR_FAST_GENERATOR
# ============================================================

RARITY_SCORE_THRESHOLD = 3
POTENTIAL_COUPLES = {}
COUPLES_LOCK = threading.Lock()

ACCOUNT_RARITY_PATTERNS = {
    "REPEATED_DIGITS_4": [r"(\d)\1{3,}", 3],
    "REPEATED_DIGITS_3": [r"(\d)\1\1(\d)\2\2", 2],
    "SEQUENTIAL_5": [r"(12345|23456|34567|45678|56789)", 4],
    "SEQUENTIAL_4": [r"(0123|1234|2345|3456|4567|5678|6789|9876|8765|7654|6543|5432|4321|3210)", 3],
    "PALINDROME_6": [r"^(\d)(\d)(\d)\3\2\1$", 5],
    "PALINDROME_4": [r"^(\d)(\d)\2\1$", 3],
    "SPECIAL_COMBINATIONS_HIGH": [r"(69|420|1337|007)", 4],
    "SPECIAL_COMBINATIONS_MED": [r"(100|200|300|400|500|666|777|888|999)", 2],
    "QUADRUPLE_DIGITS": [r"(1111|2222|3333|4444|5555|6666|7777|8888|9999|0000)", 4],
    "MIRROR_PATTERN_HIGH": [r"^(\d{2,3})\1$", 3],
    "MIRROR_PATTERN_MED": [r"(\d{2})0\1", 2],
    "GOLDEN_RATIO": [r"1618|0618", 3]
}

def check_account_rarity(account_data):
    account_id = account_data.get("game_uid", "")
    if account_id == "N/A" or not account_id:
        return False, None, None, 0
    rarity_score = 0
    detected_patterns = []
    for rarity_type, pattern_data in ACCOUNT_RARITY_PATTERNS.items():
        pattern = pattern_data[0]
        score = pattern_data[1]
        if re.search(pattern, account_id):
            rarity_score += score
            detected_patterns.append(rarity_type)
    account_id_digits = [int(d) for d in account_id if d.isdigit()]
    if len(set(account_id_digits)) == 1 and len(account_id_digits) >= 4:
        rarity_score += 5
        detected_patterns.append("UNIFORM_DIGITS")
    if len(account_id_digits) >= 4:
        differences = [account_id_digits[i+1] - account_id_digits[i] for i in range(len(account_id_digits)-1)]
        if len(set(differences)) == 1:
            rarity_score += 4
            detected_patterns.append("ARITHMETIC_SEQUENCE")
    if len(account_id) <= 8 and account_id.isdigit() and int(account_id) < 1000000:
        rarity_score += 3
        detected_patterns.append("LOW_ACCOUNT_ID")
    if rarity_score >= RARITY_SCORE_THRESHOLD:
        reason = f"Account ID {account_id} - Score: {rarity_score} - Patterns: {', '.join(detected_patterns)}"
        return True, "RARE_ACCOUNT", reason, rarity_score
    return False, None, None, rarity_score

def check_account_couples(account_data, thread_id):
    account_id = account_data.get("game_uid", "")
    if account_id == "N/A" or not account_id:
        return False, None, None
    with COUPLES_LOCK:
        for stored_id, stored_data in list(POTENTIAL_COUPLES.items()):
            stored_account_id = stored_data.get('game_uid', '')
            if account_id and stored_account_id and abs(int(account_id) - int(stored_account_id)) == 1:
                partner_data = stored_data
                del POTENTIAL_COUPLES[stored_id]
                return True, f"Sequential Account IDs: {account_id} & {stored_account_id}", partner_data
            if account_id == stored_account_id[::-1]:
                partner_data = stored_data
                del POTENTIAL_COUPLES[stored_id]
                return True, f"Mirror Account IDs: {account_id} & {stored_account_id}", partner_data
        POTENTIAL_COUPLES[account_id] = {
            'uid': account_data.get('uid', ''),
            'game_uid': account_id,
            'name': account_data.get('nickname', ''),
            'password': account_data.get('password', ''),
            'region': account_data.get('region', ''),
            'thread_id': thread_id,
            'timestamp': datetime.now().isoformat()
        }
    return False, None, None

def save_rare_account(account_data, rarity_type, reason, rarity_score, is_ghost=False):
    try:
        if is_ghost:
            rare_filename = os.path.join("SPIDER", "GHOST", "RAREACCOUNT", "rare-ghost.json")
        else:
            region = account_data.get('region', 'UNKNOWN')
            rare_filename = os.path.join("SPIDER", "RARE ACCOUNTS", f"rare-{region}.json")
        os.makedirs(os.path.dirname(rare_filename), exist_ok=True)
        rare_entry = {
            'uid': account_data["uid"],
            'password': account_data["password"],
            'account_id': account_data.get("game_uid", "N/A"),
            'name': account_data["nickname"],
            'region': "SPIDER" if is_ghost else account_data.get('region', 'UNKNOWN'),
            'rarity_type': rarity_type,
            'rarity_score': rarity_score,
            'reason': reason,
            'date_identified': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'jwt_token': account_data.get('jwt_token', ''),
            'thread_id': account_data.get('thread_id', 'N/A')
        }
        rare_list = []
        if os.path.exists(rare_filename):
            try:
                with open(rare_filename, 'r', encoding='utf-8') as f:
                    rare_list = json.load(f)
            except:
                rare_list = []
        existing_ids = [acc.get('account_id') for acc in rare_list]
        if account_data.get("game_uid", "N/A") not in existing_ids:
            rare_list.append(rare_entry)
            with open(rare_filename, 'w', encoding='utf-8') as f:
                json.dump(rare_list, f, indent=2, ensure_ascii=False)
            return True
        return False
    except:
        return False

def save_couples_account(account1, account2, reason, is_ghost=False):
    try:
        if is_ghost:
            couples_filename = os.path.join("SPIDER", "GHOST", "COUPLESACCOUNT", "couples-ghost.json")
        else:
            region = account1.get('region', 'UNKNOWN')
            couples_filename = os.path.join("SPIDER", "COUPLES ACCOUNTS", f"couples-{region}.json")
        os.makedirs(os.path.dirname(couples_filename), exist_ok=True)
        couples_entry = {
            'couple_id': f"{account1.get('game_uid', 'N/A')}_{account2.get('game_uid', 'N/A')}",
            'account1': {
                'uid': account1["uid"],
                'password': account1["password"],
                'account_id': account1.get("game_uid", "N/A"),
                'name': account1["nickname"],
                'thread_id': account1.get('thread_id', 'N/A')
            },
            'account2': {
                'uid': account2["uid"],
                'password': account2["password"],
                'account_id': account2.get("game_uid", "N/A"),
                'name': account2["nickname"],
                'thread_id': account2.get('thread_id', 'N/A')
            },
            'reason': reason,
            'region': "SPIDER" if is_ghost else account1.get('region', 'UNKNOWN'),
            'date_matched': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        couples_list = []
        if os.path.exists(couples_filename):
            try:
                with open(couples_filename, 'r', encoding='utf-8') as f:
                    couples_list = json.load(f)
            except:
                couples_list = []
        existing_couples = [couple.get('couple_id') for couple in couples_list]
        if couples_entry['couple_id'] not in existing_couples:
            couples_list.append(couples_entry)
            with open(couples_filename, 'w', encoding='utf-8') as f:
                json.dump(couples_list, f, indent=2, ensure_ascii=False)
            return True
        return False
    except:
        return False

# ============================================================
# WEB ROUTES
# ============================================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/regions')
def get_regions():
    return jsonify(rEgIoNlIsT)

@app.route('/api/start', methods=['POST'])
def start_generation():
    global is_generating, generation_thread, current_generation_id, generation_queue
    
    if is_generating:
        return jsonify({'status': 'error', 'message': 'Generation already running'})
    
    data = request.json
    region = data.get('region', 'IND')
    nickname = data.get('nickname', 'SPIDER')
    password = data.get('password', 'SPIDY')
    total = int(data.get('total', 100))
    threads = int(data.get('threads', 50))
    ghost = data.get('ghost', False)
    auto_activate = data.get('auto_activate', True)
    
    # Clear old queue
    while not generation_queue.empty():
        try:
            generation_queue.get_nowait()
        except:
            break
    
    is_generating = True
    current_generation_id = datetime.now().strftime('%Y%m%d%H%M%S')
    
    def run_generator():
        global is_generating
        try:
            generator = AcCoUnTcReAtOr(region, nickname, password, "plain", auto_activate, total, ghost)
            generator.set_log_callback(log_callback)
            generator.rUn()
        except Exception as e:
            generation_queue.put({'type': 'error', 'message': str(e)})
        finally:
            is_generating = False
            generation_queue.put({'type': 'done', 'message': 'Generation complete'})
    
    def log_callback(message, msg_type="info"):
        generation_queue.put({'type': msg_type, 'message': message})
    
    generation_thread = threading.Thread(target=run_generator)
    generation_thread.daemon = True
    generation_thread.start()
    
    return jsonify({'status': 'started', 'generation_id': current_generation_id})

@app.route('/api/status')
def get_status():
    return jsonify({
        'running': is_generating,
        'generation_id': current_generation_id
    })

@app.route('/api/stop', methods=['POST'])
def stop_generation():
    global is_generating
    is_generating = False
    return jsonify({'status': 'stopped'})

@app.route('/api/stream')
def stream_logs():
    def generate():
        while True:
            try:
                msg = generation_queue.get(timeout=2)
                yield f"data: {json.dumps(msg)}\n\n"
                if msg.get('type') == 'done':
                    break
            except queue.Empty:
                yield f"data: {json.dumps({'type': 'ping'})}\n\n"
                if not is_generating and generation_queue.empty():
                    break
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/api/accounts')
def get_accounts():
    accounts = []
    base_dir = "GEN"
    if os.path.exists(base_dir):
        for region in os.listdir(base_dir):
            region_path = os.path.join(base_dir, region)
            if os.path.isdir(region_path):
                for file in os.listdir(region_path):
                    if file.endswith('.txt'):
                        file_path = os.path.join(region_path, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                for line in f:
                                    if 'UiD' in line:
                                        accounts.append({
                                            'region': region,
                                            'line': line.strip()
                                        })
                        except:
                            pass
    return jsonify(accounts[:100])

@app.route('/api/download/<region>')
def download_accounts(region):
    """Download accounts for a specific region as .txt file"""
    file_path = os.path.join("GEN", region, f"Accounts-{region}.txt")
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'No accounts found for this region'}), 404
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if not content.strip():
            return jsonify({'error': 'Accounts file is empty'}), 404
        
        response = Response(
            content,
            mimetype='text/plain',
            headers={
                'Content-Disposition': f'attachment; filename=Accounts-{region}.txt',
                'Content-Type': 'text/plain; charset=utf-8'
            }
        )
        return response
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/all')
def download_all_accounts():
    """Download all accounts from all regions as a single .txt file"""
    base_dir = "GEN"
    all_content = []
    
    if not os.path.exists(base_dir):
        return jsonify({'error': 'No accounts found'}), 404
    
    for region in os.listdir(base_dir):
        region_path = os.path.join(base_dir, region)
        if os.path.isdir(region_path):
            for file in os.listdir(region_path):
                if file.endswith('.txt'):
                    file_path = os.path.join(region_path, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if content.strip():
                                all_content.append(f"========== {region} ==========")
                                all_content.append(content)
                                all_content.append("")
                    except:
                        pass
    
    if not all_content:
        return jsonify({'error': 'No accounts found'}), 404
    
    combined = "\n".join(all_content)
    
    response = Response(
        combined,
        mimetype='text/plain',
        headers={
            'Content-Disposition': 'attachment; filename=All-Accounts.txt',
            'Content-Type': 'text/plain; charset=utf-8'
        }
    )
    return response

@app.route('/api/regions_with_accounts')
def get_regions_with_accounts():
    """Get list of regions that have accounts"""
    regions = []
    base_dir = "GEN"
    
    if os.path.exists(base_dir):
        for region in os.listdir(base_dir):
            region_path = os.path.join(base_dir, region)
            if os.path.isdir(region_path):
                for file in os.listdir(region_path):
                    if file.endswith('.txt'):
                        file_path = os.path.join(region_path, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                count = sum(1 for _ in f if 'UiD' in _)
                                if count > 0:
                                    regions.append({
                                        'region': region,
                                        'count': count
                                    })
                        except:
                            pass
                        break
    return jsonify(regions)

# ============================================================
# MAIN ENTRY
# ============================================================

if __name__ == '__main__':
    print(f"""
{Fore.MAGENTA}{Style.BRIGHT}
            ███████╗██████╗ ██╗██████╗ ███████╗██████╗ 
            ██╔════╝██╔══██╗██║██╔══██╗██╔════╝██╔══██╗
            ███████╗██████╔╝██║██║  ██║█████╗  ██████╔╝
            ╚════██║██╔═══╝ ██║██║  ██║██╔══╝  ██╔══██╗
            ███████║██║     ██║██████╔╝███████╗██║  ██║
            ╚══════╝╚═╝     ╚═╝╚═════╝ ╚══════╝╚═╝  ╚═╝
            
            🕷️  SPIDER GENERATOR WEB SERVER  🕷️
            http://127.0.0.1:5000
{Style.RESET_ALL}
    """)
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)