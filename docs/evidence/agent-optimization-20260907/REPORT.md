# Oteryn — raport programu optymalizacji instrukcji i weryfikacji

Data: 2026-09-07. Rodzic: [META #142](https://github.com/Oteryn/Oteryn/issues/142).

**Status: PROGRAMME_NOT_COMPLETE — pozostałość pod aktywną zewnętrzną własnością.** Wszystkie niezależne prace dostawców tego wykonania zostały zintegrowane i odczytane na protected main; szeroka akceptacja Game pozostaje wycofana. Adopcja została scalona we wszystkich trzech repozytoriach dostawców, lecz końcowy przegląd wykazał nadal aktywne sprzeczne kontrolery w Game i Platform. Ich równoległe, aktywnie modyfikowane gałęzie R5 pozostają pod odrębną własnością. Nie zamykamy #142 ani nie nazywamy tego pełnym ukończeniem W1–W7.

## Wynik według zakresu

| Zakres | Wynik | Pozostałość |
|---|---|---|
| W1 Game | #373 zintegrowany; 47 szablonów, pin, konsument i CI; 16/16 ograniczonych prób | Szerokie ROLLOUT_QUALIFIED wycofane; P1 w osiągalnych kontrolerach, właściciel #379/#367 |
| W2 Platform | #1304 zintegrowany; 10 aktywnych szablonów i centralny uwierzytelniony konsument | Cykl życia i cleanup naprawione przez #1306/#1307/#1308; szersze sprzeczne kontrolery posiada #1303/#1302 |
| W3A Atlas | #345/#347/#348 zintegrowane w allowliście maintenance | Dokumenty aktualnej ochrony i rodzina E2E pod cudzym #346 |
| W3B Atlas | NOT_APPLICABLE dla aktualnego zakresu | Brak istniejącej konfiguracji lub nakazu jej dodania; opcjonalne nowe ścieżki poza freeze |
| W4 | META, 47 promptów Game, 10 Platform, 6 Atlas i część historycznych rekordów uporządkowane | Pełne zamknięcie blokują wskazane aktywne kontrolery i zewnętrzne zakresy #379/#1303/#346/#376 |
| W5 | 32/32 zaakceptowane wykonania w 8 świeżych wątkach | Ograniczone syntetyczne przypadki; brak telemetrii tokenów i kosztu |
| W6 | Game #377/#378 zintegrowane; #378 PR/MQ/main PASS | Rzeczywisty #380 PR/MQ/main PASS i pomiar ukończony; Platform/Atlas zachowują istniejące dobrane bramki |
| W7 | Ten jeden raport i surowe artefakty | Odczyty dostawców potwierdzone; ten raport wymaga własnej zwykłej ścieżki META #163, odczyt po integracji w komentarzu |

## Integracje i odczyty

| Repozytorium | Scalone PR-y tego wykonania | Ostatni opisany protected main |
|---|---|---|
| META | #159, #160, #162 | `da4cbbceab286ac9ea350a9748eb7e570870851e` |
| Game | #373, #377, #378, #380 | `10b6be51551af5d70d45b4f56c2f6d3e8f6dc528` |
| Platform | #1304, #1306, #1307, #1308 | `b0f268d682b1f9117140168a3a9d9b86c56ba9cc` |
| Atlas | #345, #347, #348 | `53527271db3c49fc44bf548f8934addf7dd695b4` |

META #159: `16a9718e5fe54ab1c153fe78aac789e9bc5da64e`; #160: `1dedfc0f264fe0e23e5365dbe9280c2d96df50c5`; #162: `da4cbbceab286ac9ea350a9748eb7e570870851e`. Dokładne PR, MQ i main CI PASS są w `meta-ci-overhead.json`. Nieaktualny Draft #143 zamknięto bez scalenia jako zastąpiony istniejącymi integracjami.

Game #373: `10446c31b2508ccf6b65cc609a35246bf2666567` z dokładnego kandydata `7e70330e7eab43c9bb0acd82c00e2296bd6c46c5`, PR/MQ/main PASS. #377: `15164c38a2775e45eaff4001fddddbabf4b63ab6`. #378: `65a204ea284c54188b13c4c41cf7411b1a003c61`, PR/MQ/main PASS. Zielona integracja nie usuwa później potwierdzonych braków instrukcji.

Platform #1304: `907546f193e91b0bed2f5f077ab5b874771929ef` z `e8c0e5ea1d2d9faa469ca1b053698427ecdce692`, PR/MQ PASS. Main Agent Governance `34108893446` wykrył zakończony, nadal aktywny rekord zadania; nie jest oznaczony jako PASS. #1306 zarchiwizował ten rekord i wykonał istniejący mechanizm cleanup. #1307 usunął jednorazową zgodę i zarchiwizował własny rekord; #1308 poprawił jego konkretny wymóg checkpointu. Końcowe PR, MQ i main Agent Governance/CI są PASS; wcześniejszych porażek nie wymazano. Historyczny audyt gałęzi na zaufanym main również miał jawne niepowodzenie. Nieaktualny #1270 zamknięto bez scalenia jako zastąpiony #1304.

Atlas #345: `6026b21d5f3024d4a0d33bedd74c66aab43e2187`; #347: `cb30141cd3da23cf98cf92b07dee30b6889ac96b`; #348: `53527271db3c49fc44bf548f8934addf7dd695b4`. PR audit i MQ PASS dla wszystkich trzech. `atlas-ci.json` zachowuje rzeczywiste przebiegi. Początkowy odczyt wrapperem ograniczonym do PR błędnie nie znalazł ich; naprawiono to pełnym Actions REST. Wyzwalacze main-push nie obejmują tych ścieżek, a centralny konsument Atlas sprawdzano manualnie, bez niedozwolonej zmiany workflow.

## Autorytet, instrukcje i rozmiar źródeł

Początkowy META `8673d109d1a364efa7936133082a39750ca74cf9` był lokalizatorem startowym. Nowsze zmiany dotyczyły przechodnich autorytetów maszynowych, dlatego Game i Platform przypięto do `5ed3f14400af450b5875c091e443da70f2d67ab9`, Atlas do `1dedfc0f264fe0e23e5365dbe9280c2d96df50c5`. Późniejsze #159/#160/#162 nie zmieniają tego pakietu. `binding-readback.json` i `instruction-continuity.json` zachowują odczyty oraz potwierdzenie, że poprawki dowodów/cyklu życia nie zmieniły przebadanych promptów ani centralnych konsumentów.

Stały zbiór ścieżek porównano jako sumę zbiorów blobów Git przed/po; brak pliku oznacza zero. Szczegóły, pełne SHA i definicje są w `source-inventory.json`/`.md`. Jest to rozmiar źródeł, nie rzeczywiście załadowany kontekst, tokeny ani oszczędność finansowa.

| Repozytorium | Bajty przed → po | Linie przed → po | Zakres |
|---|---:|---:|---|
| META | 79 894 → 60 331 | 1 419 → 1 121 | 9 zmienionych źródeł; centralny pakiet pozostaje odrębnym narzutem |
| Game | 679 113 → 360 332 | 12 951 → 8 547 | 58 ścieżek sumy zbiorów; 47 aktywnych promptów zachowanych |
| Platform | 307 953 → 106 829 | 5 277 → 1 944 | 20 ścieżek; katalog 23 = 10 aktywnych + 13 historycznych |
| Atlas | 445 757 → 447 347 | 9 612 → 9 915 | 45 ścieżek; 38 promptów zachowanych; wzrost przez 2 nowe pliki walidatora |

Game usuwa pięć skopiowanych walidatorów/testów Remote Desktop i deduplikacji; zostają `validate_inherited_prompt_policy.py` i regresja adopcji. Jego dodatkowy lokalny firewall nadal wymaga naprawy opisanej poniżej. Platform zastępuje `policy_consistency.py` i testy uwierzytelnionym konsumentem centralnym; ewaluacja zachowuje semantyczne warunki zamiast wymuszać kopię tekstu. Atlas dodaje konsument i testy w dozwolonych ścieżkach. Nie znaleziono śledzonych `SKILL.md`, `.agents/**` ani `.codex/**`; nie tworzono ogólnego skilla. Historyczne dowody zachowano; zakres uporządkowania nie obejmuje każdej historycznej ani zewnętrznie posiadanej ścieżki.

## Rzeczywiste próby i granice dowodu

`fixtures/` zawiera wspólne wejścia i protokół. Każde ramię miało jawnie skonfigurowane `gpt-5.6-sol`, `medium` w świeżym niezależnym wątku: pięć początkowych przypadków oraz osobne trzy powtórzenia bezpieczeństwa/dostarczenia promptu na każde ramię. Game: 16/16 w czterech wątkach; Platform: 16/16 w czterech kolejnych. Cztery rzeczywiste wyniki kodu przeszły niezależnie po dziewięć asercji, a cztery README zawierają dokładnie zadaną poprawkę literówki. Odrzucono przeniesienie autorytetu domenowego, wrogą deklarację obejścia kolejki oraz niepotwierdzoną pracę w tle.

- **Kontrakt:** schematy, piny, ścieżki, uwierzytelnienie, regresje i dokładne CI. Atlas dodatkowo allowlista maintenance.
- **Dostarczenie:** faktyczne odczyty i rozwiązanie źródeł Game/Platform w tej powierzchni Work, w powtórzeniach również reprezentatywny prompt. Brak dowodu automatycznego ładowania przez każdy klient. Atlas ma dowód deterministyczny/manualny.
- **Zachowanie:** ograniczone syntetyczne wykonania pięciu typów przypadków, bez wniosku statystycznego, przyczynowego kosztu czy poprawności produkcyjnej. Próba nie obejmowała wszystkich osiągalnych specjalistycznych kontrolerów.

`game-comparison.json`, `platform-comparison.json` i `trials/` zachowują dokładne wyniki, hashe, odczyty, powtórzenia i błędy. Oryginalne raporty zapisano jako tekst, ponieważ ich linki dotyczą scratch; treść i identyfikatory źródeł pozostają niezmienione. Początkowy test Game baseline ujawnił problem `bool`/`int`, który wykonawca naprawił. Pozostałe błędne odczyty, truncation, błędy skryptów i ponowienia również pozostały w surowych zapisach.

## CI: pełny koszt PR + MQ + main

Pomiar to suma API `completed_at - started_at` wykonanych zadań, pominięte = 0; ujemne surowe znaczniki pominiętych zadań zachowano. To suma równoległej pracy, nie faktura ani czas oczekiwania użytkownika. Nie mieszamy jej z wcześniejszymi, krótszymi przedziałami wyliczanymi z logów.

Naturalny bazowy Game #365 zmieniał dwa pliki dokumentacji, lecz nieaktualna migawka dała `unreviewed-document-consumer-inputs` i FULL. `game365-baseline-ci.json`: PR 972 s, MQ 895 s, main 966 s, terminalny cleanup 2 s; razem 2835 s, z duplikatem audytu i CodeQL. W6 odświeża tylko audytowane migawki wejść i regresje; nie zmienia klasyfikatora ani workflow. Nieznany wpływ i późniejszy drift nadal wybierają FULL.

#377 zestarzał się przed scaleniem przez równoległy produktowy main; nie liczymy go jako uzyskanej oszczędności. Faktyczna oś UTC: Ready 09:22:44; MQ 09:22:52; Draft 09:26:39; merge 09:31:53. Konwersja do Draft nie usunęła go z kolejki, a czas commitera 09:22:52 nie był czasem scalenia. Korekta #378 uwzględnia także pominiętą zmianę narzędzia architektury: audyt 23 wybranych plików Rust, +15 339/-51. MQ pozostaje FULL.

Rzeczywisty #380 archiwizuje zakończony rekord #375; to użyteczna praca, nie sztuczny commit pomiarowy. Pierwszy zaufany klasyfikator wybrał `neutral-documentation`, `rust=false`, `windows=false`; cztery ciężkie zadania PR pominięto. Cały pierwszy przebieg nie przeszedł przez brak wymaganych nagłówków w opisie PR; poprawiono metadane przy niezmienionym SHA. Pełna kolejka `34110731737` i wszystkie main workflow (`34111555582`, `34111555586`, `34111555608`) zakończyły się PASS. Na main lekkie policy/metadata, supply-chain i klasyfikator wykonały się; Linux/Windows/PostgreSQL pominięto zgodnie z istniejącą klasyfikacją dokumentacji. Issue #375 jest zamknięty, rekord zarchiwizowany, gałęzie źródłowe usunięte. `game380-final-ci.json` zawiera wszystkie 13 przebiegów i zadania.

| Faza, wszystkie próby | Bazowy #365 | Dokumentacyjny #380 | Różnica obserwowana |
|---|---:|---:|---:|
| PR | 972 s | 291 s | -681 s |
| Merge Queue | 895 s | 915 s | +20 s |
| main | 966 s | 208 s | -758 s |
| terminalny cleanup | 2 s | 3 s | +1 s |
| Razem | 2835 s | 1417 s | -1418 s / -50,0% |

To jedno nierandomizowane porównanie naturalnych PR-ów dokumentacyjnych. Zmieniały się pliki, stan repozytorium, cache i runnery; wynik nie dowodzi przyczynowej oszczędności czasu, tokenów ani pieniędzy. Pokazuje odtworzone pomijanie właściwych ciężkich zadań przy zachowanej pełnej MQ. Początkową pomyłkę sumy trzech faz wobec terminalnego cleanup skorygowano w kanonicznym komentarzu #375 `5569289175`; tabela powyżej jest porównywalna.

Jednorazowy koszt migracji/napraw w enumerowanych PR-ach tego wykonania, przed końcowymi domknięciami: Game 12 619 s (`programme-ci-overhead.json` + `game378-final-ci.json`), Platform 1138 s, META 948 s (`meta-ci-overhead.json`), Atlas 77 s (`atlas-ci.json`). Liczymy porażki, anulowania, duplikaty i pracę CodeQL. Migawka kolektora początkowo pominęła aktywne MQ #378 przez wyszukiwanie tylko znanych SHA; zapis ograniczenia poprawiono i dodano kompletne MQ/main. Końcowe domknięcia dodają Game 1417 s (`game380-final-ci.json`) i Platform 452 s (`platform-cleanup-final-ci.json`), w tym wszystkie naprawy #1306/#1307/#1308. Suma Game wynosi 14 036 s, Platform 1590 s; META 948 s jest migawką sprzed finalnej generacji raportu #163, której przebiegi będą wskazane w odczycie PR. Równoległe PR-y R5 i ich zewnętrzne sesje nie są w tej sumie; to nie pełny koszt organizacji, faktura ani deklaracja amortyzacji.

Platform już pominął ciężkie runtime jobs w zmianie instrukcji; pierwsza generacja to 270 s, w tym CodeQL 196 s. Atlas ma istniejące tanie bramki maintenance: #345 27 s, #347 24 s, #348 26 s. Nie dodano szerokiej zmiany workflow bez wykazanego zysku.

## Pozostałe konflikty i własność

**Game — P1:** `OWNER_FUNDED_AI_POLICY.md` nadal nadaje stałe uprawnienie recenzji i odwołuje się do wycofanego `CODEX_REVIEW_POLICY.json`. `ANTI_STALL_AND_EXECUTION_BUDGET.md` i `GOVERNANCE_CONTRACT.json` nadal ustalają lokalne retry oraz `WAITING`/`ROTATE`, konkurując z META. P2: surowe podciągi w walidatorze odrzucają także inertne/negatywne dowody, nie obejmując wszystkich aktywnych kontrolerów; pozostają narzucone modele/wysiłek i niepowiązane obowiązkowe odczyty. [Kanoniczne wycofanie akceptacji #367](https://github.com/Oteryn/Oteryn-Game/issues/367#issuecomment-5569126004) i komentarz #373 `5569130209` zachowują rozróżnienie od uczciwego 16/16. Naprawę posiada aktywnie zmieniany #379; #367 pozostaje otwarty. Historycznych ADR/Superpowers ani no-op walidatora nie uznano za czynny autorytet.

**Platform — P1 programu:** #1304 poprawnie spełnił swój ograniczony zakres, lecz sześć starszych dokumentów specjalistycznych pozostaje osiągalnych. `GITHUB_ONLY_EXECUTION.md` dopuszcza bezpośredni squash merge przy niedostępnym auto-merge, w sprzeczności z META. `TERMINAL_ONLY_COMMUNICATION.md` ustanawia własny kontroler. Ich cleanup posiada #1302/#1303. Przegląd wcześniejszego `ec473…` wykazał rozbieżność z #1304; właściciel później opublikował normalne uzgodnienie z `907546…` i nadal zmieniał kandydata (ostatnio `46f177124fd6604d699bef822b209eed0df29249`). Nie kwalifikowano w tym wykonaniu jego nowego dokładnego delta ani integracji. Nie wolno stosować zielonych testów starego SHA do nowego kandydata. Szczegóły zawiera `platform-r5-residue-review.md`.

**Atlas i historia:** #346 posiada korektę maintenance authority i rodzinę promptów E2E; #376/#374 posiada dwanaście terminalnych packetów Game. Nie przejmowano tych aktywnych zakresów. `ownership-readback.json` zapisuje również pozostałe otwarte PR-y, które nie należą do tego wykonania. Opcjonalna nowa konfiguracja Atlas nie ma obecnie mandatu i pozostaje poza dozwolonymi ścieżkami; nie jest fikcyjnie oznaczona jako wykonana.

**Platform cleanup:** #1306 korzysta z istniejącego main-push `apply-reviewed-manifest`, bez zmian kontrolera lub kryteriów. Zestaw to trzy dokładne zamknięte, niescalone PR-y #1270/#1290/#1291. Inwentarz hosted potwierdził 21 gałęzi/3 kandydatów; po oczekiwanej porażce prowizorycznego digestu upload artefaktu został pominięty. Zestaw odtworzono niezależnie z live REST, nie nazwano go pobranym artefaktem. Digest, SHA, PR, aktywne roszczenia, retention, ochrona i polityka są ponownie sprawdzane przez istniejący mechanizm. #1050 to jego schemat/proweniencja, a bieżący zakres pochodzi z #142/#1301/#1305. Scalenie #1306 jako `f3ded5cb400e1a44cc1649549994f4cf890085a3` uruchomiło guarded apply: workflow `34111160408`, job `101707594801` PASS. Niezależny pełny odczyt 17 pozostałych gałęzi potwierdził nieobecność wszystkich trzech celów; `platform-cleanup-apply.json` zachowuje log i exact-SHA recovery. Scalony #1307 (`57083e3bdcf9d1b8d28aac6fe6d6ce71f73012dd`) usunął jednorazową zgodę i zarchiwizował rekord, zamykając #1305. #1308 (`b0f268d682b1f9117140168a3a9d9b86c56ba9cc`) naprawił archiwalny `next_action: none`, wykryty przez jawne sprawdzenie checkpointu mimo zielonego hosted skanu aktywnych zadań. Końcowe main CI/Agent Governance PASS; wszystkie trzy cele i gałęzie cleanup są nieobecne. `terminal-file-readback.json` oraz `final-main-readback.json` wiążą końcowy odczyt.

## Konfiguracja wykonania i zachowane zabezpieczenia

`execution-metadata.json`: 14 tożsamości dzieci — 3 wykonawców Sol/medium, 2 selektywnych recenzentów Sol/high, 1 kolektor Sol/low, 8 świeżych ramion Sol/medium. To jawna konfiguracja, nie niezależne poświadczenie runtime ani liczba wszystkich tur. Koszt pracy dzieci nie został pominięty. Po początkowej autoryzacji nie żądano dodatkowych potwierdzeń właściciela. Telemetria tokenów, cache, rozumowania i rozliczeń pozostaje UNAVAILABLE; nie wyliczono fikcyjnych oszczędności.

Nie zmieniano produkcji, sekretów, ochrony, wymaganych bramek ani reguł kolejki. Zachowano domeny Game, Platform i Atlas. `protection-readback.json` rozróżnia legacy branch protection od rulesets: Game wymaga `game-gate` i MQ; Atlas rzeczywiście wymaga `Merge authority audit / protected-base validate` oraz organizacyjnego workflow, mimo starszej nazwy w dokumentach należących do #346. Nie używano bypass.

Ten raport zachowuje również koszt i skutek własnych błędów: korekty uwierzytelnienia, przypięć, zgubionego historycznego dowodu, niepełnych zakresów, rekordów cyklu życia, metadanych PR i odczytów CI. Dwie drobne wady pierwszego checkpointu raportu — skrócone lokalne SHA i zbyt wczesny znacznik czasu — poprawiono bez powtarzania prób modelu. `SHA256SUMS.json` wiąże pliki dowodowe; końcowy main samego raportu będzie potwierdzony po scaleniu, poza jego własnym commitem.

## Granica zakończenia tego wykonania

Dalsze edycje źródeł #379/#1303/#346/#376 należą do aktywnych, odrębnie przydzielonych mutatorów; ich SHA zmieniały się podczas tego wykonania. Nie ma w tym wykonaniu przekazania tej własności ani dokładnej końcowej kwalifikacji tych kandydatów. Przejmowanie ich plików lub scalanie zmieniających się Draftów naruszałoby zasadę jednego właściciela zapisu. Pozostałość jest więc jawnie pozostawiona tym ścieżkom, a nie przedstawiana jako zielone ukończenie programu. #142 i #367 pozostają otwarte. Wyniki niezależnych własnych ścieżek, w tym normalne protected integracje i CI, są domknięte; nie ma własnego PR dostawcy pozostawionego jedynie z działającym CI/MQ.
