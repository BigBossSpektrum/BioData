from waitress import serve
import os
import sys

sys.path.append(os.path.dirname(__file__))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inverligol.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

serve(application, host='0.0.0.0', port=8000)