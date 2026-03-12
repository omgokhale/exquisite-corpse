"""
Download data.tar.gz from Google Drive and extract
"""
import urllib.request
import tarfile
import os

url = "https://drive.google.com/uc?export=download&id=1BB3hV7ZEgPyVSMmUC4-dkchVt5SkOg_J"
output = "/data/data.tar.gz"

print("Downloading 2.2GB from Google Drive...")
print("This will take 5-10 minutes...")

urllib.request.urlretrieve(url, output)
print("✓ Download complete!")

print("\nExtracting...")
with tarfile.open(output, "r:gz") as tar:
    tar.extractall("/data", filter='data')

os.remove(output)
print("✓ Extraction complete!")

print("\nVerifying...")
raw_count = len(os.listdir("/data/data/raw_images"))
print(f"✓ Found {raw_count} raw images")
