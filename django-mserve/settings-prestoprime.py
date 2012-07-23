# Do PrestoPRIME setup
PRESTOPRIME = True

if PRESTOPRIME:
    CELERY_IMPORTS += ("prestoprime.tasks",)
    INSTALLED_APPS += ('prestoprime',)

