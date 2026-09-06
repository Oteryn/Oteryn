# Oteryn — instruction debt: koszt, złożoność i skuteczność

Data: 2026-09-06. Rewizja raportu: 2 — niezależna inspekcja źródeł i ograniczone próby deterministyczne.
Klasa: `AUDIT_EVIDENCE`. Rekomendacje nie są polityką wykonawczą ani zgodą na ich wdrożenie.
Alias: [Oteryn: instruction debt audit](../agents/prompts/OTERYN-INSTRUCTION-DEBT-AUDIT.md).

Aktualne polecenie użytkownika upoważnia do audytu i aktualizacji raportu w istniejącym META PR #151. Nie upoważnia do zmian polityk, CI, ustawień, repozytoriów produktowych ani produkcji. Zachowano identyfikatory D1–D17; dodano D18–D21. Pełny poprzedni raport, proponowane brzmienia i jego inwentaryzacja pozostają w [historycznej rewizji a08e0795](https://github.com/Oteryn/Oteryn/blob/a08e0795c49d62c5e2e33e1013444e245c661770/docs/evidence/OTERYN-INSTRUCTION-DEBT-AUDIT-20260906.md).

Legenda: **FACT** — odczyt lub wykonana próba; **INFERENCE** — wniosek z dowodów; **HYPOTHESIS** — przewidywany efekt bez próby zachowania agenta; **UNKNOWN** — brak danych; **RECOMMENDATION** — propozycja. Stan jest snapshotem. Przed decyzją odświeżyć tylko materialne zmienne fakty.

## A. EXECUTIVE FINDINGS

**RECOMMENDATION:** optymalizować całkowity koszt poprawnie zakończonego zadania, nie samą długość promptu. Koszt obejmuje kontekst, wywołania narzędzi, koordynację, CI, poprawki, odtworzenie stanu i udział człowieka. Krótsze instrukcje, które pomijają granicę uprawnień lub blokują poprawną pracę, nie są optymalizacją.

| Priorytet | Ustalenie | Znaczenie |
| --- | --- | --- |
| Wysoki | D15/D19: walidator #145 zarówno przepuszcza sprzeczne nakazy, jak i odrzuca poprawne wskazanie pliku do audytu | Naprawić kontrakt i przypadki dodatnie, nie tylko dopisywać regexy |
| Wysoki, warunkowy | D18: Platform root + nested AGENTS to 35 209 B wobec domyślnego limitu loadera 32 768 B | Ryzyko niepełnego załadowania; rzeczywista konfiguracja użytkownika jest nieznana |
| Wysoki | D1/D3/D5/D6/D9: równoległe stare i nowe zasady review, delegacji oraz kontynuacji | Usuwać źródła rozbieżnych decyzji, zachowując safety i historię |
| Przed adopcją | D20/D21: dowód ancestry nie jest dowodem protection; zielony test biblioteki nie dowodzi adopcji przez produkty | Precyzyjnie określić, co zweryfikowano |
| Średni–wysoki | D10: dokumentacja Atlas wymienia inny required context niż ruleset | Uzgodnić instrukcje z rzeczywistym enforcementem, bez jego osłabiania |
| Koszt do zmierzenia | D7/D14: duży obowiązkowy bootstrap oraz pełna kwalifikacja Game MQ | Oddzielić zmniejszenie kontekstu od osobnej optymalizacji CI |

FACT: uruchomiono 10 celowo dobranych prób skopiowanych funkcji walidatora; 7 wyników różni się od jawnie zdefiniowanego oczekiwania audytu. To kontrprzykłady z trzema kontrolami, nie 70% awaryjności systemu ani benchmark Astry. Szczegóły w E.

**Zmiana poprzedniej rekomendacji:** nie wystarczy „naprawić dwa regexy i scalić #145”. Potrzebne są również pozytywne przypadki legalnych zadań, zgodność deklarowanego dowodu ze sprawdzanym faktem oraz osobny dowód rzeczywistej adopcji. Nie tworzyć w tym celu kolejnego systemu orkiestracji lub usług zatwierdzających.

## B. INSTRUCTION INVENTORY AND EVIDENCE BOUNDARY

### B1. Rewizje

| Oznaczenie | Repozytorium | Odczytana rewizja |
| --- | --- | --- |
| M | Oteryn/Oteryn main | `0c493896040072badeff1f333eb83d7114a993ff` |
| G | Oteryn/Oteryn-Game main | `53c6bdf06a2282d893035a995c46052c88f935b4` |
| P | Oteryn/Oteryn-Platform main | `3b2ea1c7392187d5d22488673073dc8f8305a374` |
| A | Oteryn/Oteryn-Atlas main | `51623c7dab2346cee39cd51e3caa845bf4b65426` |
| V | META PR #145, nadal Draft | `697233ed2b0a6495e1c897be9b70ffc2d7ae3428` |
| R0 | Raport i alias przed aktualizacją, PR #151 Draft | `a08e0795c49d62c5e2e33e1013444e245c661770` |

