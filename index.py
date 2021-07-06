from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse
import random
import math
import time
import hashlib
import json

class AccountConverter(object):

    def __init__(self, params: str):
        self.bytes_list = bytearray()

        self.push_long(self.type_name_to_long(params))

    def char_to_symbol(self, c):
        if (ord(c) >= ord('a') and ord(c) <= ord('z')):
            return chr(((ord(c) - ord('a')) + 6))

        if (ord(c) >= ord('1') and ord(c) <= ord('5')):
            return chr(((ord(c) - ord('1')) + 1))
        return chr(0)

    def type_name_to_long(self, type_name):
        if type_name == None or type_name == "":
            return 0
        c = 0
        value = 0
        type_name_len = len(type_name)
        for i in range(12 + 1):
            if (i < type_name_len and i <= 12):
                c = ord(self.char_to_symbol(type_name[i]))
            if (i < 12):
                c &= 0x1f
                c <<= 64 - 5 * (i + 1)
            else:
                c &= 0x0f
            value |= c
        return value

    def push_base(self, val, iteration):
        for i in iteration:
            self.bytes_list.append(0xFF & val >> i)

    def push_long(self, val):
        self.push_base(val, range(0, 57, 8))


class handler(BaseHTTPRequestHandler):
  def getRand(self):
    arr = bytearray(8)
    for i in range(len(arr)):
        arr[i] = math.floor(random.random() * 255)
    return arr


  def mine(self, raw_data: dict) -> dict:
      data = dict()
      is_wam = raw_data['account_str'][-4:] == '.wam'
      good = False
      acc_and_lastmine = AccountConverter(raw_data['account_str']).bytes_list + raw_data['last_mine_arr']
      start = time.time()
      while not good:
          rand_arr = self.getRand()
          hex_digest = hashlib.sha256((acc_and_lastmine + rand_arr)).hexdigest()
          if is_wam:
              good = hex_digest[:4] == '0000'
          else:
              good = hex_digest[:6] == '000000'
          if good:
              if is_wam:
                  last = int(hex_digest[4:5], 16)
              else:
                  last = int(hex_digest[6:7], 16)
              good &= last <= raw_data['difficulty']
      end = time.time()
      data['nonce'] = rand_arr.hex()
      data['hash'] = hex_digest
      data['mining_time'] = round(end-start, 2)
      data['credit'] = "https://www.facebook.com/Thanet.Siriboon/"
      return data


  def do_GET(self):
    raw_data = {
      "account_str": "",
      "difficulty": 0,
      "last_mine_arr": bytearray()
    }
    parms = dict()
    try:
      for x in urlparse(self.path)[4].split("&"):
        d = x.split("=")
        parms[d[0]] = d[1]
      raw_data['last_mine_arr'] = bytearray.fromhex(parms["lastMineTx"][:16])
      raw_data['account_str'] = parms["waxaccount"]
      raw_data['difficulty'] = int(parms["difficulty"])
    except:
      self.send_response(200)
      self.send_header('Content-type', 'application/json')
      self.end_headers()
      self.wfile.write(json.dumps({"error": "ส่งค่ามาไม่ครบ", "credit": "https://www.facebook.com/Thanet.Siriboon/"}).encode('utf-8'))
      return
    data = self.mine(raw_data)
    self.send_response(200)
    self.send_header('Content-type', 'application/json')
    self.end_headers()
    self.wfile.write(json.dumps(data).encode('utf-8'))
    return
