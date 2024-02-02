Troubleshooting
===============

Fehlermeldung: qt.qpa.plugin: Could not load the Qt platform plugin "xcb" in "" even though it was found.
---------------

Dazu das Programm mit der Umgebungsvariable QT_DEBUG_PLUGINS auf 1 gesetzt laufen lassen. Dann erfährt
man (hoffentlich), beim Laden welcher Bibliothek das Ganze fehlschlägt. In meinem Fall war das
`libqxcb.so`.
     
Um nun herauszufinden, woran das Laden der Bibliothek scheitert, ruft man `ldd` mit dem vollen Pfad
zur Bibliothek auf. Dann erfährt man, welche Abhängigkeiten nicht erfüllt sind. In meinem Fall fehlte
`libxcb-cursor`, was sich durch Installation des debian-Pakets `libxcb-cursor0` beheben ließ.