M, P i A są zgodne z poprzednim raportem. Porównanie G od `9be69b4e0a06f3978d5c5c5603ca3e5670a9f18a` obejmuje dwa commity i 12 ścieżek. Backup `Oteryn/Oteryn-Platform-Migration-Backup-20260818` pozostaje w historycznym zakresie raportu; jego stanu nie odświeżano w tej rewizji audytu.

### B2. Faktyczny zakres tej inspekcji

Ponownie przeczytano istotne źródła: root M/G oraz odpowiednie fragmenty root P/A; kontrakty access, bounded i persistent w M; JSON continuation; centralny kontrakt i standard promptów V; funkcje centralnego walidatora i workflow V; polityki review G; anti-stall G; bootstrap P; maintenance document i validator A; macierz CI G. Sprawdzono także rozmiary plików P, aktualny ruleset Atlas, PR #145/#151, dyskusję #151, porównanie G i zarchiwizowany checkpoint #346. Odczytano historyczny run CI i dokumentację OpenAI.

Poprzednie liczby 345 plików, 122 promptów, osiem AGENTS i 19 promptów z profilami modeli są **historyczną inwentaryzacją R0**, nie liczbą ponownie przejrzanych źródeł ani pomiarem ładowania w tej sesji. D8, D12, D13 i część D16 zachowano jako ustalenia bazowe, bez ponownego pełnego przeglądu ich kolekcji. Nie wykonano ponownego audytu całej konfiguracji organizacyjnej ani wszystkich archiwów.

### B3. Rozmiar i aktywacja

| Platform P | Bajty UTF-8 z metadanych GitHub |
| --- | ---: |
| `AGENTS.md` | 26 661 |
| `docs/agents/AGENTS.md` | 8 548 |
| Suma tych dwóch plików | 35 209 |
| `docs/agents/PLATFORM_AGENT_BOOTSTRAP.md` | 18 025 |
| `docs/agents/CONTEXT_ROUTING.md` | 7 182 |
| Root + bootstrap + router | 51 868 |
| Powyższe + nested AGENTS | 60 416 |

To rozmiary źródeł, nie telemetryka tokenów. Automatycznie odkrywany łańcuch AGENTS i dokumenty jawnie doczytywane przez agenta to różne mechanizmy. Nie należy porównywać całych 60 416 B z limitem automatycznego loadera.

Root/nested są aktywne zgodnie ze ścieżką i mechanizmem sesji. Bootstrap P jest obowiązkowy przez root. Prompty, specjalistyczne procedury i skills powinny być ładowane po trafnym wyborze. Evidence i archiwa nie są instrukcjami uruchomienia. Sam odsyłacz nie uzasadnia ponownego czytania wszystkich zależności.

## C. PRECEDENCE / ACTIVATION MAP

**RECOMMENDATION — architektura docelowa:** krótki kontrakt organizacyjny M → jawny immutable binding produktu → root/nested z lokalnymi invariantami → delta konkretnego zadania. Model, effort, narzędzia i fallback należą do profilu wykonania, nie do tożsamości roli.

FACT: Game przypina routing do META `e002fc7532188e73a0f495da3e20710541ed50e0`, Platform do `8fac1d55805fc3372351ea0a55ad7728b3570ebc`, Atlas do M. Nowy bundle V nie jest scalony. Nie uznawać obecnych produktów za adopters V ani traktować rozbieżnego starego pinu jako automatycznej zgody na jego podmianę.

Zakres użytkownika i obowiązujące uprawnienia pozostają nadrzędne. Root może jawnie wycofać starszy lokalny kontroler; sam młodszy timestamp nie rozstrzyga authority. GitHub rozstrzyga lifecycle/head/checks, lecz komentarz, alias, manifest i dostępne narzędzie nie tworzą uprawnień do produkcji lub innego repozytorium.

**RECOMMENDATION — świeżość:** raz ustalić bazowy kontekst zadania; niezmienne treści reuse po repo/path/SHA. Przed publikacją lub integracją odświeżać mutable head, stan PR, wymagane checks i materialne konflikty. Zmiana main wymaga inspekcji wpływu, nie automatycznego odtworzenia całego zadania. Brak dowodu uprawnienia nadal zatrzymuje dotkniętą operację; nie uzasadnia jednak blokowania niezależnego bezpiecznego odczytu.

## D. MATERIAL FINDINGS

### D1. Stary kontroler review — potwierdzone, wysoki priorytet

FACT: G `docs/agents/CODEX_REVIEW_POLICY.json` ma `RETIRED` i `standing_review_controller: false`. `docs/agents/OWNER_FUNDED_AI_POLICY.md` nadal nakazuje mechaniczny kontroler i `CODEX_REQUIRED`; root jawnie go superseduje.

