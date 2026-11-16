from apscheduler.schedulers.background import BackgroundScheduler

from app.schedular.movie_updater import update_movies


scheduler = BackgroundScheduler()

# This job is opt-in at application startup. On free/sleeping hosts the API
# process may be stopped for long periods, so an in-process scheduler cannot
# guarantee execution and should be disabled there.
scheduler.add_job(
    update_movies,
    trigger="cron",
    hour=3,
    minute=0,
    id="daily_movie_update",
    replace_existing=True,
)


def start_scheduler():
    if not scheduler.running:
        scheduler.start()
        print("Scheduler started - movies auto-update daily at 3am.")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
