import re
import time
import os.path
import httpx
from bs4 import BeautifulSoup
from decimal import Decimal

import util
from util.log import logger
from plugin import handler


_p = r'[0-9]*\.?[0-9]+'
_pattern=r'^[\+-]' + _p
@handler(
  'bookkeeping', 
  pattern=_pattern,
)
async def _bookkeeping(update, context, text):
  message = update.message
  if not (match := re.match(_pattern, text)):
    return 
  money = Decimal(match.group(0))
  if money == Decimal(0): return
  timestamp = round(time.time())
  now = time.localtime(timestamp)
  styletime = time.strftime("%Y-%m-%d %H:%M:%S", now)
  u = getUSDT()
  with Book(message.chat.id) as book:
    book[timestamp] = [round(money, 2), u]
  
  if money > 0:
    m = money / u
    msg = (
      f'+ {styletime} 入账 ' +
      f'{abs(money)}/{u}={m:.2f}U'
    )
  else:
    m = money * u
    msg = (
      f'- {styletime} 出账 ' +
      f'{abs(money)}U*{u}={m:.2f}'
    )
  await message.reply_text(
    msg,
    reply_to_message_id=message.message_id,
  )
 
    
@handler('', pattern='^账单')
async def _(update, context, text):
  message = update.message
  book = Book(message.chat.id)
  total_add = total_add_u = \
  total_sub = total_sub_u = Decimal(0)
  today = time.strftime('%Y%m%d')
  for i in sorted(book, reverse=True):
    if time.strftime('%Y%m%d', time.localtime(int(i))) != today:
      break
    ai = book[i]
    if ai is None: break
    m = Decimal(ai[0])
    u = Decimal(ai[1])
    if m > Decimal(0): 
      total_add += m
      total_add_u += m / u
    if m < Decimal(0):
      total_sub += abs(m) * u
      total_sub_u += abs(m) 
  _t = lambda x: '%g' % float(round(x, 2))
  msg = (
    f'总入账: {_t(total_add)}\n'
    f'总出账: {_t(total_sub)} | {_t(total_sub_u)}U\n'
    f'未出账: {_t(total_add - total_sub)} | {_t(total_add_u - total_sub_u)}U'
  )
  await message.reply_text(
    msg,
    reply_to_message_id=message.message_id,
  )
    

class Book(util.Data):
  def __init__(self, file: str):
    path = util.getFile('data/books/')
    if not os.path.isdir(path):
      os.mkdir(path)
    self.file = 'books/' + str(file)
    self.data = util.getData(self.file)
    
    
def getUSDT():
  url = 'https://www.google.com/finance/quote/USDT-CNY'
  r = httpx.get(url, headers={
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1517.62",
    'Referer': 'https://www.google.com/',
    'host': 'www.google.com'
  })
  soup = BeautifulSoup(r.text, "html.parser")
  main = soup.select('main c-wiz span')
  usdt = Decimal(main[0].select('div div')[0].text)
  return usdt
    