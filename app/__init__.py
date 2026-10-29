import warnings

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning,
                        message="Python 3.6 is no longer supported by the Python core team")

# Suppress the warning about running celery with superuser privileges
warnings.filterwarnings("ignore", category=UserWarning,
                        message="You're running the worker with superuser privileges")

