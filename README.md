<div align="center">
<h1>NFTgram bot</h1>

[![Telegram](https://img.shields.io/badge/Telegram-nftgram_bot-blue?logo=telegram)](https://t.me/NFTgram_bot)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
</div>

---


[@NFTgram\_bot](https://t.me/NFTgram_bot) - это чат-бот маркетплейса NFT криптоарта.


## Requirements
* [Python](https://www.python.org/downloads) >= 3.8
* [Redis](https://redis.io/download)
* [aioredis](https://github.com/aio-libs/aioredis-py) - asyncio Redis client library.
* [Emoji](https://github.com/carpedm20/emoji) - emoji for Python


## Installation and launch
### Manual
1. Clone the repository:
```bash
git clone https://github.com/nftgram/NFTgram_bot
cd NFTgram_bot
```
2. Install Python version no less than 3.8 with [pip](https://pip.pypa.io/en/stable/installing/).
3. Install requirements:
```bash
pip install -r requirements.txt
```
4. Compile translations:
```bash
pybabel compile -d locales/ -D bot
```
5. Create environment file from example:
```bash
cp .env.example .env
```
6. Personalize settings by modifying ```.env``` with your preferable text editor. Remove ```INTERNAL_HOST``` and ```DATABASE_HOST``` if you want bot and database running on localhost.
7. Create a new Telegram bot by talking to [@BotFather](https://t.me/BotFather) and get its API token.
8. Install and start [Redis server](https://redis.io/topics/quickstart).
9. Set environment variables:
```bash
export $(grep -v '^#' .env | xargs)
```
10. Launch NFTgram_bot:
```bash
python -m nftgram
```
