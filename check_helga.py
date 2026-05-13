import os
from main import buecher_scannen
b = buecher_scannen()
for i, x in enumerate(b):
    if "Helga" in x["autor"]:
        print(f"{i+1}: {x['titel']} ({os.path.basename(x['pdf_pfad'])})")
