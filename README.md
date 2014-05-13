## Choco
A simple KakaoTalk Bot written in Python.

The bot can handle multiple rooms at a time.

- Wait! If you gonna use 'Your' Kakaotalk ID(not an extra ID), using this library to run a bot or else is not recommend. (because of critical problem with PC Kakaotalk's login, and I don't know why it happens exactly)

## Adding comands
1. Create new python file to `modules` directory.
2. Add `from modules import module, Result` to top.
3. (optional) Add `#-*- coding: utf-8 -*-` to use other languages such as Korean, Japanese.
4. Write your bot script like (full code):

```python
#-*- coding: utf-8 -*-
from modules import module, Result, ResultType

@module.route('Hello')
def hello(message):
    return Result(type=ResultType.TEXT, content='Hello!')

@module.route(u'(\d+)\+(\d+)', re=True)
def sum_value(message, a, b):
    resp = '{0} + {1} = {2}'.format(a, b, int(a) + int(b))
    return Result(type=ResultType.TEXT, content=resp)

@module.route('Photo')
def hello_photo(message):
    if message.attachment:
        return Result(type=ResultType.TEXT, content=u'I recv a photo!')
```

## Installation
1. Clone this repository
2. Move to choco directory and execute this command: `./choco` (If occurs permission error execute `chmod +x choco`)
3. Edit config file(config.py)
4. Open redis and run the following command:
```
redis> hset choco_auth mail [kakaotalk email]
redis> hset choco_auth password [kakaotalk password]
redis> hset choco_auth client [client name]
redis> hset choco_auth uuid [any text]
```
5. Run choco and authorize KakaoTalk account
6. Your account session data will be save to Redis DB (HASH: choco_session, If you want to re-authorize kakao account, remove this hash key use `HDEL` command

### Run
* On **linux/unix**: `./choco`
* On **windows**: Before you run the bot, rename `choco` to `run.py` and just double-click `run.py` to start the bot, as long as you have Python installed correctly. 

## Getting help with Choco
### Install dependencies
To install dependencies, run:

```sh
pip install -r requirements.pip
```

### Support
The developer reside in [Ozinger IRC](http://ozinger.com), [Freenode IRC](http://freenode.net) and would be glad to help you. (IRC nickname is `ssut`)

If you think you have a found a bug/have a idea/suggestion, please **open a issue** here on Github.

### Requirements
Choco runs(tested) on **Python** 2.7.x. It is currently developed on **OS X** 10.9 with **Python** 2.7. (Not tested on PyPy and other envirionment)

It **requires some Python modules**. Please check **Install dependencies** section.

**Windows** users: You need to install PyCrypto manually. Please check [pykakao](https://github.com/ssut/pykakao) repository.

## License
Choco is **licensed** under the **MIT** license. The terms are as follows.

```text
The MIT License (MIT)

Copyright (c) 2014 SuHun Han

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```