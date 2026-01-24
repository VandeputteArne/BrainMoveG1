# BrainMoveAJM: Gebruikershandleiding

> **Voor wie is deze handleiding?** Deze handleiding is bedoeld voor dagelijks gebruik van het BrainMove systeem. Voor installatie en technische setup, zie de brainmove-installatiehandleiding.
---

## Wat is BrainMove?

BrainMove is een interactief trainingssysteem met cognitieve en motorische oefeningen. Het systeem bestaat uit:

- **4 gekleurde potjes** (rood, blauw, geel, groen) met aanraaksensoren
- **Een centrale hub** (Raspberry Pi) die alles verbindt
- **Een webapp** om spellen te spelen en resultaten te bekijken

---

## Systeem Opstarten

### Stap 1: Hub Inschakelen

1. **Sluit de USB-C voeding aan** op de Raspberry Pi (de witte box).
2. Wacht **2 minuten** tot het systeem volledig is opgestart.
3. Het WiFi-netwerk `BrainMoveG1` wordt automatisch actief.

> **Tip:**Moest de webapp nog niet actief zijn na 2 minuten, controleer of de groene LED op de Raspberry Pi, deze knippert tijdens het opstarten en brandt constant wanneer het systeem klaar is.

### Stap 2: Potjes Activeren

1. **Druk op de knop** op elk potje om deze te activeren (wakker maken uit slaapstand).
2. Wacht **circa 2 seconden** - het potje start op uit slaapstand.
3. Het potje maakt een **verbindingsgeluid** wanneer deze succesvol verbindt.
4. Herhaal voor alle 4 de potjes (rood, blauw, geel, groen).

**Als een potje niet verbindt:**
- **Houd de knop 1,5-3 seconden ingedrukt** om te herstarten (je hoort een piepje bij 1,5s)
- Zet het potje dichter bij de hub
- Laad het potje op, mogelijk is de batterij leeg

> **Let op:** Potjes gaan automatisch in slaapstand na langdurig niet-gebruik om batterij te sparen. Druk op de knop om ze te wekken.

### Stap 3: Verbind met WiFi

**Optie A: Scan de QR-code (aanbevolen)**

![WiFi QR-code](qr-hotspot%20.png)

Scan deze QR-code met je telefoon camera om automatisch te verbinden.

**Optie B: Handmatig verbinden**

1. Open **WiFi-instellingen** op je telefoon, tablet of laptop
2. Verbind met netwerk: **`BrainMoveG1`**
3. Voer het wachtwoord in (vraag dit aan de beheerder)

### Stap 4: Open de Webapp

**Optie A: Scan de QR-code (aanbevolen)**

![Webapp QR-code](qr-brainmove.png)

Scan deze QR-code om direct naar de webapp te gaan.

**Optie B: Handmatig openen**

1. Open een **webbrowser** (Chrome, Safari, Firefox)
2. Ga naar: **`http://brainmove.local:3000`**

---

## De Webapp Gebruiken

De webapp begeleidt je door 3 schermen voordat je kunt beginnen met trainen.

### Scherm 1: Welkomstscherm

Bij het openen van de app zie je het welkomstscherm met:

- Het **BrainMove logo**
- De slogan **"Beweeg slimmer, denk scherper"**
- Een **pijl-knop** om verder te gaan

Tik op de pijl-knop om naar het volgende scherm te gaan.

### Scherm 2: Potjes Aanzetten

Op dit scherm zie je de 4 gekleurde potjes (rood, blauw, groen, geel) met hun verbindingsstatus.

**Wat te doen:**
1. **Druk op de fysieke knop** onder elk potje om het aan te zetten
2. Op het scherm zie je de status veranderen van **offline** naar **online**
3. Je hoort een **geluid** wanneer een potje succesvol verbindt
4. Herhaal voor alle 4 de potjes

> **Let op:** Je kunt pas verder als **alle 4 potjes verbonden** zijn. De pijl-knop is uitgeschakeld zolang er potjes offline zijn.

### Scherm 3: Waarschuwing

Dit scherm toont een belangrijke waarschuwing:

> **"Schakel het systeem altijd uit via de pagina Apparaten. Trek nooit de stekker uit het stopcontact, dit kan het systeem beschadigen."**

Tik op **"Begin met trainen"** om naar het spellenvenster te gaan.

