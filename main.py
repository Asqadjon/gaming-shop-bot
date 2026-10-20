import asyncio
import logging
import sys
from loader import bot, dp
from database import init_db
from handlers import start, payment, gaming

async def main():
    init_db()

    dp.include_router(start.router)
    dp.include_router(payment.router)
    dp.include_router(gaming.router)

    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    print("Rasmiy savdo boti ishga tushdi!")
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())