from apscheduler.schedulers.background import BackgroundScheduler

from app.schedular.movie_updater import update_movies


scheduler = BackgroundScheduler()

scheduler.add_job(
    update_movies,
    trigger="cron",
    hour=3,
    minute=0
)


def start_scheduler():
    scheduler.start()
    print("Scheduler Started")