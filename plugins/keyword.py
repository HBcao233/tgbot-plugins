import re
import random
import config
import util
from util.log import logger
from plugin import handler


@handler('add', info='添加关键词', scope='superadmin')
async def _add(update, context, text):
  message = update.message
  if message.chat.id not in config.superadmin:
    return
  if not getattr(message, 'reply_to_message', None):
    return await message.reply_text('请用命令回复一条消息', reply_to_message_id=message.message_id)
  
  if text == '':
    return await message.reply_text('请输入关键词', reply_to_message_id=message.message_id)
    
  with util.Data('keywords') as data:
    data[text] = f'{message.reply_to_message.chat.id}/{message.reply_to_message.message_id}'
  await message.reply_text(f'添加关键词 "{text}" 成功', reply_to_message_id=message.message_id)
  
  
@handler('del', info='删除关键词', scope='superadmin')
async def _(update, context, text):
  message = update.message
  if message.chat.id not in config.superadmin:
    return
  
  if text == '':
    return await message.reply_text('请输入需要删除的关键词', reply_to_message_id=message.message_id)
  
  with util.Data('keywords') as data:
    logger.info(repr(data))
    logger.info(text in data)
    if text not in data:
      return await message.reply_text(f'关键词 "{text}" 不存在', reply_to_message_id=message.message_id)
    del data[text] 
  await message.reply_text(f'删除关键词 "{text}" 成功', reply_to_message_id=message.message_id)
  
  
@handler('list', info='查看关键词列表', scope='superadmin')
async def _list(update, context, text):
  message = update.message
  if message.chat.id not in config.superadmin:
    return
  
  data = util.Data('keywords') 
  if len(data) == 0:
    return await message.reply_text('未添加任何关键词', reply_to_message_id=message.message_id)
  msg = ''
  for i in data.keys():
    msg += f'\n· <code>{i}</code>'
  await message.reply_text(
    f'关键词列表: {msg}', 
    reply_to_message_id=message.message_id,
    parse_mode='HTML',
  )
  
  
@handler('_')
async def _(update, context, text, *_args, **_kwargs):
  data = util.Data('keywords')
  ms = []
  for i in data.keys():
    if re.search(i, text):
      ms.append(data[i])
      
  if len(ms) > 0:
    m = random.choice(ms)
    arr = m.split('/')
    await context.bot.copy_message(
      from_chat_id=arr[0],
      message_id=arr[1],
      chat_id=update.message.chat.id,
    )