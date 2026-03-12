from .base import *

DEBUG = False
DATABASES = {
    'default': dj_database_url.config(default=os.environ.get('DATABASE_URL'))
}
ALLOWED_HOSTS = ['dutyplannerfrontend-staging.up.railway.app', 'https://dutyplannerfrontend-production.up.railway.app/']