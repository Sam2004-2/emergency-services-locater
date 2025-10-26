import multiprocessing
import os


bind = "0.0.0.0:8000"
workers = int(os.getenv("WORKERS", multiprocessing.cpu_count() * 2 + 1))
timeout = int(os.getenv("TIMEOUT", "60"))
accesslog = "-"
errorlog = "-"
