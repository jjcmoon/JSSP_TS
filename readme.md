# Project Algoritmen & Datastructuren (2017)

This project implements a tabu search algoritm for the
job shop scheduling problem (JSSP), as described in the
article of Dell'Amico en Trubian: 
"Applying tabu search to the job-shop scheduling problem"

Starting solutions are generated with a heurstical bidirectional
algoritm.

This was my project for the "Algoritmen & Datastructuren" 
course. Implementation details and performance results
are discussed in ``report.pdf``.

### Structure

Het project is gestructureerd in de volgende bestanden:

jobshop.py  - Hoofdklasse en representatie voor jobshop 
              probleem

bidir.py    - Implementeerd het bidir algoritme

tabu.py     - Implementeerd het tabu search algoritme

util.py     - Bevat enkele mindere relavante hulpfuncties

instance.py - Bevat functies om instanties in te lezen en 
              bidir/tabu search hierop te draaien

Verder zijn er ook twee txt bestanden met de instanties van
lawrence en yamada voorzien om op te testen.

### Usage

Het algoritme voor tabu search kan uit gevoerd worden door
in de main functie van instance.py de instructie mainTabu()
te plaasten met gewenste parameters.
Vervolgens kan men dit uitvoeren met python3:

	python3 instance.py

Voor bidir is dit analoog maar met mainBidir().

Merk op dat ik voor alle resultaten de pypy3 interpreter
gebruikt heb i.p.v. de standaard Cpython interpreter.
De resultaten zijn vanzelfsprekend identiek, maar de 
uitvoeringstijden zijn significant lager.