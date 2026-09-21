import subprocess
import sys

# Add any new Python dependencies here as the project grows.
PACKAGES = [
    "pandas",
    "feedparser",
    "trafilatura",
    "tqdm",
    "selenium",
    "webdriver-manager",
    "transformers",
    "torch",
    "anthropic",
]

subprocess.check_call([
    sys.executable,
    "-m",
    "pip",
    "install",
    *PACKAGES
])

print("\nAll dependencies installed successfully!")