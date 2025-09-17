# MCP-Server für Luftqualitätsdaten

## 1. Einführung und Ziele

Dieser MCP-Server richtet sich an alle, die unkompliziert und in natürlicher Sprache Luftqualitätsdaten abrufen wollen. Dabei sind Synergieeffekte aus dem Zusammenspiel von LLM, MCP und ggf. anderen MCPs besonders interessant: So können beispielsweise Schadstofftendenzen an verschiedenen Orten statistisch aufbereitet und mit anderen Datenquellen verbunden und korreliert werden (Beispielprompt: "Wie hat sich die Bleibelastung im Feinstaub in der Nähe von Ohlauerstr. 43 in Berlin über die letzten 10 Jahre entwickelt? Erstelle eine Graphik"). Im Gegensatz zu Agenten nutzt es im Normalfall wesentlich weniger Token.

## 2. Einschränkungen 

Ggf. setzen sich Limitierungen der Messstationen bzw. der API bis zu den Ausgaben des MCPs fort: So werden bestimmte Daten wie Blei im Feinstaub nicht stündlich, sondern seltener gemessen.

## 3. API-Abhängigkeit

* Dieser Server verlässt sich auf die Specs der Luftdaten-API (https://www.umweltbundesamt.de/daten/luft/luftdaten/doc). Um mögliche API-Änderungen zu erkennen, empfiehlt es sich, das LLM vor dem Einsatz des MCPs dazu zu prompten, Plausibilitätschecks der Outputs durchzuführen.
* Die Daten werden bereitgestellt vom Umweltbundesamt.
* Datenlizenz Deutschland – Umweltbundesamt – Version 2.0 (Lizenztext:  www.govdata.de/dl-de/by-2-0)

## 4. Anwendungsfälle

Die Idee für das MCP ist es, das "Spielen" mit den Luftverschmutzungsdaten des Umweltbundesamtes ohne technischen Aufwand zu ermöglichen. Denkbar ist ein Einsatz im Alltag (Beispielprompts: "Wo in der Nähe von Ohlauerstr. 43 in Berlin ist die Luftqualität gut?", "War ich in der Ohlauerstr. 43 in Berlin diese Woche erhöhten Gesundheitsrisiken durch Feinstaub ausgesetzt?")

## 5. Toolbeschreibungen

* get_components_annually: Holt die Jahresmittelwerte für einen bestimmten Schadstoff für alle Messstationen, die ihn messen, für ein gegebenes Jahr.
* get_stations_scope_and_span_for_component: Holt für eine bestimmte Schadstoffkomponente die IDs der Messstationen, die sie messen, die Häufigkeit und die Zeitspanne der Messungen.
* get_metadata_now: Holt alle Metadaten für den jetzigen Zeitpunkt wie mögliche Komponenten, alle Messstationen u. Ä. Hohe Tokenzahl, sollte deshalb nur verwendet werden, wenn alle anderen Tools nicht anwendbar sind.
* get_all_stations_nearby_today: Holt alle Messtationen, die in der Nähe einer angegebenen Postleitzahl sind, und nutzt zum Filtern von nahegelegenen Messstationen die erste Ziffer der Postleitzahl. 
* get_quality_for_station_now: Holt die aktuelle Luftqualität für eine bestimmte Messstation.
* get_quality_for_station: Holt die Luftqualität für einen anzugebenden Zeitraum für eine bestimmte Messstation.
* get_components_by_number: Gibt alle laut Dokumentation gemessenen Komponenten und deren Kennziffer zurück. 

## 6. Mögliche Verfeinerungen in der Zukunft

* Kombination mit anderen Daten-MCPs: Denkbar wären beispielsweise andere Umweltdaten des Umweltbundesamts, um Korrelationen zu beobachten (Beispielprompt: "Wie hat sich die Konzentration von Blei im Feinstaub nahe dem Müggelsee verändert? Korreliert das mit der Belastung von Fischen im Müggelsee?")
* Suche nach Stationen in der Umgebung mithilfe von Koordinaten anstatt Postleitzahlen durch API-Call zu Kartenservice, der die Koordinaten zu eingegebenen Adressen holt
* Luftqualitätsvorhersage

## 7. Architektonische Entscheidungen

* Parameterinputs durch das LLM werden auf Plausibilität überprüft, damit das LLM ggf. einen neuen Call mit besseren Inputs starten kann
* API-Outputs werden nicht validiert, sondern können ggf. vom LLM auf Plausibilität überprüft werden
* Tool-Beschreibungen sind auf Deutsch, da es sich um Luftdaten aus dem deutschsprachigen Raum handelt und deshalb mit deutschsprachigen LLM-Fragen zu rechnen ist