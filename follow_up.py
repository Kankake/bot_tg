from apscheduler.schedulers.asyncio import AsyncIOScheduler

def init_scheduler(bot):
    scheduler = AsyncIOScheduler()
    # пример: рассылка напоминаний или акций по расписанию
    # scheduler.add_job(lambda: bot.send_message(...), 'cron', day_of_week='mon-fri', hour=9)
    scheduler.start()