### Navigatie

Na de onboarding kom je in het hoofdmenu. Onderaan het scherm vind je de navigatiebalk met 4 opties:

| Icoon | Naam | Functie |
|-------|------|---------|
| Spellen | **Spellen** | Overzicht van alle beschikbare spellen |
| Klok | **Geschiedenis** | Je eerdere trainingen bekijken |
| Trofee | **Ranglijst** | Top scores van alle spelers |
| Potjes | **Apparaten** | Status van de kegels bekijken |

---

## Een Spel Starten

### Stap 1: Kies een spel

In het **Spellenvenster** zie je alle 4 de spellen. Elk spel toont:
- De **naam** van het spel
- Je **hoogste score** (indien beschikbaar)
- Een **tag** met het type oefening

Tik op een spel om naar de detailpagina te gaan.

### Stap 2: Configureer het spel

Op de **detailpagina** configureer je het spel:

1. **Gebruikersnaam**: Voer je naam in (verplicht voor de ranglijst)
2. **Moeilijkheidsgraad**: Kies Makkelijk, Gemiddeld of Moeilijk
3. **Aantal rondes**: Kies 5, 10, 15 of 20 rondes
4. **Kleuren**: Selecteer welke potjes je wilt gebruiken (minimaal 2)

Er is ook een **beschrijving** van het spel en de regels.
Je ziet daar onder een **mini-ranglijst** met de top 3 spelers voor dit spel.

### Stap 3: Start het spel

Tik op **"Start het spel"** om te beginnen.

> **Let op:** De startknop is uitgeschakeld als:
> - Je geen gebruikersnaam hebt ingevuld
> - Er minder dan 2 kleuren geselecteerd zijn
> - Er minder dan 2 potjes online zijn

### Na het Spel

Na afloop van het spel zie je:

1. **Proficiat-scherm**: Felicitatie met confetti!
2. Tik op **"Bekijk je resultaten"** voor gedetailleerde statistieken

---

## De Spellen

BrainMove bevat 4 verschillende spellen, elk gericht op andere vaardigheden.

### Spel 1: Kleur Sprint (Reactiesnelheid)

**Doel:** Tik zo snel mogelijk op het potje met de getoonde kleur.

**Hoe werkt het:**
1. Een kleur verschijnt op het scherm
2. Tik op het potje met die kleur
3. Je reactietijd wordt gemeten
4. Na de laatste ronde zie je je resultaten

**Score:** Gemiddelde reactietijd (lager = beter)

---

### Spel 2: Geheugen (Onthouden)

**Doel:** Onthoud en herhaal steeds langere kleurenreeksen.

**Hoe werkt het:**
1. Het systeem toont een reeks kleuren op het scherm
2. Wacht tot alle kleuren zijn getoond
3. Tik de potjes aan **in dezelfde volgorde**
4. Elke ronde wordt de reeks 1 kleur langer
5. Bij een fout eindigt het spel

**Score:** Hoogste niveau bereikt + gemiddelde reactietijd

---

### Spel 3: Nummer Match (Cognitief)

**Doel:** Koppel nummers aan kleuren en tik het juiste potje aan.

**Hoe werkt het:**
1. Je ziet een nummer-kleur mapping (bijv. 1=Rood, 2=Blauw, etc.)
2. Een nummer verschijnt op het scherm
3. Tik op het potje met de bijbehorende kleur
4. De mapping kan veranderen, blijf opletten!

**Score:** Gemiddelde reactietijd + nauwkeurigheid

---

### Spel 4: Vallende Kleuren (Precisie)

**Doel:** Tik op de kleur voordat deze "valt" naar de onderkant.

**Hoe werkt het:**
1. Een kleur verschijnt bovenaan het scherm en "valt" naar beneden
2. Tik op het juiste potje voordat de kleur de onderkant bereikt
3. Tik je op het verkeerde potje? Game over!
4. Mis je de kleur? Game over!

**Score:** Aantal succesvol gevangen kleuren

---

## Moeilijkheidsgraden

Elk spel heeft 3 moeilijkheidsgraden:

| Niveau | Beschrijving |
|--------|--------------|
| **Makkelijk** | Langzame snelheid, meer tijd om te reageren |
| **Gemiddeld** | Standaard snelheid, normale uitdaging |
| **Moeilijk** | Snelle snelheid, minimale reactietijd |

