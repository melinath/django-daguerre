DATABASES = {
	"default": {
		"NAME": ":memory:",
		"ENGINE": "django.db.backends.sqlite3",
	}
}

INSTALLED_APPS = [
    'daguerre',
]

SECRET_KEY = "NOT SECRET"