"""
Hilfsskript: Extrahiert die letzten N Seiten eines PDFs als Rohtext.
Wird für die lückenlose Quellenextraktion in Schritt 5 benötigt.
"""

import sys
import os
import fitz  # PyMuPDF

def extract_last_pages(pdf_path, num_pages=50):
    if not os.path.exists(pdf_path):
        return f"Fehler: Datei nicht gefunden: {pdf_path}"
    
    try:
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        
        start_page = max(0, total_pages - num_pages)
        text_parts = []
        
        for i in range(start_page, total_pages):
            page = doc.load_page(i)
            text_parts.append(f"[SEITE {i+1}]\n" + page.get_text())
        
        doc.close()
        return "\n\n".join(text_parts)
    except Exception as e:
        return f"Fehler bei der Extraktion: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Verwendung: python extract_last_pages.py <pdf_pfad> [anzahl_seiten]")
        sys.exit(1)
    
    path = sys.argv[1]
    pages = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    
    print(extract_last_pages(path, pages))
