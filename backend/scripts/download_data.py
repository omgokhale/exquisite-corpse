"""
Download data.tar.gz from Google Drive and extract
Uses gdown to bypass Google's large file warnings
"""
import subprocess
import tarfile
import os
import sys

# Install gdown if not present
print("Installing gdown...")
subprocess.check_call([sys.executable, "-m", "pip", "install", "gdown", "-q"])

import gdown

url = "https://drive.google.com/uc?id=1BB3hV7ZEgPyVSMmUC4-dkchVt5SkOg_J"
output = "/data/data.tar.gz"

print("\nDownloading 2.2GB from Google Drive...")
print("This will take 5-10 minutes...")

gdown.download(url, output, quiet=False)
print("✓ Download complete!")

print("\nExtracting...")
with tarfile.open(output, "r:gz") as tar:
    tar.extractall("/data")

os.remove(output)
print("✓ Extraction complete!")

print("\nVerifying...")
raw_count = len(os.listdir("/data/data/raw_images"))
print(f"✓ Found {raw_count} raw images")
