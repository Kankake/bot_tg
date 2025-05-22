from apscheduler.schedulers.asyncio import AsyncIOScheduler

def init_scheduler(bot):
    scheduler = AsyncIOScheduler()
    # add jobs here
    scheduler.start()