RECOMMENDATION: lokalny dokument ograniczyć do odsyłacza do aktualnej authority i właściwej granicy niereviewowanego użycia metered AI. Wycofać dispatchable kopie kontrolera w promptach, nie niezależność review. Kryterium: jeden wybór review dla tego samego ryzyka, bez drugiej bramki AI.

### D2. Routing po etykiecie powierzchni — potwierdzone w META

FACT: M `ecosystem/agent-continuation-policy.json` dopuszcza `software_development_loop` tylko dla `codex`. Kontrakt access równocześnie wymaga rozpoznawania faktycznych narzędzi. Poprzedni raport opisuje dodatkowy handoff w P `EXECUTION_MODE_ROUTING.md`; tego pliku nie odczytano ponownie.

RECOMMENDATION: rozdzielić zdolność do edycji/testów od zdolności do trwałego automatycznego wznowienia. Kontynuować na obecnej autoryzowanej powierzchni, jeśli spełnia wymagania konkretnej czynności. JSON, walidator i procedura muszą zmienić się spójnie. HYPOTHESIS: mniej zbędnych handoffów; nie wykazano jeszcze oszczędności.

### D3. Parallel-first — potwierdzone w G/P

FACT: rooty G/P wymagają parallel-first i uzasadnienia wykonania szeregowego; M uznaje `single_agent` za zwykłą strategię. Produkty mają starsze jawne piny.

RECOMMENDATION: przy kontrolowanej adopcji zastąpić obowiązek przez `single_agent` lub `parallel_when_beneficial`. Równoległość tylko dla niezależnego zakresu z korzyścią ponad koszt koordynacji. Zachować jeden mutating owner na writable lane. Nie narzucać nowego obowiązku uruchamiania subagentów „dla oszczędności”.

### D4. Checkpointy — częściowo naprawione

FACT: G przeniósł `OTV2-20260906-native-evidence-wire-346.md` z `tasks/active` do `tasks/archive`; metadane to `completed` i `RELEASED`. Porównanie nie zmienia pozostałych 12 plików z pierwotnej listy 13. Nie odświeżono indywidualnie wszystkich ich Issues i alokacji; liczba 12 nie jest nowym potwierdzonym licznikiem stale work.

RECOMMENDATION: przed archiwizacją sprawdzić terminalne Issue/PR i release ownership. GitHub przechowuje lifecycle, plik jest recovery cache. Pakiet archiwizacji łączyć w spójną zmianę, nie serię PR-ów dla każdego pola. Nie tworzyć testu kodującego listę „dzisiaj zamkniętych Issues”.

### D5. Retry budget a BLOCKED — potwierdzone

FACT: G `ANTI_STALL_AND_EXECUTION_BUDGET.md` i bootstrap P nakazują zakończenie po trzech repair cycles. M odróżnia `STALLED` przy niezmienionej awarii od zależności wymagającej właściciela/uprawnienia/polityki.

RECOMMENDATION: ograniczać niezmieniony łańcuch prób, a nie każdą nową diagnostycznie uzasadnioną naprawę. Zachować trwałe liczniki przez rotację. Nie interpretować wyczerpania budżetu workera jako ukończenia zadania lub konieczności decyzji użytkownika.

### D6. „Later invocation” — potwierdzone

FACT: bootstrap P wymaga kolejnego wywołania, zanim scalona zmiana authority zacznie obowiązywać; root wymaga uzgodnienia zmienionej authority przed dalszą mutacją.

RECOMMENDATION: po merge istotnej polityki odświeżyć applicability w bieżącym zadaniu i zachować niezmienioną pracę. Nadal bezwzględnie zakazać samoposzerzenia scope przez własną niezweryfikowaną gałąź. Nowe wywołanie nie powinno być rytuałem bezpieczeństwa.

### D7. Bootstrap P — potwierdzona duplikacja

FACT: 18 025 B bootstrapu powtarza capability, publishing, komunikację, retry, recovery, GitHub-only i closeout obok root oraz specjalizacji.

RECOMMENDATION: wejście pozostawia scope, safety i mapę warunkowego wyboru procedury. Usunąć powtórzone instrukcje dopiero po wskazaniu jednej obowiązującej authority. Nie rozbijać pliku na dziesięć obowiązkowo czytanych dokumentów; to przenosi koszt zamiast go usuwać.

### D8. Szerokie ładowanie nested G — zachowane z baseline

R0 wskazuje `docs/agents/CONTEXT_ROUTING.md` jako źródło obowiązkowego czytania `docs/agents/AGENTS.md` także poza zmianami dokumentacji. Ten router nie zmienił się w sprawdzonym delta G; bez nowego pełnego walkthrough.

RECOMMENDATION: najbliższe instrukcje dla affected paths oraz lifecycle tylko wtedy, gdy jest potrzebny. Trivial work bez checkpointu nie powinno tworzyć programu ani zbędnych plików zarządzania.