> **Tip:** Begin met "Makkelijk" om het spel te leren kennen, en verhoog de moeilijkheid naarmate je verbetert.

---

## Resultaten Bekijken

### Na Elk Spel

Na afloop van een spel zie je het **Proficiat-scherm** met confetti. Tik op **"Bekijk je resultaten"** om je statistieken te zien:

- **Gemiddelde reactietijd** (in seconden)
- **Aantal correcte/foute antwoorden**
- **Je ranking** vergeleken met andere spelers
- **Grafiek** van je prestaties per ronde

### Geschiedenis

Bekijk al je eerdere trainingen:

1. Tik op **"Geschiedenis"** in de navigatiebalk
2. **Filter** op spel, datum of spelersnaam
3. Tik op een training voor gedetailleerde statistieken
4. **Exporteer** naar Excel voor verdere analyse

### Ranglijst

Vergelijk je scores met andere spelers:

1. Tik op **"Ranglijst"** in de navigatiebalk
2. Selecteer een **spel**
3. Filter op **moeilijkheidsgraad**
4. Bekijk de **Top 10** spelers

---

## Apparaten Beheren

### Status Controleren

Tik op **"Apparaten"** in de navigatiebalk om te zien:

- **Online/Offline status** van elk potje
- **Batterijpercentage** per potje
- **Laatst gezien** tijdstempel

### Status Indicatoren

| Indicator | Betekenis |
|-----------|-----------|
| Groen | Potje is online en klaar |
| Rood | Potje is offline of niet verbonden |
| Batterij-icoon | Toont het batterijpercentage |

### Potjes Uitschakelen

Om alle potjes uit te schakelen (bijv. aan het einde van de dag):

1. Ga naar **"Apparaten"**
2. Tik op **"Alles uitschakelen"**
3. Voer het **beheerderswachtwoord** in
4. Alle potjes gaan in slaapstand

---

## Problemen Oplossen

### Potje Verbindt Niet

**Symptoom:** Potje maakt geen verbindingsgeluid, blijft offline in de app.

**Oplossingen:**
1. **Houd de knop 1,5-3 seconden ingedrukt** om te herstarten (je hoort een piepje bij 1,5s, laat dan los)
2. Controleer of het potje **opgeladen** is (laad eventueel op)
3. Breng het potje **dichter bij de hub**
4. Wacht 30 seconden en probeer opnieuw

### Lage Batterij Waarschuwing

**Symptoom:** Pop-up melding over lage batterij.

**Oplossingen:**
1. **Laad het potje op** met de USB-kabel
2. Bij batterij kleiner of gelijk aan 5% gaat het potje automatisch in slaapstand
3. Een volle oplading duurt ongeveer 2 uur

### Webapp Laadt Niet

**Symptoom:** Pagina laadt niet of geeft foutmelding.

**Oplossingen:**
1. Controleer of je verbonden bent met **WiFi "BrainMoveG1"**
2. Ververs de pagina (pull-to-refresh of F5)
3. Probeer het **IP-adres** direct: `http://brainmove.local:3000`
4. Wis de browser cache en probeer opnieuw
5. Controleer of de hub is ingeschakeld

### Spel Reageert Niet op Aanraking

**Symptoom:** Je tikt op een potje maar er gebeurt niets.

**Oplossingen:**
1. Controleer of het potje **online** is in het apparatenmenu
2. Tik op het **midden** van het potje (waar de sensor zit)
3. Houd je hand niet te lang boven het potje (kort tikken)
4. Controleer of het spel daadwerkelijk is **gestart**
5. Herstart het potje door de knop **1,5-3 seconden ingedrukt** te houden

### Hub Start Niet Op

**Symptoom:** Geen WiFi-netwerk zichtbaar na 5 minuten.

**Oplossingen:**
1. Controleer of de **voeding** correct is aangesloten
2. Controleer of het **LED-lampje** brandt op de Raspberry Pi
3. Houd het witte knopje ingedrukt en wacht tot het lampje op de Raspberry Pi rood wordt. Trek de stekker eruit, en sluit opnieuw aan
4. Neem contact op met de technische beheerder

---

## Knopbediening Potjes

