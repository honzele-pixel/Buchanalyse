import asyncio
import os
from agents.lektor import lektor_analysieren
from bibliothek.index_utils import buch_in_bibliothek_registrieren

async def main():
    autor = "Helga Baumgarten"
    autor_ordner = "Helga_Baumgarten"
    titel = "Kein Frieden fuer Palaestina"
    titel_ordner = "Kein_Frieden_fuer_Palaestina"
    
    pdf_pfad = r"E:\Bucher\Helga_Baumgarten\Kein_Frieden_fuer_Palästina.pdf"
    basis_dir = os.path.join(r"E:\Claude_Projekte\Buchanalysen\analysen", autor_ordner, titel_ordner)
    lektor_pfad = os.path.join(basis_dir, "01_lektor.md")
    analyse_pfad = os.path.join(basis_dir, "02_inhaltsanalyse.md")
    
    print(f"Erstelle Verzeichnis: {basis_dir}")
    os.makedirs(basis_dir, exist_ok=True)
    
    print(f"Starte Lektor-Analyse fuer: {titel}")
    await lektor_analysieren(pdf_pfad, lektor_pfad)
    
    print("Registriere Buch in der Bibliothek...")
    buch_in_bibliothek_registrieren(
        autor=autor,
        titel=titel,
        lektor_pfad=lektor_pfad,
        analyse_pfad=analyse_pfad
    )
    print("Vorgang abgeschlossen.")

if __name__ == "__main__":
    asyncio.run(main())
