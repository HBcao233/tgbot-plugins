import re
import traceback
from telegram import (
  InputMediaPhoto,
  InputMediaVideo,
)
from plugin import handler
from util.log import logger


prefix = {
  'photo': 'p_',
  'video': 'v_',
  'document': 'd_',
  'audio': 'a_',
}


@handler('_')
async def pan(update, context, *_args, **_kwargs):
  message = update.message
  
  if getattr(message, 'media_group_id', None):
    if not context.bot_data.get('media_group', None): context.bot_data['media_group'] = {}
    if not context.bot_data['media_group'].get(message.media_group_id, None): 
      context.bot_data['media_group'][message.media_group_id] = []
      context.job_queue.run_once(pan_timer, 1, data=message.media_group_id)
    context.bot_data['media_group'][message.media_group_id].append(message)
    return
  
  code = None
  if getattr(message, 'photo', None):
    code = prefix['photo'] + str(message.photo[-1].file_id)
  if getattr(message, 'video', None):
    code = prefix['video'] + str(message.video.file_id)
  if getattr(message, 'document', None):
    code = prefix['document'] + str(message.document.file_id)
  if getattr(message, 'audio', None):
    code = prefix['audio'] + str(message.audio.file_id)
  if code:
    await update.message.reply_text(
      f'<code>{code}</code>', 
      reply_to_message_id=update.message.message_id,
      parse_mode='HTML',
    )


async def pan_timer(context):
  # logger.info(context.job.data)
  ms = context.bot_data.get('media_group', {}).get(context.job.data, [])
  res = []
  for m in ms:
    if m.photo:
      res.append(prefix['photo'] + m.photo[-1].file_id)
    elif m.video:
      res.append(prefix['video'] + m.video.file_id)
  res = list(map(lambda x : "<code>" + x + "</code>", res))
  await context.bot.sendMessage(
      chat_id=ms[0].chat.id,
      text="\n".join(res), 
      reply_to_message_id=ms[0].message_id,
      parse_mode='HTML',
  )
  if 'media_group' in context.bot_data.keys() and context.job.data in context.bot_data['media_group'].keys():
    del context.bot_data['media_group'][context.job.data]
    

caption = 'This message will delete in 1 hour'
_file_pattern = (
  r"(" +
  prefix['photo'] + '|' +
  prefix['video'] + '|' +
  prefix['document'] + '|' +
  prefix['audio'] +
  r")" +
  "([a-zA-Z0-9-_]+)" 
)
@handler("file", private_pattern=_file_pattern)
async def file(update, context, text):
  message = update.message
  bot = context.bot
  r = re.findall(_file_pattern, text)
  # logger.info(r)

  ms = []
  async def _s():
    nonlocal ms, bot
    if len(ms) > 0:
      with ms[0]._unfrozen():
        ms[0].caption = caption
      m = await bot.sendMediaGroup(chat_id=message.chat_id, media=ms, reply_to_message_id=message.message_id)
      context.job_queue.run_once(del_msgs, 3600, data=m)
      ms = []
  
  for i in r:
    try:
      if i[0] == prefix['photo']:
        ms.append(InputMediaPhoto(media=i[1]))
      elif i[0] == prefix['video']:
        ms.append(InputMediaVideo(media=i[1]))
      elif i[0] == prefix['document']:
        await _s()
        m = await bot.sendDocument(
          chat_id=message.chat_id, 
          document=i[1], 
          reply_to_message_id=message.message_id,
          caption=caption,
        )
        context.job_queue.run_once(del_msgs, 3600, data=m)
      elif i[0] == prefix['audio']:
        await _s()
        await bot.sendAudio(chat_id=message.chat_id, audio=i[1], reply_to_message_id=message.message_id)
    except:
      logger.error(traceback.format_exc())
      await bot.sendMessage(chat_id=message.chat.id, text="Error, maybe non-existent", reply_to_message_id=message.message_id)
  await _s()
    
    
async def del_msgs(context):
  logger.info(context.job.data)
  m = context.job.data
  if not hasattr(m, "__iter__"):
    m = [m]
  for i in m:
    try:
      await context.bot.delete_message(
        chat_id=i.chat.id,
        message_id=i.message_id,
      )
    except:
      e = traceback.format_exc()
      if 'Message to delete not found' not in e:
        logger.warning(e)
        