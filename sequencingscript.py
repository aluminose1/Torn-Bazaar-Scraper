import subprocess

# Run apimultiscrape.py
print("Running apimultiscrape.py...")
subprocess.run(['python', 'apimultiscrape.py'])

# Once the first script finishes, run the filtering script
print("Running the filter script...")
subprocess.run(['python', 'inactivityfilter.py'])