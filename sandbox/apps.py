# apps.py
#
# Authors:
#   - Coumes Quentin <coumes.quentin@gmail.com>


from apscheduler.schedulers.background import BackgroundScheduler
from django.apps import AppConfig
from django.conf import settings

from sandbox.tasks import refresh_external_libs, remove_expired_env



class SandboxConfig(AppConfig):
    name = 'sandbox'
    
    
    def ready(self):
        """Set up scheduled task.
        
        Download/update external lib at app's startup and configure a scheduled task to update
        them.
        
        cheduled task to remove expired environment."""
        refresh_external_libs()
        
        scheduler = BackgroundScheduler(job_defaults={
            'coalesce':      True,
            'max_instances': 1,
            'misfire_grace_time': 60 * 5,
        })
        scheduler.add_job(refresh_external_libs, trigger=settings.EXTERNAL_LIBRARIES_CRON_TRIGGER)
        scheduler.add_job(remove_expired_env, 'cron', minute=30)
        scheduler.start()
