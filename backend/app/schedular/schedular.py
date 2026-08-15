from apscheduler.schedulers.background import BackgroundScheduler

from app.schedular.movie_updater import update_movies


scheduler = BackgroundScheduler()

# Daily at 3am (server local time): refreshes the movie catalog from
# TMDB (new movies + updated ratings on existing ones) and rebuilds the
# content-recommendation index - see movie_updater.py for the full
# pipeline. BackgroundScheduler runs this in its own thread, so it never
# blocks the app's request-handling event loop.
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