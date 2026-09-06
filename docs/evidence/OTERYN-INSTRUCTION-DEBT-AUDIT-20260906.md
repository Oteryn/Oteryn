# Oteryn — instruction-debt audit: instruction consumers and portability

Data: 2026-09-06. Rewizja: **4**. Klasa: **AUDIT_EVIDENCE**.
Zakres: pięć widocznych repozytoriów organizacji; instrukcje, ich walidatory, zgodność z dokumentacją OpenAI i przenośność Astra–Sol.
Alias: [Oteryn: instruction debt audit](../agents/prompts/OTERYN-INSTRUCTION-DEBT-AUDIT.md).

Polecenie kontynuacji upoważnia do audytu i aktualizacji jego wyników. Publikacja ogranicza się do raportu i opisu istniejącego META PR #151. Nie wdraża polityk, nie zmienia produktów, konfiguracji modeli, workflow, ochrony, uprawnień ani produkcji. Nie uruchamia płatnych agentów ani ręcznych workflow. Alias pozostaje read-only. Wdrożenie centralizacji jest osobną pracą #142/#145.

Historia: [R0: inwentaryzacja i D1–D17](https://github.com/Oteryn/Oteryn/blob/a08e0795c49d62c5e2e33e1013444e245c661770/docs/evidence/OTERYN-INSTRUCTION-DEBT-AUDIT-20260906.md), [R2: kontrprzykłady walidatora](https://github.com/Oteryn/Oteryn/blob/91bc3d5186b133a7010e71f9e01acbd6970c1482/docs/evidence/OTERYN-INSTRUCTION-DEBT-AUDIT-20260906.md), [R3: zakres organizacyjny i przenośność](https://github.com/Oteryn/Oteryn/blob/de2f2fd42b595a81fdcb377e8230c59c6998e446/docs/evidence/OTERYN-INSTRUCTION-DEBT-AUDIT-20260906.md). R4 zachowuje identyfikatory wcześniejszych ustaleń, doprecyzowuje D18/D22 i dodaje D25–D27. Pełne wcześniejsze opisy i propozycje pozostają pod tymi niezmiennymi rewizjami.

Legenda: FACT — bezpośrednio sprawdzony tekst/wynik; INFERENCE — wniosek z dowodów; ASSUMPTION — niezweryfikowane założenie; RECOMMENDATION — propozycja; UNKNOWN — brak danych. Przewidywane oszczędności i zachowanie agentów nie są wynikami pomiaru.

## A. Executive findings

**RECOMMENDATION:** optymalizować cały koszt poprawnie zakończonego zadania: kontekst, odczyty, koordynację, CI, poprawki i udział człowieka. Nie skracać tekstu kosztem granic uprawnień lub funkcjonalności.

Ta kontynuacja ujawnia konkretną przeszkodę wdrożeniową: część narzędzi kontrolnych wymaga właśnie tych powtórzeń, które standardy promptów zalecają usunąć. Samo poprawienie Markdown nie wystarczy.

| Priorytet | Nowy lub doprecyzowany wynik | Dyspozycja |
| --- | --- | --- |
| Przed adopcją | D25: Game wymaga w root sekcji zabronionej przez centralnego kandydata; Platform wymaga kopii budżetów i statusów | Migrować dokument i jego konsumentów w jednym spójnym PR produktu |
| Średni, poprawność walidacji | D26: funkcja Platform uznaje brak katalogu oraz plik zamiast katalogu za poprawny pusty zbiór zadań | Odróżnić nieprawidłowe wejście od istniejącego pustego katalogu |
| Ograniczenie wdrożenia, nie defekt bramki | D27: Atlas maintenance nie dopuszcza nowych `.codex/**`, `.agents/**` ani zwykłych rename/copy | Rozdzielić porządkowanie dokumentów od późniejszej konfiguracji środowiska |
| Przed deklaracją kontroli kosztu | D22: domyślny model/effort podagenta nie jest nieprzekraczalnym limitem | Sprawdzić rzeczywisty wynik rozstrzygania konfiguracji i uruchomienia |
| Przed deklaracją zgodności loadera | D18/D22: Codex składa łańcuch przy starcie do katalogu roboczego, a nie automatycznie po całym repo | Sprawdzić źródła rzeczywiście załadowane dla danego zadania |

FACT: wykonano **13 ograniczonych prób offline** przepisanych funkcji: sześć dla agregacji liveness Platform, siedem dla predykatu allowlist Atlas. Dwa przypadki Platform różnią się od oczekiwania audytu. Nie jest to procent awaryjności systemu, test pełnego CI ani benchmark modeli. Źródła, granice i wyniki: E.

## B. Revisions and coverage

### B1. Odczytane rewizje

| Kod | Repozytorium / kandydat | Rewizja |
| --- | --- | --- |
| M | Oteryn/Oteryn main | `0c493896040072badeff1f333eb83d7114a993ff` |
| G | Oteryn/Oteryn-Game main | `b61f9d8cc1c0a7289ffdaf1bf4e42b851d2c0f9a` |
| P | Oteryn/Oteryn-Platform main | `3b2ea1c7392187d5d22488673073dc8f8305a374` |
| A | Oteryn/Oteryn-Atlas main | `51623c7dab2346cee39cd51e3caa845bf4b65426` |
| B | Oteryn/Oteryn-Platform-Migration-Backup-20260818 main | `6da4f83ef6a35afbab3332f90d7c7f171d23d235` |
| V | META #145, otwarty Draft | `697233ed2b0a6495e1c897be9b70ffc2d7ae3428` |
| R3 | META #151 przed aktualizacją | `de2f2fd42b595a81fdcb377e8230c59c6998e446` |

Kody oznaczają dokładne rewizje przy ścieżkach w raporcie. M/P/A/B nie zmieniły się względem R3. Game jest o jeden commit dalej niż R3 `d12b26815d9569c52920d96affdd4a5eb872b8ec`. Porównanie zawiera cztery ścieżki: live allocations, checkpoint koordynatora, packet #353 i jego plan. Nie zmienia promptów, AGENTS ani workflow. Nie należy na tej podstawie ponownie ogłaszać zamknięcia wszystkich dawnych checkpointów.

META branch metadata potwierdza `protected: true`. #151 jest otwartym Draft na `docs/instruction-debt-audit-20260906`; dyskusja Issue/PR zwróciła pustą listę komentarzy. Te odczyty nie zastępują osobnego sprawdzenia reviews i wszystkich warunków przy ewentualnej integracji. Ta aktualizacja nie wykonuje integracji.

### B2. Faktyczny zakres R4

Odświeżono refs pięciu znanych repozytoriów, #151/#145, porównanie Game i istotne drzewa/katalogi Platform. Nie powtarzano całej enumeracji organizacji: pięć widocznych repozytoriów i pusta następna strona są dowodem R3, nie dowodem administracyjnym braku innych prywatnych repozytoriów.

Bezpośrednia inspekcja objęła 14 różnych źródeł instrukcji/kodu/workflow wymienionych w H; część dużych plików czytano zakresami, co jawnie zaznaczono. Raport R3 sprawdzono osobno. Wyszukiwanie kodu służyło tylko do odnalezienia ścieżek; materialne źródła odczytywano po SHA. Oficjalne materiały OpenAI sprawdzono ponownie w zakresie potrzebnym dla nowych zaleceń.

R0: 345 plików i 122 prompty pozostają historyczną inwentaryzacją. R4 nie jest ponownym pełnym review tych plików ani całego kodu produktów. Dotychczasowe ustalenia zachowano tylko w zakresie wskazanych niezmienionych źródeł; indywidualne stany dawnych Issues nie zostały ponownie rozliczone.

### B3. Dostęp i granice

Sandbox nie mógł rozwiązać adresu sieciowego podczas próby pobrania publicznego źródła. Odczyty repozytoriów wykonano działającym konektorem GitHub. Ograniczenie nie oznacza read-only GitHub; uprawniony zapis raportu ma osobny kanał.

Nie uzyskano rzeczywistego zestawu instrukcji ładowanych w każdej instalacji użytkownika, jego konfiguracji globalnej, aktywnych skilli/hooków, telemetrii tokenów i kosztów, ani pełnej administracyjnej konfiguracji organizacji. Nie używano Remote Desktop jako obejścia. Brak inspekcji tych elementów oznacza UNKNOWN, nie dowód ich nieobecności.

## C. OpenAI comparison: actionable refinements

### C1. Wspólny rdzeń, osobne ustawienia wykonania

RECOMMENDATION: zachować jeden rdzeń celu, zakresu, wiedzy domenowej i akceptacji dla Sol i Astry. Oddzielić od niego model, klienta, parametry rozumowania, narzędzia oraz uprawnienia. Sam profil nie nadaje dostępu do repozytorium lub produkcji.

O1 zaleca audyt konfliktujących instrukcji i proporcjonalną weryfikację Astry. O2 zaleca dla Sol usuwać powtórzenia, zachowując kontekst domenowy, twarde ograniczenia, granice zgody i kryteria sukcesu. To wspiera konsolidację, nie nowy obowiązkowy zestaw nakazów w każdej roli.

W R4 źródło O2 ma jawny selektor `?model=gpt-5.6`, zamiast samego zmiennego adresu `latest-model`. Zawartość strony i wybrany model trzeba odczytać; tytuł linku nie dowodzi, który wariant został załadowany.

### C2. Model i effort podagentów: default nie oznacza ceiling

FACT, O9: przy braku ustawień podagent może odziedziczyć model i effort rodzica. Codex rozstrzyga jawne wartości uruchomienia, domyślne `[agents]` i ustawienia rodzica; plik custom agenta może je nadpisać. Udokumentowane pola to `agents.default_subagent_model`, `agents.default_subagent_reasoning_effort` i `agents.max_concurrent_threads_per_session`. Parametry konkretnego uruchomienia mogą nadpisać defaults. Work i lokalny Codex nie mają identycznych kontrolek sandboxa.

RECOMMENDATION: limit „podagenci maksymalnie Astra low/light” traktować jako osobne wymaganie kosztowe. Ustawić właściwe defaults i role, lecz potwierdzić rzeczywisty model/effort dziecka i brak drogi podniesienia ponad limit. Nie przedstawiać defaultu, deklaracji w Markdown ani liczby wątków jako dowodu nieprzekraczalnego limitu. W tej sesji takiego ograniczenia nie wdrożono ani nie zweryfikowano.

O9 opisuje Ultra jako wariant obejmujący maksymalne rozumowanie i proaktywną delegację. Dlatego sformułowanie „najwyższy dostępny” nie powinno być stałym profilem roli. Nie wykazano, że obecne prompty Oteryn uruchomiły Ultra lub spowodowały dodatkowy rachunek.

### C3. Ładowanie AGENTS i skills

FACT, O4: Codex składa łańcuch przy starcie uruchomienia, od root do bieżącego katalogu; `AGENTS.override.md` ma pierwszeństwo przed `AGENTS.md`. O4 opisuje limit 32 KiB oraz kontrolę źródeł w logach. Sama edycja pliku głębiej nie dowodzi jego obecności w początkowym łańcuchu.

D18 pozostaje warunkowe: Platform root 26 661 B + nested 8 548 B = 35 209 B. To nie zaobserwowane ucięcie ani pomiar tokenów. Przy starcie z root nested może w ogóle nie należeć do łańcucha startowego. Zadanie dotyczące głębszej ścieżki nadal musi zastosować jej właściwe instrukcje przez jawny odczyt lub zweryfikowany mechanizm klienta.

RECOMMENDATION: w małej próbie migracyjnej zapisać klienta, katalog startu, kolejność rzeczywistych źródeł oraz zastosowany model/effort. Nie wymagać wielkiego raportu przy każdym zadaniu. Nie publikować surowych logów z potencjalnie wrażliwymi danymi; wystarczy zredagowany manifest źródeł.

FACT, O5: skills najpierw udostępniają metadane, a pełne instrukcje są doczytywane po wyborze. Lista startowa Codex ma własny budżet; opisy mogą zostać skrócone, a część skilli pominięta z ostrzeżeniem. RECOMMENDATION: nie traktować przeniesienia całego governance do jednego obowiązkowego skilla jako oszczędności. Na początku opisu umieścić trafny warunek użycia; brak skilla w liście nie dowodzi jego odinstalowania.

### C4. Sol 6 i zgodność przyszłej aktualizacji

UNKNOWN: ponowne sprawdzenie oficjalnych materiałów i wyszukiwanie nie dostarczyły potwierdzonej daty Sol 6 za 2–3 tygodnie, identyfikatora modelu ani gwarancji zgodności. Zakres 20–27 września 2026 pozostaje założeniem użytkownika, nie harmonogramem OpenAI. Brak znalezionego ogłoszenia nie dowodzi, że aktualizacja nie nastąpi.

O7 nadal opisuje Astrę w ChatGPT jako GPT-6 Pro podczas rollout; nie należy utożsamiać tego z przyszłym Sol. Materiały marketingowe i wyniki wyszukiwania nie zastępują dokumentacji modelu oraz rzeczywistej dostępności konta.

RECOMMENDATION: przyszły profil zachować jako `PENDING_VERIFICATION`. Wspólne pliki MD i prompty mogą pozostać źródłem treści, lecz przejście do produkcyjnego użycia zależy od loadera, narzędzi, uprawnień i prób funkcjonalnych. Cyfra „6” nie jest testem zgodności. Nie tworzyć oddzielnej kopii całej polityki „dla Sol 6”.

## D. Findings register

### D1–D24: zachowane dyspozycje

Tabela jest aktualnym indeksem, nie deklaracją ponownego odtworzenia wszystkich dawnych prób. Pełne ścieżki, fakty i brzmienia zachowane są w R0/R2/R3. Wskazane dokumenty niezmienione po R3 pozostają dowodem; zmienne statusy zadań wymagają osobnego odczytu przed działaniem.

| ID | Problem / zachowany warunek | Dyspozycja R4 |
| --- | --- | --- |
| D1 | Wycofany kontroler review nadal w instrukcjach Game | Konsolidować także nested AGENTS i konsumentów; nie tylko jeden plik |
| D2 | Nazwa Chat/Work/Codex zastępuje sprawdzenie capability | Migrować regułę i jej schema/validator razem |
| D3 | Parallel-first i serial exception w starszych zasadach | Przy adopcji zastąpić proporcjonalną delegacją; zachować izolację writerów |
| D4 | Aktywne checkpointy a terminalne Issues | Częściowo uporządkowane; brak aktualnego pełnego licznika |
| D5 | Wyczerpanie prób mylone z brakiem zgody | Rozdzielić STALLED, WAITING_EXTERNAL i rzeczywisty BLOCKED |
| D6 | Rozbieżne reguły przyjęcia zmienionej authority | Uzgodnić kontynuację bez resetowania poprawnej pracy |
| D7 | Bootstrap Platform powtarza root i dalsze procedury | Konsolidować wraz z wymaganiami walidatora; D25 |
| D8 | Game każe zawsze czytać dokumentacyjny nested | Stosować zakres właściwy zadaniu, nie pełny pakiet dla każdej ścieżki |
| D9 | Nowy SHA powoduje zbędne pełne re-review | Oddzielić materialny zakres review od wiązania wymaganych dowodów |
| D10 | Opis maintenance Atlas rozmija się z required context | Uzgodnić dokumentację z enforcementem bez zmiany zabezpieczeń |
| D11 | Stare procedury Atlas mogą wyglądać na aktualne | Jawna dyspozycja historyczna; nie przywracać runtime podczas maintenance |
| D12 | Model i najwyższy effort zaszyte w rolach Game | Przenieść do profilu; D22/C2 precyzują dziedziczenie |
| D13 | Nakaz przeglądania wszystkich odsyłaczy | Ograniczyć do materialnych zależności; niezmienne źródła reuse po SHA |
| D14 | Koszt szerokich Game MQ lanes | Mierzyć cały PR → MQ → main; osobny pakiet CI |
| D15 | Braki centralnego sprawdzania nagłówków i parallel-first | Naprawić przed przyjęciem #145; źródło V nadal zawiera wskazaną logikę |
| D16 | Zewnętrzne skills, hooks i konfiguracje nieznane | Zachować jawny brak pokrycia, nie deklarować pełnego usunięcia długu |
| D17 | Domenowe granice bezpieczeństwa i poprawności | KEEP; nie usuwać dla krótszego tekstu |
| D18 | Warunkowe przekroczenie limitu AGENTS Platform | Sprawdzić rzeczywisty łańcuch i CWD; C3 |
| D19 | Walidator myli odwołanie/cytat/negację z nakazem | Dodać dopuszczalne przypadki, nie tylko kolejne zakazy |
| D20 | Ancestry nazwane dowodem protected-main | Doprecyzować zakres dowodu; osobny odczyt ochrony |
| D21 | Test pakietu mylony z adopcją i zachowaniem | Rozdzielić trzy rodzaje dowodu; Platform evaluator poprawnie ujawnia zero model trials |
| D22 | Przenośność modelu mylona z przenośnością środowiska | Doprecyzowane C1–C4: defaults, overrides, loader i przyszła wersja |
| D23 | Zakaz założeń obejmuje bezpieczne drobne decyzje | Pozwolić na jawne odwracalne założenia; nie domniemywać uprawnień |
| D24 | Ujednolicanie rejestrów zamiast zasad | Nie odtwarzać w Atlasie konkurencyjnego mutable lifecycle mirror |

### D25. Walidatory utrwalają powtórzenia — nowy, wysoki przed adopcją

**FACT — Game:** G `tools/agents/validate_inherited_prompt_policy.py` dopuszcza brak kopii sekcji w promptach, ale dla `AGENTS.md` i `docs/agents/GITHUB_ONLY_EXECUTION.md` nadal wywołuje stary `validate_surface_text()`. `_extract_canonical_section()` wymaga dokładnie jednej sekcji `## Remote Desktop execution routing`, a `validate_surface_text()` porównuje ją dosłownie z canonical string. G `.github/workflows/agent-governance.yml` faktycznie uruchamia ten walidator dziedziczenia.

**FACT — kandydat META:** V `ecosystem/organization-agent-policy.json` zabrania tej samej sekcji w provider overlay. V `validate_provider_overlay()` egzekwuje zakaz. Zachowanie obowiązkowego starego bloku koliduje z nową regułą; jego zwykłe usunięcie pozostawia niespełnioną starą kontrolę.

To konflikt między aktualnym konsumentem Game a przyszłym pakietem META, nie twierdzenie, że dzisiejszy main już nie przechodzi CI. Nie należy mylić go z wcześniej naprawioną wewnętrzną niespójnością dwóch walidatorów META. Samodzielny legacy CLI Game kontrolujący cztery powierzchnie nie jest w tym workflow uruchamiany jako główny validator: aktywna ścieżka prowadzi przez `validate_inherited_prompt_policy.py`.

**FACT — Platform:** P `tools/agents/policy_consistency.py::validate_policy()` wymaga kopii statusów w anti-stall, nested i bootstrap oraz kilku liczbowych reguł w bootstrapie. `_require_regex_value()` zgłasza brak zduplikowanego markera także wtedy, gdy został usunięty na rzecz jednego źródła. P `.github/workflows/agent-governance.yml` uruchamia tę kontrolę. Niektóre oczekiwania są dosłownymi fragmentami prozy; granice WWW i completion są również sprawdzane.

**INFERENCE — wysoka pewność:** migracja samych dokumentów może zostać odrzucona przez poprawnie działający według starego kontraktu walidator. To sprzężenie utrzymaniowe, nie automatycznie luka bezpieczeństwa.

**RECOMMENDATION:** w jednym PR danego produktu zmienić binding, usunąć sprzeczne kopie i przełączyć właściwy punkt walidacji. Zachować testy semantycznych granic: uprawnienia, brak obejścia, izolacja, wiarygodne dowody i odmowa niedozwolonych działań. Usunąć obowiązek wielokrotnego kodowania tej samej liczby lub zdania. Nie uruchamiać równocześnie dwóch niezgodnych kontraktów jako blocking. Nie wyłączać całego governance tylko dlatego, że potrzebna jest migracja konsumenta.

### D26. Nieprawidłowy katalog daje poprawny pusty wynik — nowy, średni

**FACT:** P `tools/agents/task_issue_liveness.py::evaluate_tasks()` iteruje tylko gdy `active_root.exists()`. Brak katalogu pozostawia pustą listę, po czym `live_valid` wynosi `errors == 0`. Zwykły plik pod tą ścieżką również nie daje elementów z `glob("*.md")` w wykonanej próbie.

Próby L01/L02 zwróciły `live_valid=true`, `errors=0`, `tasks=[]`, bez wywołania oceny zadania. Istniejący pusty katalog i katalog zawierający sam README również dają PASS; te dwa wyniki mogą być poprawne. Oczekiwanie audytu: brak wymaganego źródła inwentarza lub błędny typ ścieżki nie powinny być utożsamiane z poprawną pustką.

P `tools/agents/test_task_issue_liveness.py` zawiera pięć testów: otwarte Issue, brak pola, zamknięte Issue, numer PR zamiast Issue i błąd API. Każdy zakłada utworzony katalog; brak testu granicy katalogu w tym odczytanym pliku. Nie twierdzimy, że nie istnieje inny test w całym repo.

**Granica:** nie dowiedziono obejścia całego workflow lub merge gate. Pozostałe kroki mogą wykryć brak katalogu, zły katalog lub niespójność checkpointów. Nie zaobserwowano też brakującego katalogu na produkcyjnym main. Wniosek dotyczy kontraktu tej funkcji i jakości jej dowodu.

**RECOMMENDATION:** jawnie sprawdzić `active_root.is_dir()`; nieprawidłowe wejście zwrócić jako błąd, a dopuszczony istniejący pusty katalog jako zero zadań. Dodać małe testy regresji tych granic. Nie zastępować tego nowym rejestrem dzisiejszych Issues ani dodatkowym sieciowym odczytem dla każdej pustej ścieżki.

### D27. Plan migracji musi uwzględnić freeze Atlas — nowy warunek wdrożenia

**FACT:** A `tools/maintenance/verify-maintenance-diff.mjs::allowedNormal()` dopuszcza zmianę root `AGENTS.md`, wybrane dokumentacyjne prefiksy oraz `tools/governance/**`, ale nie `.codex/**` ani `.agents/**`. Zwykłe rename/copy są odrzucane również między katalogami dokumentacji. `tools/maintenance/**` pozostaje zamrożone. Potwierdzenie granic: A01–A07.

**RECOMMENDATION:** w obecnym Atlas maintenance przygotowywać tylko dopuszczone zmiany instrukcji i wskazań authority. Native profile/skill rollout oraz zmiany bramki odłożyć do oddzielnej, uprawnionej fazy #315. Terminalny packet usunąć z aktywnej powierzchni po sprawdzeniu lifecycle, zachowując historię; nie zakładać obowiązkowego rename do archive. Nie maskować rename jako sztucznego delete/add w celu obejścia walidatora.

Nie jest to zalecenie osłabienia freeze. ALLOW samego predykatu ścieżki nie oznacza przejścia pełnej bramki: nadal obowiązują identity, complete diff, Git mode, rozmiar i typ zawartości. Dopuszczalny plik dokumentacyjny nie nadaje dodatkowej authority.

## E. Executed probes and verification boundaries

Wykonanie: lokalny sandbox, Python 3.13.5 i Node v22.16.0, bez sieci i bez pracy na repozytoriach produktów. Przepisano dwie wskazane funkcje z odczytu konektora. Nie pobrano pełnego checkoutu. Nie są to wszystkie oryginalne testy repozytoriów.

| Próba | Wejście / zakres | Wynik | Interpretacja |
| --- | --- | --- | --- |
| L01 | Nieistniejący katalog active | `live_valid=true`, zero zadań | Kontrprzykład D26 |
| L02 | Zwykły plik zamiast katalogu | `live_valid=true`, zero zadań | Kontrprzykład D26 |
| L03 | Istniejący pusty katalog | `live_valid=true` | Kontrola dopuszczalnej pustki |
| L04 | Katalog tylko z README | `live_valid=true` | Kontrola pomijania indeksu |
| L05 | Stub oceny jednego zadania zwraca error | `live_valid=false` | Kontrola agregacji, nie test GitHub API |
| L06 | Stub oceny zadania bez error | `live_valid=true` | Kontrola agregacji, nie test otwartego Issue |
| A01 | Modify root AGENTS | ALLOW | Tylko predykat ścieżki |
| A02 | Add `docs/agents/META_AGENT_POLICY_BINDING.json` | ALLOW | Tylko predykat ścieżki |
| A03 | Add `.codex/agents/auditor.toml` | DENY | Konfiguracja klienta poza allowlist |
| A04 | Add `.agents/skills/review/SKILL.md` | DENY | Skill poza allowlist |
| A05 | Rename packetu active → archive | ERROR | Rename zabroniony |
| A06 | Modify maintenance validator | ERROR | Authority bramki zamrożona |
| A07 | Modify `src/runtime.ts` | DENY | Runtime poza allowlist |

Harness L ma jawne stuby typów i `evaluate_task`; L01–L04 w ogóle ich nie wywołują. Harness A nie uruchamia Git, nie ocenia pełnego diffu i nie wykonuje kodu kandydata. Wszystkie 13 obserwacji odpowiada odczytanej logice; tylko L01/L02 naruszają jawne oczekiwanie audytu. Siedem wyników Atlas opisuje zamierzone ograniczenia, nie siedem błędów.

Pakiet towarzyszący zawiera `probes/liveness_probe.py`, `probes/atlas_allowlist_probe.mjs`, dwa pliki wyników JSON i `probes/probe_manifest.json` z SHA-256 oraz źródłowymi blob SHA. Odtworzenie: `python probes/liveness_probe.py` i `node probes/atlas_allowlist_probe.mjs`. Skrypty powstają jako artefakty audytu, nie nowe obowiązkowe CI.

Platform `tools/validation/prompt_eval.py` zasługuje na zachowanie jawnej granicy: sprawdza tekstowe markery i zwraca `model_trials_executed: 0`. Nie należy zaliczać jego kategorii scenariuszy jako wykonanych prób modelu. Nie uruchamiano go w R4; sprawdzono implementację i jej miejsce w workflow.

Historyczne P01–P10 R2 pozostają historycznymi próbami innej funkcji. Nie dodano ich do licznika 13 i nie przedstawiono jako nowych wyników.

## F. Revised rollout recommendation for the organization

| Repozytorium | Najmniejszy spójny pakiet | Zachować / nie robić |
| --- | --- | --- |
| META | Poprawić D15/D19 i zakres D20; zdefiniować kontrakt adopcji obejmujący punkt walidacji produktu | Nie uznawać zielonego #145 za adopcję trzech produktów |
| Game | W jednym PR binding + wycofanie starego kontrolera review + migracja kontroli wymagających canonical prose | Izolacja writerów, domenowe invariants i wymagane testy pozostają |
| Platform | Konsolidacja root/bootstrap/nested wraz z `policy_consistency.py`; mały niezależny fix D26 | Nie naruszać ograniczenia WWW ani zastępować kontroli regexami „na wszystko” |
| Atlas | W dozwolonym maintenance zakresie poprawić authority pointers i opis wymaganej bramki | Bez runtime, nowych profili/skilli w zamrożonych ścieżkach i bez bypass |
| Migration Backup | Zachować dyspozycję read-only recovery/provenance | Bez „unifikacji” przez dodawanie aktywnych instrukcji lub usuwanie historii |

Najpierw poprawność istniejącego kontraktu; potem konsolidacja wraz z konsumentami; następnie mała próba zgodności na obecnych Astra/Sol. Effort, delegację i routing ciężkich testów optymalizować jako oddzielne zmienne. Oczekiwane oszczędności pozostają hipotezą do pomiaru, nie podstawą do osłabienia bramek.

Przy adopcji sprawdzić: poprawny krótki dokument przechodzi właściwy validator; brak bindingu i niedozwolone rozszerzenie uprawnień nie przechodzą; dawny sprzeczny obowiązek nie jest nadal blocking; lokalne ograniczenie produktu pozostaje. Potwierdzić normalną ścieżkę PR/MQ tam, gdzie jest wymagana. Nie tworzyć nowego stałego kontrolera orkiestracji tylko dla tego audytu.

## G. Acceptance, cost and remaining work

Sukces wdrożenia: mniej obowiązkowych źródeł tej samej decyzji, mniej nieuzasadnionych przekazań i odczytów, brak regresji poprawności i brak fałszywych blokad. Zmniejszona liczba bajtów jest metryką pomocniczą, nie dowodem lepszego działania.

Porównanie modelowe powinno zachować ten sam zakres i kryteria sukcesu. Osobno ocenić zmianę instrukcji, modelu, effortu i delegacji. Rejestrować rzeczywisty model/klienta, ładowane źródła, skuteczność, powtórzenia, udział człowieka, zużycie tokenów i koszt całej ścieżki CI. Nie przenosić kosztu PR do MQ i nazywać tego oszczędnością.

Nie wykonano: modelowego A/B, pomiaru konta, fizycznej kontroli limitu podagentów, canary adopcji produktu, pełnego repo CI ani restore backupu. Stan tych prac to NOT_EVALUATED, nie PASS. R4 kończy dodatkową partię audytu źródeł i prób, nie całe wdrożenie optymalizacji.

## H. Evidence register and conclusion

### H1. Bezpośrednio czytane źródła R4

| Kod | Ścieżka | Zakres |
| --- | --- | --- |
| M | `AGENTS.md` | Pełny odczyt |
| M | `docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md` | Odczyt; duży wynik ograniczony przez narzędzie, bez deklaracji pełnego pokrycia |
| M | `docs/agents/contracts/BOUNDED_AUTONOMOUS_EXECUTION_POLICY.md` | Pełny dostępny tekst |
| V | `ecosystem/organization-agent-policy.json` | Pełny odczyt |
| V | `tools/governance/central_agent_policy.py` | Funkcje od linii 354 do końca |
| G | `tools/agents/validate_inherited_prompt_policy.py` | Pełny odczyt |
| G | `tools/agents/validate_remote_desktop_prompt_routing.py` | Zakresy 1–240, 325–480, 620–805, 840–koniec; bez twierdzenia o pełnym code review |
| G | `.github/workflows/agent-governance.yml` | Pełny odczyt |
| P | `tools/agents/policy_consistency.py` | Zakresy 1–240 i 465–koniec |
| P | `tools/agents/task_issue_liveness.py` | Pełny odczyt |
| P | `tools/agents/test_task_issue_liveness.py` | Pełny odczyt |
| P | `tools/validation/prompt_eval.py` | Pełny odczyt |
| P | `.github/workflows/agent-governance.yml` | Pełny odczyt |
| A | `tools/maintenance/verify-maintenance-diff.mjs` | Pełny odczyt |

Bloby kluczowe dla odtworzenia: G routing `57e4717750e34b16ff296f4a84d0af90edc9a5c2`; G inherited `8bfae653d8d252fc1815cd3d88e8d1c4e450f13d`; P consistency `e7487eab7a801ca3654585d40606a55eca4b6668`; P liveness `1634a776976d231b10e8d322c49a2a1ed087eb6b`; A maintenance `714fb73fe08b7c741d606c6e5a8ecdf33a3adf10`. Źródło ma postać `repo@SHA:path`; SHA repozytoriów w B1.

### H2. Oficjalne źródła OpenAI, odczyt 2026-09-06

| ID | Źródło | Wykorzystanie R4 |
| --- | --- | --- |
| O1 | [Model guidance — Astra](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6-astra) | Konflikty instrukcji i proporcjonalna weryfikacja |
| O2 | [Model guidance — GPT-5.6](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.6) | Krótszy wspólny rdzeń z zachowaniem treści i granic |
| O4 | [AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md) | Startup/CWD, override, limit, odczyt źródeł |
| O5 | [Build skills](https://learn.chatgpt.com/docs/build-skills) | Stopniowe ładowanie i ograniczony katalog metadanych |
| O7 | [GPT-5.6 and GPT-6 Pro in ChatGPT](https://help.openai.com/en/articles/20001354-gpt-56-and-gpt-6-pro-in-chatgpt) | Rozróżnienie Astry od przyszłego Sol; rollout |
| O9 | [Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents) | Dziedziczenie i pierwszeństwo ustawień, defaults a limit |

Pozostałe O3/O6/O8 i dawne opisy są zachowane w R3; nie liczymy ich jako nowych prób zgodności. Odczyty publicznych stron są stanem dokumentacji, nie dowodem wdrożenia ustawień konta użytkownika.

**Podstawa wniosku:** dwa bezpośrednio prześledzone mechanizmy wymagające powtórzeń, dwa odtworzone przypadki błędnego pustego wyniku, siedem sprawdzonych granic allowlist oraz dokumentacja rozstrzygania profili i loadera.

**Wniosek:** kolejna zmiana powinna usuwać zbędną warstwę wraz z jej technicznym konsumentem. Wspólne prompty nie wymagają identycznej struktury wszystkich repozytoriów, a wymiana modelu nie potwierdza zgodności środowiska. Zachować bezpieczne granice i użyteczne testy, naprawić fałszywe PASS/BLOCKED i dopiero mierzyć koszt. Publikacja tego raportu nie oznacza wdrożenia optymalizacji.
