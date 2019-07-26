from django.conf import settings


# Wait for container to be initialise before testing
settings.INITIALISING_THREAD.join()