### D9. Review po każdej zmianie SHA — potwierdzone

FACT: anti-stall G unieważnia każde wymagane independent review po przesunięciu head; root review policy wymaga material risk-bearing change.

RECOMMENDATION: aktualny head wymaga wymaganych checks i przeglądu delta. Ponowne niezależne review, gdy zmieniło się oceniane ryzyko lub obowiązuje wyraźny exact-head contract. Zachować wcześniejszy dowód wraz z zakresem i rewizją, nigdy nie przepisywać starego CI jako wyniku nowego head.

### D10. Atlas required context — ponownie potwierdzone

FACT: A `docs/maintenance/ATLAS-MAINTENANCE-MODE.md` podaje `atlas-gate`; live ruleset `22103758` wymaga `Merge authority audit / protected-base validate` i MQ. Nazwa joba nie dowodzi required context. Dokument nadal używa perspektywy „This Stage B candidate”, zamiast samodzielnego opisu późniejszego stanu.

RECOMMENDATION: poprawić required-context locator i opis etapu po readbacku workflow inventory. Nie zmieniać rulesetu, by pasował do starego zdania. Frozen runtime/deployment oraz protected-base validator pozostają.

### D11. Historyczne procedury Atlas — ryzyko aktywacji

FACT: root A zawiera maintenance freeze oraz rozbudowane procedury testowe. HYPOTHESIS: bez wyraźnego wyboru etapu agent może próbować wykonywać zawieszoną procedurę.

RECOMMENDATION: najpierw wybrać maintenance albo jawnie autoryzowane restoration. Procedury runtime przechowywać jako warunkowe references; nie usuwać właściwych oracles, visual acceptance ani rozdziału danych fixture/bounded/fullworld.

### D12. Model/effort w roli — baseline, zmieniona rekomendacja

Liczba 19 promptów Game jest inwentaryzacją R0, nie nowym pomiarem. RECOMMENDATION: zachować alias jako rolę; model, powierzchnię, effort i fallback przenieść do profilu wykonania. Nie zakładać dostępności modelu lub wymuszenia effortu na każdej powierzchni.

Nie zalecamy globalnego `low` ani globalnego najwyższego effortu. Przy porównaniu instrukcji utrzymać ten sam model i effort. Dopiero potem oddzielnie mierzyć warianty effortu i delegacji. Aktualne wskazówki OpenAI zalecają przy migracji zachować dotychczasowy efektywny effort, poza przejściem z `none`/`minimal` do `low` [O2].

### D13. Każdy odsyłacz przy governance — baseline

R0 wskazuje G `docs/agents/AGENTS.md` i wymóg review wszystkich referenced files. Brak nowego pełnego review tego nested pliku.

RECOMMENDATION: sprawdzać zmienioną politykę, bezpośrednich konsumentów i kontrakty dotknięte znaczeniem zmiany. Rozszerzać inspekcję po konkretnej zależności bezpieczeństwa lub kompatybilności, nie przez rekurencję każdego linku.

### D14. Game MQ i koszt kwalifikacji — konfiguracja potwierdzona

FACT: G `docs/agents/BUILD_TEST_MATRIX.md` opisuje impact routing PR oraz pełny zestaw MQ, w tym Linux/PG, Windows/SIM i supply chain. AGENTS nie jest zwykłą neutralną dokumentacją w classifierze. Szerokie testy są zamierzonym fail-closed zachowaniem, nie automatycznie błędem.

RECOMMENDATION: osobny, autoryzowany projekt CI może wybierać unię ryzyk pełnego synthetic group diff z protected classifiera. Unknown/incomplete nadal wybiera FULL. Najpierw pomiar całego PR → MQ → main, następnie shadow i realne canary. Nie obiecywać oszczędności z samego skrócenia Markdown.

### D15. Dwa braki #145 — potwierdzone próbami

FACT: V `tools/governance/central_agent_policy.py` używa literalnego substringu bez normalizacji whitespace; `validate_task_prompt_text()` nie stosuje kontroli parallel-first/serial-exception obecnych w overlay validatorze. P03–P06 pokazują akceptację tekstów objętych negatywnym oczekiwaniem audytu.

RECOMMENDATION: naprawić oba braki, ale nie stosować poprzedniej minimalnej propozycji regexów bez D19. Walidacja ma wykrywać sprzeczne aktywne dyrektywy, nie blokować audyt ich plików. Wymagane kontrolne przypadki dopuszczalne i odrzucane, w istniejącej suite.

### D16. Skills i konfiguracja zewnętrzna — UNKNOWN obecnie

Nie potwierdzono ponownie historycznego katalogu skills, statusów disabled ani innych instalacji użytkownika. R0 zachowuje dowody tamtej sesji; nie uzasadnia ponownego usuwania lub reinstalacji.

