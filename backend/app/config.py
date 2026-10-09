import os
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/calibration")
TARGET_COVERAGE = float(os.getenv("TARGET_COVERAGE", "0.9"))