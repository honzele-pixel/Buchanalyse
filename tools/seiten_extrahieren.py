"""
Hilfsskript: Extrahiert einen Seitenbereich aus einem PDF als Rohtext.
Verwendung: python tools/seiten_extrahieren.py <pdf_pfad> <von_seite> <bis_seite>
Beispiel:   python tools/seiten_extrahieren.py "E:\Bucher\Michael_Luders\Armageddon_im_Orient.pdf" 249 274
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz  # PyMuPDF

def seiten_extrahieren(pdf_pfad: str, von: int, bis: int) -> str:
    doc = fitz.open(pdf_pfad)
    seiten = []
    for nr in range(von - 1, min(bis, len(doc))):
        text = doc[nr].get_text()
        if text.strip():
            seiten.append(f"[Seite {nr + 1}]\n{text}")
    doc.close()
    return "\n\n".join(seiten)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Verwendung: python tools/seiten_extrahieren.py <pdf_pfad> <von_seite> <bis_seite>")
        sys.exit(1)

    pdf_pfad = sys.argv[1]
    von = int(sys.argv[2])
    bis = int(sys.argv[3])

    print(f"Extrahiere Seiten {von}–{bis} aus: {pdf_pfad}\n")
    text = seiten_extrahieren(pdf_pfad, von, bis)
    print(text)
