Praktische Scan-Tips
====================

Um Textdokumente vernünftig und effektiv zu digitalisieren,
sollte man zumindest über ein Grundverständnis davon haben,
was beim Scannen passiert.

Auflösung
---------

Als erstes wird ein Raster über die Vorlage gelegt, so dass
die Vorlage in eine gewisse Anzahl kleiner Quadrate zerlegt
wird (in der Theorie könnten das auch Rechtecke sein; ich
kenne aber keinen Scanner der das unterstützt und der
Scan Converter würde solche Dateien auch als fehlerhaft
zurückweisen).

Aus jedem dieser kleinen Quadrate wird dann ein Rasterpunkt
des Digitalisats. Je mehr Rasterpunkte erzeugt werden, umso
näher am Original wird dann das Digitalisat ausfallen. Die
Anzahl der Rasterpunkte ist deshalb ein Maß für die Qualität
eines Scans. Dieses Maß wird in dpi angegeben - das steht
für dots per inch, also Rasterpunkte pro Zoll. Dieses Maß
wird auch *Auflösung* des Scans genannt.
Deshalb ist der erste Parameter, den man beim Scannen festlegen
muß, die Auflösung oder Anzahl der dots per inch,
da einem die meisten Scanner
hier die Wahl lassen.

Wie gesagt, je höher die Auflösung ist, um so besser ist der
Scan. Warum also nicht die höchste Auflösung wählen, die der Scanner anbietet?
Ganz einfach: Je mehr dpi man wählt, umso größer wird die
Datei, die wir erzeugen. Es kostet also Speicherplatz (und
Rechenzeit), wenn wir hier mit hohen Werten arbeiten. Und
da Papier zweidimensional ist, steigt die Dateigröße nicht einfach
linear mit den dpi, sondern quadratisch: Wenn wir ein Quadrat
mit einem Zoll Kantenlänge mir 100 dpi scannen, dann bekommen
wir 100 x 100 = 10.000 Rasterpunkte. Wenn wir die Auflösung
aber auf 200 dpi verdoppeln, haben wir auf einmal
200 x 200 = 40.000 Rasterpunkte. Während sich die Auflösung
nur verdoppelt hat, hat sich die Datenmenge vervierfacht.

Als Standard hat sich eine Auflösung von 300 dpi
etabliert und das ist es auch, was der Scan Konverter als
Ziel-Auflösung produziert. Wenn die Scans also mehr
als 300 dpi haben, wird die Auflösung einfach heruntergerechnet.
Es bringt also ganz prinzipiell nichts, mit mehr als 300 dpi
zu scannen.

Farbtiefe
---------

Der zweite Parameter (der ebenfalls entscheidende Auswirkungen
auf das Aussehen und die Dateigröße von Scans hat), ist die Farbtiefe.
Das klingt etwas nerdig, gemeint ist damit, dass man entweder
farbig, grau oder schwarz-weiß scannt. Warum spricht man
hier von Farbtiefe?

Wir erinnern uns an das Raster, das der Scanner über die
Vorlage legt und die Quadrate, die er dabei erzeugt. Für jedes
dieser Quadrate wird nun eine Zahl erzeugt, die die Farbinformation
für das Quadrat festlegt.