RECOMMENDATION: precyzyjne metadata wyboru, treść ładowana po aktywacji i wąskie references, zgodnie z mechanizmem progressive disclosure [O3]. Nie dodawać nowego skilla, frameworka czy pluginu, gdy wystarcza poprawa istniejącego wejścia. Nie traktować katalogu `docs/superpowers/` jako dowodu aktywnego pluginu.

### D17. KEEP — ochrona funkcjonalności i bezpieczeństwa

Zachować jawne scope i zakaz self-authorized expansion; jeden writer i ownership; protected checks/MQ tam, gdzie wymagane; independently current authority i session-generation fencing Game; determinism/clock/RNG; Atlas jako projekcję Game z prawami/provenance; niezależne negatywne oracles; rozdział fixture/bounded/fullworld; credential i production fences; historię recovery; zakaz no-op retriggerów, resetowania retry i fikcyjnej pracy w tle.

Usunięcie zbędnego tekstu wymaga zachowania tych decyzji i obserwowalnych wyników. Żaden z nowych kontrprzykładów nie uzasadnia osłabienia zabezpieczeń produktu.

### D18. Loader AGENTS może nie objąć całej polityki — nowe

FACT: root P i nested `docs/agents/AGENTS.md` sumują się do 35 209 B, czyli 2441 B ponad 32 768 B, jeszcze przed separatorami. Dokumentacja Codex opisuje limit `project_doc_max_bytes` 32 KiB i ładowanie łańcucha root → current working directory [O1].

INFERENCE, pewność wysoka warunkowo: dla takiego łańcucha przy domyślnej konfiguracji istnieje ryzyko niepełnego załadowania instrukcji. UNKNOWN: rzeczywisty limit, working directory i zachowanie loadera na powierzchniach użytkownika. Nie zaobserwowano obcięcia jego sesji.

RECOMMENDATION: zredukować root i powtórzenia; najważniejsze granice pozostawić blisko wejścia. Sprawdzić rzeczywiste loaded instructions dla root i docs/agents w jednym reprezentatywnym środowisku. Nie podnosić limitu bezwarunkowo ani dodawać nowej blocking bramki liczby bajtów.

### D19. Linter blokuje legalne zadania — nowe, wykonane próby

FACT: P07/P09 odrzucają read-only audit z dokładnym locatorem polityki. P08 odrzuca lokalne ograniczenie równoległości dla migracji tylko dlatego, że zawiera frazę `parallel-first`. `PROMPTING_STANDARD.md` V dopuszcza scope/locators i zawężenie authority; regex nie rozróżnia tych funkcji tekstu.

RECOMMENDATION: odróżnić locator od skopiowanej polityki oraz aktywny nakaz od negacji i historycznego cytatu. Gdzie to pomaga, walidować jawnie wydzielone pola scope/locators, a nie każde wystąpienie nazwy pliku. Nie budować uniwersalnego silnika rozumienia Markdown ani odpłatnego LLM-judge dla każdego PR. Kryterium: przykłady legalnej pracy nie wymagają obchodzenia lintera przez zatajenie źródła.

### D20. Zakres dowodu resolvera jest zawężony — nowe, inspekcja statyczna

FACT: V `resolve_meta_authority_via_github()` ustawia `merged_to_protected_main` na podstawie statusu compare `ahead`/`identical`. Sprawdza istnienie commitu i ancestry, ale ta funkcja nie odczytuje protection. Osobny odczyt M `branches/main` potwierdził `protected: true`; nie twierdzimy, że obecne META jest niechronione.

RECOMMENDATION: rozdzielić te fakty lub jawnie konsumować protection evidence z istniejącego preflightu. Nazwa i zaakceptowany zakres dowodu muszą odpowiadać wykonanym sprawdzeniom. Nie dodawać kolejnego ledger/attestation controller. Nie wykonano eksperymentu na niechronionej gałęzi ani testu obejścia zabezpieczeń.

### D21. Bundle CI nie jest dowodem adopcji — nowe doprecyzowanie

FACT: sprawdzony workflow V uruchamia suite i `central_agent_policy.py`; jego `main()` waliduje bundle. PR #145 jest META-only i nie zmienia root AGENTS. Nie ma z tego dowodu, że każdy rzeczywisty provider/prompt jest już objęty nowym kontraktem. Brak adopcji w tym PR jest jego jawnym zakresem, nie sam w sobie defektem.

RECOMMENDATION: osobno raportować gotowość bundle, adopcję produktu i wynik próby agenta. Po adopcji sprawdzić rzeczywiste aktywne wejście oraz poprawny i niedozwolony przykład; historia nie staje się dispatchable przez samą obecność pliku. Centralizacja zakończona oznacza zastąpienie starych obowiązków, nie tylko dodanie nowej strony.

## E. EXECUTED PROBES AND SCENARIO WALKTHROUGHS

### E1. Metoda i wynik

