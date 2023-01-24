Praktische Scan-Tips
====================


Die Kurzfassung
---------------

Für das Scannen von Textdokumenten solltet ihr euch
an folgende drei Regeln halten:

* Wählt als Auflösung 300 dpi

* Wählt je nach Vorlage farbig oder Graustufen, niemals
  "Schwarz/Weiß" oder Strichzeichung.
  
* Speichert als tif- oder png-Datei, niemals als jpg

Wenn ihr einfach unsere Autorität akzeptiert und euch
an diese Anweisungen haltet, müsst ihr nicht weiterlesen.
Im folgenden erläutern wir, das es damit auf sich hat.

Auflösung
---------

Wir haben oben gesagt, dass ihr eine Auflösung von
300 dpi wählen sollt. Aber was heißt das genau?
dpi ist eine Abkürzung für dots per inch, also Punkte
pro Zoll. Der Scanner legt über die Vorlage ein
Raster und teilt sie in kleine Karos ein (in der
Theorie könnten das auch Rechtecke sein; ich
kenne aber keinen Scanner der das unterstützt und der
Scan Converter würde solche Dateien auch als fehlerhaft
zurückweisen). Dann wird
für jedes Karo ein Wert ermittelt, der die Farbe
des Karos beschreibt. Wenn das Raster grob
gewählt wird, wird das Digitalisat sehr pixelig,
je feiner es ist, umso näher kommt es dem Original.

Die Anzahl der Rasterpunkte ist deshalb ein Maß für die Qualität
eines Scans. Dieses Maß wird in dpi angegeben.
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
mit einem Zoll Kantenlänge mit 100 dpi scannen, dann bekommen
wir 100 x 100 = 10.000 Rasterpunkte. Wenn wir die Auflösung
aber auf 200 dpi verdoppeln, haben wir auf einmal
200 x 200 = 40.000 Rasterpunkte. Während sich die Auflösung
nur verdoppelt hat, hat sich die Datenmenge vervierfacht.

Als Standard hat sich eine Auflösung von 300 dpi
etabliert und das ist es auch, was der Scan Konverter als
Ziel-Auflösung produziert. Beim Scan Konverter 1 konnte man
das auswählen, für den neuen haben wir das fest eingebaut.
Sollte sich tatsächlich ein Bedarf für andere Auflösungen
herausstellen, könnte das als Sonderoption eingebaut werden.

Das heißt also, egal mit welcher Auflösung gescannt wird,
die Ausgabe erfolgt immer mit einer Auflösung von 300 dpi.
Wenn der Scan mehr hat, wird das einfach heruntergerechnet - es
bringt also nicht wirklich etwas, mit mehr als 300 dpi zu scannen.
Wenn mit weniger gescannt, rechnet das Programm die
Auflösung hoch - das ist aber nicht wirklich empfehlenswert.

Farbtiefe
---------

Der zweite Parameter (der ebenfalls entscheidende Auswirkungen
auf das Aussehen und die Dateigröße von Scans hat), ist die Farbtiefe.
Das klingt etwas nerdig, ist aber auch nicht weiter
kompliziert. Wir haben oben erklärt, dass den einzelnen Rasterpunkten
jeweils ein Farbwert zugeordnet wird. Wenn wir schwarz/weiß
scannen, bekommt der Rasterpunkt entweder 0 oder 1 zugewiesen, je
nachdem, ob er eher als Schwarz oder eher als Weiß angesehen wird.
Man spricht hier von einer Farbtiefe von 1 Bit, weil es nur ein
Bit (1 Ziffer im Binärsystem) braucht, um die Information abzuspeichern.

Wenn man Graustufen scannt, dann wird eine Skala von 0 bis
255 angelegt, wobei 0 für ganz Schwarz und 255 für reines Weiß
steht und die Werte dazwischen für mehr oder minder dunkles
Grau. Warum aber diese komisch krumme Zahl 255? Für Computer,
die nicht im Dezimalsystem, sondern im Binärsystem rechnen,
ist 255 keine krumme Zahl, denn im Binärsystem sieht
255 folgendermaßen aus: 11111111. 255 ist der höchste Wert,
den man mit 8 Ziffern im Binärsystem darstellen kann. Die
Farbtiefe bei Graustufen ist deshalb 8 Bit. Um ein Graustufen-Bild
abzuspeichern braucht man also 8 mal mehr Speicherplatz als für
ein Schwarz-Weiß-Bild.

Nochmal mehr wird es, wenn man farbig scannt. Farbe stellt
der Scanner als Mischung von drei Farbkanälen, Rot, Grün und Blau
dar. Das Verfahren ist das selbe wie bei den Graustufen. Für
jeden dieser Farbkanäle wird ein Wert von 0 bis 255 ermittelt,
man braucht also 3 mal 8 Bit, um einen Farbwert abzuspeichern.
Die Farbtiefe bei farbigen Scans ist also 3 x 8 = 24 Bit. Das
heißt dann auch, dass ein Farbscan bei gleicher Auflösung 24
mal so groß ist wie ein Schwarz-Weiß-Scan.

Farbig scannen sollte man also nur, wenn man wirklich Farbe
benötigt, sonst kann man gleich Graustufen scannen und die
Datenmenge um ein Drittel reduzieren.

Warum aber sollte man nicht gleich Schwarz-Weiß scannen und
die Datenmenge noch mal um den Faktor 8 reduzieren, vor allem
wenn man es mit Text zu tun hat - was ja in der Theorie
tatsächlich schwarz auf weiß ist? Tatsächlich wollen wir
mit den Scan Konverter am Ende schwarz-weiße pdf-Dateien
produzieren. Aber die Umwandlung, die die Scanner-Hardware
vornimmt, ist miserabel. Der Scan Konverter stellt eine
ganze Reihe unterschiedlicher Algorithmen zur Verfügung,
um den Scan letztlich in ein schwarz-weißes pdf zu verwandeln.
Dazu ist aber das mehr an Information notwendig, das eine
Farbtiefe von 8 oder 24 bit liefert.

Speicherformat und Kompression
------------------------------




Wir erinnern uns an das Raster, das der Scanner über die
Vorlage legt und die Quadrate, die er dabei erzeugt. Für jedes
dieser Quadrate wird nun eine Zahl erzeugt, die die Farbinformation
für das Quadrat festlegt.