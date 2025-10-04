import os
import json
import subprocess

# Directories to scan for executables
bin_dirs = ["/bin", "/usr/bin", "/usr/local/bin", "/sbin", "/usr/sbin"]

# Set to collect unique command names
commands = set()

# Collect all unique commands from bin directories
for directory in bin_dirs:
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            full_path = os.path.join(directory, filename)
            if os.access(full_path, os.X_OK) and not os.path.isdir(full_path):
                commands.add(filename)

print(f"Discovered {len(commands)} commands. Fetching descriptions...")

entries = []

for cmd in sorted(commands):
    try:
        # Use 'man -f' or 'whatis' to fetch summary (quiet fallback)
        result = subprocess.run(["whatis", cmd], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        output = result.stdout.strip()

        if "nothing appropriate" in output.lower() or output == "":
            continue  # skip if no entry

        # Extract short description from whatis format: "ls (1) - list directory contents"
        desc = output.split(" - ", 1)
        if len(desc) == 2:
            entry = {
                "title": cmd,
                "description": desc[1].strip(),
                "example": f"{cmd} --help",
                "tags": []
            }
            entries.append(entry)
    except Exception as e:
        print(f"Error processing {cmd}: {e}")

# Save to JSON
with open("auto_dictionary.json", "w") as f:
    json.dump(entries, f, indent=2)

print(f"✅ Generated {len(entries)} entries in auto_dictionary.json")