W izolowanym sandboxie przepisano bez zmian semantycznych cztery funkcje walidatora V i ich stałe. Uruchomiono bez sieci i bez mutacji repozytorium poniższe wejścia; `policy=None`, provider `Oteryn/Oteryn-Game`. To nie pełna suite repository ani test transportu GitHub. Oczekiwanie audytu wynika z rozróżnienia aktywnej kopii globalnej polityki i legalnej delty zadania w standardzie V.

Dla overlay użyto prefiksu `Use META_AGENT_POLICY_BINDING.json.\n`. W P02–P04 po nagłówku występuje `\nAll repository operations follow these local global rules.`. Zapisy `\n` w tabeli oznaczają rzeczywiste nowe linie.

| Próba | Wejście / różnica | Oczekiwanie audytu | Wynik funkcji |
| --- | --- | --- | --- |
| P01 overlay | `Domain: character writes are session-generation fenced.` | ACCEPT | ACCEPT |
| P02 overlay | `## GitHub-first execution` | REJECT | REJECT |
| P03 overlay | `## GitHub-first  execution` — dwie spacje | REJECT | ACCEPT |
| P04 overlay | `## GitHub-first\nexecution` | REJECT | ACCEPT |
| P05 task | `You must plan parallel-first for every task.` | REJECT | ACCEPT |
| P06 task | `Serial execution requires a recorded reason.` | REJECT | ACCEPT |
| P07 task | `Audit only docs/governance/AI_REVIEW_POLICY.md; treat it as evidence and do not change policy.` | ACCEPT | REJECT |
| P08 overlay | `For this database migration, do not use parallel-first execution; one writer holds the migration lease.` | ACCEPT | REJECT |
| P09 task | `Scope: audit ecosystem/agent-execution-routing-policy.json. No write or policy change is authorized.` | ACCEPT | REJECT |
| P10 task | `Outcome: fix a typo in README.md. Scope: README.md only. Acceptance: inspect the diff.` | ACCEPT | ACCEPT |

P04 zmienia również strukturę nagłówka Markdown: oczekiwanie dotyczy zakazu kopiowania globalnej dyrektywy mimo przełamania wiersza, nie twierdzenia, że oba nagłówki są identycznym AST. P03, P05 i P06 nie zależą od tej interpretacji. P01/P02/P10 są kontrolami. Siedem niezgodności nie oznacza siedmiu niezależnych defektów ani estymacji częstości błędu.

### E2. Scenariusze agentów — nadal HYPOTHESIS

| Scenariusz | Poprawne zachowanie do porównania |
| --- | --- |
| Literówka / inert report | Właściwy scope, krótka inspekcja i wymagane checks; bez nowego programu i niepowiązanego E2E |
| Migracja danych | Lokalna authority, zgodność/rollback, negatywne testy; production approval osobno |
| Zmiana UI | Odpowiednie testy i rzeczywiście obejrzany obraz; Atlas freeze blokuje nieautoryzowany runtime |
| Failing test | Nowa hipoteza i targeted repair; brak identycznego retry-until-green i sztucznego BLOCKED |
| Deployment | Przygotowanie dozwolone, oddzielna zgoda na chronioną operację; merge nie jest deployment proof |
| Wieloplikowe zadanie | Tylko korzystna delegacja, jeden writer na lane, poprawna integracja i durable handoff |

Nie uruchomiono tych sześciu scenariuszy na modelach ani porównania A/B.

## F. PROPOSED EDITS AND COST MODEL

### F1. Najmniejszy sensowny zakres zmian

| Obszar | Propozycja | Dowód zachowania funkcji |
| --- | --- | --- |
| V `central_agent_policy.py` i istniejące testy | D15/D19; doprecyzowanie D20 | Corpus dopuszczalnych i zakazanych tekstów; osobne ancestry/protection facts |
| G review prose/prompts | D1 | Jedna authority review; zachowana niezależność i metered-use boundary |
| P root/bootstrap/router | D6/D7/D18 | Ładowanie właściwych instrukcji i ten sam zestaw safety decisions |
| G/P jawny binding i lokalne reguły | D3/D5/D9 | Serial bez wyjątku; retry bounded; brak fałszywych stopów |
| G aktywne checkpointy | D4 | Terminal lifecycle i release przed usunięciem z dispatch |
| A maintenance document | D10/D11 | Zgodność z live context; freeze i protected-base validation bez zmian |
| Profile wykonania i task prompts | D2/D8/D12/D13 | Brak zbędnych handoffów i ładowania; domain acceptance zachowane |
| Game CI | D14 — osobny zakres | Pełny synthetic diff, fail-closed unknown, real PR/MQ canary |

Atlas `allowedNormal()` dopuszcza odpowiednie A/M/D pod `docs/agents/`, więc sam plik binding JSON nie jest zakazany przez rozszerzenie. Nie oznacza to zgody na uruchomienie nowego workflow, candidate executable ani zmiany immutable maintenance validatora. Adopcja dokumentów i aktywacja nowego enforcementu muszą mieć właściwy zakres.