Elk potje heeft één knop met verschillende functies afhankelijk van hoe lang je drukt:

### Vanuit Slaapstand
| Actie | Resultaat |
|-------|-----------|
| Kort drukken | Potje wordt wakker en verbindt |

> **Let op:** Na het indrukken duurt het circa **2 seconden** voordat je een geluid hoort. Dit is normaal - het potje start op uit slaapstand.

### Wanneer Actief (verbonden of verbindend)
| Indrukduur | Resultaat | Geluidssignaal |
|------------|-----------|----------------|
| < 1,5 seconden | Slaapstand | Dalende toon (hoog → laag) |
| 1,5 - 3 seconden | Herstarten | Piepje bij 1,5s, dan stijgende toon |
| > 3 seconden | Geannuleerd | Lage toon |

> **Tip:** Bij het herstarten hoor je een kort piepje wanneer je de 1,5 seconden bereikt. Laat dan de knop los om te herstarten. Houd je langer dan 3 seconden vast, dan wordt de actie geannuleerd.

---

## Potjes Opladen

### Oplaadproces

1. Sluit de **USB-kabel** aan op het potje
2. Sluit de andere kant aan op een **USB-oplader** of computer
3. Het **LED-lampje** op het potje geeft de laadstatus aan:
   - **Rood**: Bezig met opladen
   - **Blauw**: Volledig opgeladen
4. Opladen duurt ongeveer **2 uur** voor een volle batterij

### Batterijduur

- Een volle batterij gaat **ongeveer 10 uur** mee bij normaal gebruik
- In slaapstand gaat de batterij **weken** mee
- Bij inactiviteit gaan potjes automatisch in slaapstand

> **Tip:** Laad de potjes 's avonds op zodat ze de volgende dag klaar zijn voor gebruik.

---

## Systeem Afsluiten

### Einde van de Sessie

1. Ga naar **"Apparaten"** in de app
2. Tik op **"Alles uitschakelen"** om potjes in slaapstand te zetten
3. Ontkoppel de **voeding** van de Raspberry Pi

---

## Tips voor Optimaal Gebruik

### Voor de Training

- Controleer of alle potjes **online** zijn
- Zorg dat potjes **voldoende opgeladen** zijn (> 20%)
- Plaats potjes op een **stabiele ondergrond**
- Zorg voor **voldoende ruimte** rond de potjes

### Tijdens de Training

- Beweeg **duidelijk en tussen de 10 - 100cm** boven de potjes
- Kijk naar het scherm voor de **volgende instructie**
- Neem **pauze** indien nodig
- Begin met **makkelijk** en verhoog geleidelijk

### Na de Training

- Bekijk je **resultaten** en voortgang
- Vergelijk met de **ranglijst**
- **Exporteer** data indien nodig
- Laad potjes op indien nodig

---

## Veiligheidsinstructies

- Gebruik het systeem op een **vlakke, stabiele ondergrond**
- Zorg voor **voldoende bewegingsruimte**
- Stop direct bij **duizeligheid of ongemak**
- Laat kinderen alleen onder **toezicht** spelen
- Houd de potjes **droog** (niet geschikt voor buiten als het vochtig is)
- Gebruik alleen de **meegeleverde voeding** voor de hub

---

## Snelle Referentie

| Actie | Hoe |
|-------|-----|
| Systeem starten | USB-C voeding aansluiten op hub |
| Potje wakker maken | Druk kort op de knop (vanuit slaapstand) |
| Potje in slaapstand | Druk kort op de knop (< 1,5 sec) |
| Potje herstarten | Houd knop 1,5-3 sec ingedrukt (piepje = loslaten) |
| Knopactie annuleren | Houd knop > 3 sec ingedrukt |
| Verbinden met WiFi | Netwerk "BrainMoveG1" |
| Webapp openen | `http://brainmove.local:3000` |
| Potjes uitschakelen | Apparaten → Alles uitschakelen |
| Potje opladen | USB-kabel aansluiten |

---

## Contact & Ondersteuning

Bij technische problemen of vragen, neem contact op met:

- **Email:** arne.vandeputte@student.howest.be, michiel.gekiere@student.howest.be, Jonathan.matthys@student.howest.be
- **GitHub:** [BrainMoveG1 Repository](https://github.com/VandeputteArne/BrainMoveG1)

---