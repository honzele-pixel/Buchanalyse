# Orchestrator – Koordiniert den Ablauf aller 4 Agenten
#
# WARUM DIESE DATEI LEER IST:
# Ursprünglich war geplant, hier die Steuerungslogik zu schreiben
# die alle 4 Agenten nacheinander aufruft.
#
# Das haben wir aber direkt in main.py umgesetzt – noch besser,
# weil main.py gleichzeitig das Benutzermenü enthält:
#
#   main.py
#     → zeigt Buchauswahl-Menü
#     → ruft Agent 1 (Lektor) auf
#     → ruft Agent 2 (Inhaltsanalyst) auf
#     → ruft Agent 3 (Vernetzer) auf
#     → ruft Agent 4 (Berichterstatter) auf
#
# main.py IST der Orchestrator – alles an einem Ort, kein
# zusätzlicher Umweg über diese Datei nötig.
