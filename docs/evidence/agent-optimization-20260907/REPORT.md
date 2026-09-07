# Oteryn — optymalizacja instrukcji i weryfikacji, 2026-09-07

Status: **W TOKU — ten checkpoint nie zamyka programu**. Rodzic: [META #142](https://github.com/Oteryn/Oteryn/issues/142).

Ten zapis zachowuje rzeczywiste wyniki prób przed integracją dostawców. Końcowe odczyty protected main, dowody Merge Queue i pełne podsumowanie CI zostaną uzupełnione po zakończeniu aktywnych prac.

## Wyniki dotychczasowe

- META: #159, #160 i #162 zintegrowane zwykłą ścieżką Merge Queue. Odczyt po #162: `da4cbbceab286ac9ea350a9748eb7e570870851e`, protected; CI PR, MQ i main PASS.
- Atlas: #345 oraz korekta przypięcia #347 zintegrowane. Porządki sześciu szablonów w #348 zintegrowano jako `53527271db3c49fc44bf548f8934addf7dd695b4`; PR audit34105663446 oraz MQ34106211138/34106211085 PASS. Siódmy zakres należy do aktywnego PR #346. Brak istniejących `.agents`, `.codex` i `SKILL.md`; W3B nie wymaga naprawy nieistniejących plików, a opcjonalna nowa konfiguracja pozostaje poza aktualnym zakresem maintenance.
- Game: kandydat #373 przeszedł niezależny przegląd strukturalny, pełne CI i ograniczone próby modelu. Wymaga uzupełnienia rekordu oceny oraz końcowego CI/MQ/main. Osobny #377 aktualizuje audytowane migawki wejść klasyfikatora; nie zmienia algorytmu ani bramek.
- Platform: kandydat #1304 przeszedł przegląd strukturalny i próby modelu wraz z powtórzeniami. Trwają naprawy rekordów cyklu życia wykryte przez CI.

## Próby modelu

Warunki i wejścia są w `fixtures/`. Każde ramię uruchomiono w świeżym niezależnym wątku z jawną konfiguracją `gpt-5.6-sol`, `medium`. Porównanie obejmuje poprawkę dokumentacji, rzeczywisty mały kod i dziewięć asercji, granicę domeny, wrogą historyczną deklarację uprawnień oraz kontynuację. Osobne powtórzenia sprawdzają trzy decyzje dotyczące bezpieczeństwa i dostarczenie reprezentatywnego szablonu zadania.

Game: 16/16 poprawnych wykonań przypadków w czterech wątkach. Platform: 16/16 w kolejnych czterech wątkach. Łącznie 32 poprawne wykonania przypadków w ośmiu świeżych wątkach. Koordynator sprawdził pliki oraz niezależnie wykonał dziewięć asercji dla każdego z czterech wynikowych modułów. Oba repozytoria odrzuciły proponowane przeniesienie autorytetu, obejście Merge Queue i niepotwierdzoną pracę w tle.

To ograniczone badanie na syntetycznych zadaniach. Nie dowodzi bezbłędności przyszłych zadań, dostarczenia instrukcji przez każdy klient ani statystycznej oszczędności. Surowe raporty w `trials/` zachowują również błędy odczytów, ponowienia i wyniki testów; zapisano je jako tekst, ponieważ ich oryginalne linki dotyczą przestrzeni roboczej. Faktyczne identyfikatory niezmiennych źródeł pozostają w treści.

## Koszt i ograniczenia pomiaru

Telemetria tokenów, cache, rozumowania i rozliczeń nie jest udostępniona. Nie oszacowano fikcyjnej faktury ani procentu oszczędności tokenów. Rozmiary źródeł nie są tokenami; część raportów mierzy pełne obiekty czytane fragmentami, więc nie należy odejmować nieporównywalnych sum.

Pierwsza generacja Platform #1304: 270 sekund sumy znaczników czasu wykonanych zadań, w tym 196 sekund CodeQL i nieudane sprawdzenia cyklu życia. Pominięte zadania liczą się jako zero; ujemne różnice znaczników dla kilku pominiętych zadań zachowano jako surową anomalię. To wskaźnik obserwacyjny, nie rozliczony czas runnera. Końcowe porównanie musi obejmować PR + MQ + main i wszystkie poprzednie próby.

## Kontrole

Brak zmian produkcyjnych, sekretów, ustawień ochrony, wymaganych bramek lub osłabienia Merge Queue. Aktualizacja migawki CI zachowuje pełną ścieżkę dla nieznanego albo nieaudytowanego wpływu. Nie wykonywano sztucznych commitów wyłącznie do uruchomienia CI.
