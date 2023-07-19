from datetime import datetime
import asyncio
import telegram

class TeleBot:
    def __init__(self, token : str, chats = None) -> None:
        self.bot = telegram.Bot(token)
        self.chats = []
        if isinstance(chats, list):
            self.chats = []
        elif isinstance(chats, int):
            self.chats.append(chats)
        self.timestamp = True

    def add_chat(self, chatid : int):
        self.chats.append(chatid)

    async def _sendmsg(self, msg : str, chatid : int):
        async with self.bot:
            await self.bot.send_message(text=msg, chat_id=chatid)

    async def _sendfile(self, msg : str, chatid : int, filelog : str, filename : str = 'logfile.txt'):
       async with self.bot:
           await self.bot.send_document(chat_id=chatid, caption=msg, document=open(filelog, 'rb'), filename=filename)

    def send_file(self,filelog,msg = None,filename : str = None):
       for chat in self.chats:
            asyncio.run(self._sendfile(msg, chat, filelog, filename))

    def message(self, msg : str):
        if self.timestamp:
            msg = f'{datetime.now()}: ' + msg
        for chat in self.chats:
            asyncio.run(self._sendmsg(msg, chat))

if __name__ == "__main__":
    bot = TeleBot("5811298447:AAF0--61uBVvKgFvMeYs76fB1QjmhaihU-Y", -822387173)
    bot.message('Hello!')
