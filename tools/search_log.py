import os

search_dir = r"C:\Users\tduy2"
exclude_dirs = ["AppData", "Downloads", "Pictures", "Videos", "Music", "Contacts", "Links", "Saved Games", "Searches"]
found = False

for root, dirs, files in os.walk(search_dir):
    # prune excluded dirs
    dirs[:] = [d for d in dirs if d not in exclude_dirs]
    for file in files:
        if file == "mistral_game_translate.py":
            print(f"FOUND: {os.path.join(root, file)}")
            found = True
            break
    if found:
        break
if not found:
    print("Not found in C:\\Users\\tduy2 (excluding AppData etc.)")
