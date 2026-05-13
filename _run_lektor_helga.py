
import asyncio
import os
from agents.lektor import lektor_analysieren

async def main():
    pdf_pfad = r"E:\Bucher\Helga_Baumgarten\Völkermord_in_Gaza.pdf"
    ausgabe_pfad = r"E:\Claude_Projekte\Buchanalysen\analysen\Helga_Baumgarten\Völkermord_in_Gaza\01_lektor.md"
    
    # Sicherstellen, dass der Ordner existiert
    os.makedirs(os.path.dirname(ausgabe_pfad), exist_ok=True)
    
    await lektor_analysieren(pdf_pfad, ausgabe_pfad)

if __name__ == "__main__":
    asyncio.run(main())
