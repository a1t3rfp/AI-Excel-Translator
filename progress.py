import json
import os

FILE = "progress.json"


def save_progress(row):

    with open(FILE, "w") as f:
        json.dump({"row": row}, f)


def load_progress():

    if not os.path.exists(FILE):
        return 2

    with open(FILE, "r") as f:
        data = json.load(f)

    return data["row"]


def clear_progress():

    if os.path.exists(FILE):
        os.remove(FILE)