### F2. Co mierzyć zamiast zgadywać oszczędności

Podstawowa miara: koszt zasobów na zaakceptowane, poprawnie zakończone zadanie. Raportować osobno powodzenie, fałszywe blokery i naruszenia safety, żeby spadek kosztu przez porzucanie pracy nie wyglądał jak sukces.

| Wymiar | Pomiar |
| --- | --- |
| Kontekst | Faktycznie loaded bytes/files i powtórne odczyty; input/cached/output/reasoning tokens wyłącznie z dostępnej telemetryki |
| Koordynacja | Liczba handoffów, czas odbudowy kontekstu, konflikty ownership, materialnie użyte wyniki subagentów |
| CI | Job-seconds i wall time oddzielnie; cały PR/MQ/main, liczba uruchomień i rerunów |
| Funkcjonalność | Acceptance, poprawne wybory narzędzi/tests, completed tasks, fałszywe stop/approval |
| Utrzymanie | Ile aktywnych źródeł wymaga edycji przy jednej zmianie zasady; nie sama liczba wszystkich plików |

FACT: odczyt timing historycznego Game run `33973093609` zwrócił `run_duration_ms: 550000` i `billable.total_ms: 0` dla obu platform. Jobs endpoint potwierdził sześć zakończonych sukcesem jobs. To 9 min 10 s czasu runu, nie pomiar bieżącej średniej, nie suma job-seconds i nie dowód kwoty oszczędności.

UNKNOWN: rachunki i efektywne stawki, token telemetry użytkownika, obecny cache-hit rate, reprezentatywny rozkład zadań, kontrolne czasy przed/po i koszt ludzkiej obsługi. Bez nich nie podajemy procentu ani kwoty. Zasady cache API nie dowodzą analogicznej oszczędności limitu subskrypcji ChatGPT [O4].

RECOMMENDATION: reuse niezmiennych źródeł oraz ograniczone wyniki narzędzi, zamiast ponownego pobierania dużych plików. W API stabilne wejście może pomagać w cache, ale cenę i cache-write/read należy sprawdzić w rzeczywistym użyciu. Nie utrzymywać zbędnych instrukcji tylko dla trafień cache.

## G. SMALLEST USEFUL CLEANUP BATCH

**Pakiet 1 — poprawność i jednoznaczność:** w istniejącej pracy #142/#145 naprawić D15/D19, ustalić zakres D20 i acceptance D21. Oddzielnymi autoryzowanymi zmianami usunąć wycofany kontroler Game oraz poprawić maintenance prose Atlas. Nie otwierać równoległej konkurencyjnej implementacji centralizacji.

**Pakiet 2 — mniej obowiązkowej pracy:** po scaleniu centralnej authority przyjmować jawny binding produktu i równocześnie wycofywać powielone obowiązki. Priorytet P root/bootstrap i loader; następnie delegacja, kontynuacja, review-delta i checkpointy. Zachować działanie już przydzielonych zadań oraz właściwe lokalne invariants.

**Pakiet 3 — optymalizacja kosztu wykonania:** osobno porównać effort/delegację i routing CI. Nie mieszać w jednym eksperymencie nowego modelu, nowych instrukcji, mniejszego effortu i ograniczenia testów. Atlas restoration pozostaje osobnym zadaniem maintenance, nie efektem ubocznym cleanupu.

Nie dodawać centralnego mega-promptu, nowego orchestratora, obowiązkowego LLM-review każdej zmiany, drugiego statusu merge, automatycznych exceptions dla numerów PR ani stałego pełnego audytu całej organizacji przy każdym aliasie.

## H. VALIDATION PLAN AND CONCLUSION

**Wykonano:** inspekcję źródeł z B, 10 deterministycznych prób z E, arytmetyczne porównanie rozmiarów loadera oraz odczyt historycznego CI. Nie uruchamiano produktowych testów ani ręcznie workflow; zwykła publikacja aktualizacji raportu może uruchomić istniejące CI.

**RECOMMENDATION — walidacja etapowa:** najpierw istniejąca lokalna suite walidatora z kontrolami dodatnimi/ujemnymi. Następnie mały, uprzednio autoryzowany canary instrukcji: dokumentacja, diagnostyka awarii i zadanie wysokiego ryzyka w środowisku testowym. A = obecne instrukcje; B = jeden cleanup batch; ten sam snapshot/model/effort/narzędzia/acceptance. Powtarzać próby tam, gdzie zmienność lub ryzyko wymaga mocniejszego dowodu; nie tworzyć domyślnej wielkiej macierzy na każdy drobny edit.

Akceptacja: mniej zbędnego czytania, koordynacji lub uruchomień przy zachowaniu poprawności i kompletności. Zero tolerancji dla nieautoryzowanych operacji, fałszywego PASS i pominięcia safety invariant. W razie regresji przywrócić minimalny brakujący scaffold, nie całą historyczną warstwę. Kontrole wymagane przez bieżące repo pozostają obowiązkowe niezależnie od eksperymentu.

