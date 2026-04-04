# Context – Staffelstab zwischen den Agenten
#
# WARUM DIESE DATEI LEER IST:
# Ursprünglich war geplant, hier eine eigene Klasse zu schreiben die
# Zwischenergebnisse zwischen den Agenten im Arbeitsspeicher weitergibt.
#
# Das haben wir aber eleganter gelöst:
# Jeder Agent speichert sein Ergebnis als .md Datei auf der Festplatte:
#   Agent 1 → 01_lektor.md
#   Agent 2 liest 01_lektor.md → schreibt 02_inhaltsanalyse.md
#   Agent 3 liest beide → schreibt 03_vernetzung.md
#   Agent 4 liest alle drei → schreibt 04_bericht.md
#
# Das Dateisystem IST der Context – einfach, robust, und man kann
# jederzeit reinschauen was jeder Agent produziert hat.
# Keine zusätzliche Klasse nötig.
