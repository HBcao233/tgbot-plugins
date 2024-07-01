# 正常的 Hello World
print('Hello World')

# 神金的 Hello World
@lambda _, __=print:lambda *___,**____:_(__(*___,**____))
def print(*_,**__):
  return print
print('Hello', end=' ')('World')