**UNKNOWN / poza zakresem:** pełne administration/branch-protection META i Platform, konfiguracja pozostałych powierzchni i skills, niewidoczne repozytoria, wszystkie lifecycle records, skuteczność modeli w A/B i rzeczywiste oszczędności finansowe. Rewizja 2 nie jest audytem bezpieczeństwa produktu ani potwierdzeniem gotowości #145 do merge.

**Wniosek:** istnieje potwierdzony dług i nowe kontrprzykłady funkcjonalne. Największa wartość pochodzi z usunięcia konfliktów i zbędnych decyzji agenta, a nie z maksymalnej redukcji długości tekstu. Uproszczenie uznajemy za wdrożone dopiero po adopcji, wycofaniu starych obowiązków i proporcjonalnym dowodzie zachowania funkcji.

### Źródła i odtwarzalność

Ścieżki w D są względne do repo i pełnej rewizji z B1. Wybrane bezpośrednie locatory:

- [M: root](https://github.com/Oteryn/Oteryn/blob/0c493896040072badeff1f333eb83d7114a993ff/AGENTS.md), [continuation JSON](https://github.com/Oteryn/Oteryn/blob/0c493896040072badeff1f333eb83d7114a993ff/ecosystem/agent-continuation-policy.json).
- [V: walidator](https://github.com/Oteryn/Oteryn/blob/697233ed2b0a6495e1c897be9b70ffc2d7ae3428/tools/governance/central_agent_policy.py), [standard promptów](https://github.com/Oteryn/Oteryn/blob/697233ed2b0a6495e1c897be9b70ffc2d7ae3428/docs/agents/policy/PROMPTING_STANDARD.md), [workflow](https://github.com/Oteryn/Oteryn/blob/697233ed2b0a6495e1c897be9b70ffc2d7ae3428/.github/workflows/ci.yml).
- [G: root](https://github.com/Oteryn/Oteryn-Game/blob/53c6bdf06a2282d893035a995c46052c88f935b4/AGENTS.md), [review prose](https://github.com/Oteryn/Oteryn-Game/blob/53c6bdf06a2282d893035a995c46052c88f935b4/docs/agents/OWNER_FUNDED_AI_POLICY.md), [archiwum #346](https://github.com/Oteryn/Oteryn-Game/blob/53c6bdf06a2282d893035a995c46052c88f935b4/docs/agents/tasks/archive/OTV2-20260906-native-evidence-wire-346.md), [macierz CI](https://github.com/Oteryn/Oteryn-Game/blob/53c6bdf06a2282d893035a995c46052c88f935b4/docs/agents/BUILD_TEST_MATRIX.md).
- [P: root](https://github.com/Oteryn/Oteryn-Platform/blob/3b2ea1c7392187d5d22488673073dc8f8305a374/AGENTS.md), [bootstrap](https://github.com/Oteryn/Oteryn-Platform/blob/3b2ea1c7392187d5d22488673073dc8f8305a374/docs/agents/PLATFORM_AGENT_BOOTSTRAP.md), [metadata agents tree](https://api.github.com/repos/Oteryn/Oteryn-Platform/git/trees/ed9899c876a2d677dbfc93ab46eea88951210e73).
- [A: maintenance document](https://github.com/Oteryn/Oteryn-Atlas/blob/51623c7dab2346cee39cd51e3caa845bf4b65426/docs/maintenance/ATLAS-MAINTENANCE-MODE.md), [validator](https://github.com/Oteryn/Oteryn-Atlas/blob/51623c7dab2346cee39cd51e3caa845bf4b65426/tools/maintenance/verify-maintenance-diff.mjs), [live ruleset 22103758](https://api.github.com/repos/Oteryn/Oteryn-Atlas/rulesets/22103758).
- [Game historyczny run](https://github.com/Oteryn/Oteryn-Game/actions/runs/33973093609), [timing API](https://api.github.com/repos/Oteryn/Oteryn-Game/actions/runs/33973093609/timing).

Dokumentacja OpenAI odczytana 2026-09-06, źródła zmienne:

- [O1: AGENTS.md discovery i project_doc_max_bytes](https://learn.chatgpt.com/docs/agent-configuration/agents-md).
- [O2: Model guidance — instruction following, testing, delegation i effort](https://developers.openai.com/api/docs/guides/latest-model).
- [O3: Skills i progressive disclosure](https://learn.chatgpt.com/docs/build-skills).
- [O4: Prompt caching API](https://developers.openai.com/api/docs/guides/prompt-caching).

Wynik publikacji, dokładny final head i jego CI należy odczytać z PR #151. Nie zapisywać przyszłego własnego SHA w tym pliku ani nie przesuwać head wyłącznie dla aktualizacji statusu.
