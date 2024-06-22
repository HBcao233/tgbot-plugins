import re
import traceback
from telegram import (
  InputMediaPhoto,
  InputMediaVideo,
  ReplyParameters,
)
from plugin import handler
from util.log import logger


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
  
  if getattr(message, 'photo', None):
      await update.message.reply_text(
          f'<code>p_{message.photo[-1].file_id}</code>', 
          reply_to_message_id=update.message.message_id,
          parse_mode='HTML',
      )
  if getattr(message, 'video', None):
      await update.message.reply_text(
          f'<code>vi_{message.video.file_id}</code>', 
          reply_to_message_id=update.message.message_id,
          parse_mode='HTML',
      )
  if getattr(message, 'document', None):
      await update.message.reply_text(
          f'<code>d_{message.document.file_id}</code>', 
          reply_to_message_id=update.message.message_id,
          parse_mode='HTML',
      )
  if getattr(message, 'audio', None):
      await update.message.reply_text(
          f'<code>au_{message.audio.file_id}</code>', 
          reply_to_message_id=update.message.message_id,
          parse_mode='HTML',
      )


async def pan_timer(context):
  # logger.info(context.job.data)
  ms = context.bot_data.get('media_group', {}).get(context.job.data, [])
  res = []
  for m in ms:
    if m.photo:
      res.append("p_" + m.photo[-1].file_id)
    elif m.video:
      res.append("vi_" + m.video.file_id)
  res = list(map(lambda x : "<code>" + x + "</code>", res))
  await context.bot.sendMessage(
      chat_id=ms[0].chat.id,
      text="\n".join(res), 
      reply_to_message_id=ms[0].message_id,
      parse_mode='HTML',
  )
  if 'media_group' in context.bot_data.keys() and context.job.data in context.bot_data['media_group'].keys():
    del context.bot_data['media_group'][context.job.data]
    

_file_pattern = r"(vi_|p_|d_|au_)([a-zA-Z0-9-_]+)"
@handler("file", private_pattern=_file_pattern)
async def file(update, context, text):
    bot = context.bot
    r = re.findall(_file_pattern, text)
    # r = list(map(lambda x: list(filter(lambda y: y!='', x)), r))
    logger.info(r)

    ms = []
    async def _s():
      nonlocal ms, bot
      if len(ms) > 0:
        await bot.sendMediaGroup(chat_id=update.message.chat_id, media=ms, reply_parameters=ReplyParameters(message_id=update.message.message_id, chat_id=update.message.chat_id))
        ms = []
    
    for i in r:
      try:
        if i[0] == 'p_':
          ms.append(InputMediaPhoto(media=i[1]))
          # await bot.sendPhoto(chat_id=update.message.chat_id, photo=i[1], reply_to_message_id=update.message.message_id)
        elif i[0] == 'vi_':
          ms.append(InputMediaVideo(media=i[1]))
          # await bot.sendVideo(chat_id=update.message.chat_id, video=i[1], reply_to_message_id=update.message.message_id)
        elif i[0] == 'd_':
          await _s()
          await bot.sendDocument(chat_id=update.message.chat_id, document=i[1], reply_to_message_id=update.message.message_id)
        elif i[0] == 'au_':
          await _s()
          await bot.sendAudio(chat_id=update.message.chat_id, audio=i[1], reply_to_message_id=update.message.message_id)
      except Exception:
        logger.error(traceback.print_exc())
        await bot.sendMessage(chat_id=update.message.chat.id, text="Error, maybe non-existent", reply_to_message_id=update.message.message_id)
    await _s()
    