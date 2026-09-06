# Oteryn — organization instruction-debt audit and model portability

Data: 2026-09-06. Rewizja: 3. Klasa: `AUDIT_EVIDENCE`.
Zakres: wszystkie pięć repozytoriów Oteryn widocznych przez połączenie GitHub; zgodność z dokumentacją OpenAI; przenośność Astra / Sol.
Alias: [Oteryn: instruction debt audit](../agents/prompts/OTERYN-INSTRUCTION-DEBT-AUDIT.md).

To aktualizacja audytu i rekomendacji, nie wdrożenie polityk. Zapis ogranicza się do raportu i opisu istniejącego META PR #151. Nie zmienia uprawnień aliasu, repozytoriów produktowych, CI, konfiguracji modeli, ustawień ochrony ani produkcji. Nie wykonuje merge. Wdrożenie centralizacji pozostaje osobną pracą #142 / #145.

Historia: [R0 — pełna pierwotna inwentaryzacja i propozycje D1–D17](https://github.com/Oteryn/Oteryn/blob/a08e0795c49d62c5e2e33e1013444e245c661770/docs/evidence/OTERYN-INSTRUCTION-DEBT-AUDIT-20260906.md); [R2 — D18–D21 i dziesięć prób walidatora](https://github.com/Oteryn/Oteryn/blob/91bc3d5186b133a7010e71f9e01acbd6970c1482/docs/evidence/OTERYN-INSTRUCTION-DEBT-AUDIT-20260906.md). R3 zachowuje identyfikatory ustaleń, aktualizuje zakres i dodaje D22–D24. Nie przepisuje historycznych prób jako nowych wyników.

Legenda: **FACT** — bezpośredni odczyt lub wskazany wynik; **INFERENCE** — wniosek z dowodów; **HYPOTHESIS** — przewidywany, niezmierzony efekt; **ASSUMPTION** — jawne założenie; **UNKNOWN** — brak danych; **RECOMMENDATION** — propozycja. Rewizje i odczyty są snapshotem, nie gwarancją późniejszej aktualności.

## A. Executive findings

**RECOMMENDATION:** jeden model-neutralny kontrakt organizacji, lokalne niezmienniki produktów i krótkie prompty zadaniowe; osobno profil modelu i środowiska wykonania. Ten kierunek można zastosować już do obecnych Astra i Sol. Nie ma uzasadnienia, aby czekać na niepotwierdzone Sol 6 albo tworzyć drugi system instrukcji.

**FACT:** GitHub zwrócił pięć widocznych repozytoriów; następna strona była pusta. Wszystkie objęto dyspozycją w tym raporcie, łącznie z archiwalnym backupem. To nie administracyjny dowód braku niewidocznych repozytoriów prywatnych. Pełne przeglądanie całego kodu produktu nie było celem tego audytu instrukcji.

Najważniejszy problem nie polega na braku dobrych standardów. Game, Platform oraz Atlas już deklarują prompty jako różnice właściwe dla zadania. Konflikty pozostają w rootach, nested AGENTS, starszych procedurach i konsumentach standardu. Nowa polityka bez usunięcia kolidującej starej warstwy zwiększałaby złożoność. Źródła: G/P `docs/agents/PROMPTING_STANDARD.md`, A `docs/agents/DOCUMENTATION_AGENT_IA.md`, D1–D9.

| Priorytet | Wniosek | Oczekiwany efekt, nie wynik pomiaru |
| --- | --- | --- |
| Przed adopcją | D15/D19/D20/D21: poprawność walidatora, zakres dowodu i rzeczywista adopcja muszą być rozdzielone | Mniej fałszywych blokad i fałszywego poczucia zgodności |
| Wysoki | D1/D3/D5/D6/D9: usunąć konkurujące reguły review, delegacji, zatrzymania i wznowienia | Mniej powtórzeń oraz zbędnych przekazań |
| Wysoki, warunkowy | D7/D8/D18: ograniczyć obowiązkowo ładowany kontekst, sprawdzić faktyczny loader | Mniejsze ryzyko pominięcia właściwych instrukcji |
| Wysoki projektowo | D22: oddzielić model, loader, narzędzia, uprawnienia i profil wykonania | Aktualizacja modelu bez przepisywania kontraktów produktów |
| Średni | D23/D24: rozróżniać bezpieczne założenia od brakującej authority; nie narzucać wszystkim jednej bazy statusów | Zachowanie funkcjonalności zamiast upraszczania przez zakazy |
| Osobny pakiet kosztowy | D14: mierzyć całą ścieżkę PR → MQ → main | Optymalizacja CI bez pozornego przeniesienia kosztu do kolejnego etapu |

**UNKNOWN:** nie znaleziono w sprawdzonych oficjalnych źródłach OpenAI potwierdzenia premiery Sol 6 za 2–3 tygodnie, jego identyfikatora ani zgodności wykonania. Termin 20–27 września 2026 wynika wyłącznie z założenia użytkownika liczonego od 6 września. Nie jest datą premiery. Oficjalne GPT-6 Pro w ChatGPT oznacza Astrę, nie zapowiedź Sol 6. Źródła O1–O3, O7–O8.

## B. Coverage, revisions and evidence boundary

### B1. Rewizje organizacji

| Kod | Repozytorium | Odczytany main / kandydat | Dyspozycja |
| --- | --- | --- | --- |
| M | Oteryn/Oteryn | `0c493896040072badeff1f333eb83d7114a993ff` | Centralny kontrakt i koordynacja; bez product runtime |
| G | Oteryn/Oteryn-Game | `d12b26815d9569c52920d96affdd4a5eb872b8ec` | Instrukcje Game, role, routing, domenowe AGENTS |
| P | Oteryn/Oteryn-Platform | `3b2ea1c7392187d5d22488673073dc8f8305a374` | Instrukcje WWW, bootstrap, nested, prompting i routing |
| A | Oteryn/Oteryn-Atlas | `51623c7dab2346cee39cd51e3caa845bf4b65426` | Maintenance, prompt/task authority, read-model invariants |
| B | Oteryn/Oteryn-Platform-Migration-Backup-20260818 | `6da4f83ef6a35afbab3332f90d7c7f171d23d235` | Archiwum read-only; zachować recovery/provenance |
| V | META PR #145 | `697233ed2b0a6495e1c897be9b70ffc2d7ae3428` | Nadal Draft, nie polityka wdrożona w produktach |
| R2 | META PR #151 przed tą aktualizacją | `91bc3d5186b133a7010e71f9e01acbd6970c1482` | Baza raportu, nie baza polityki organizacji |

Kody M/G/P/A/B/V przy ścieżkach poniżej oznaczają dokładne rewizje z tabeli. Locator źródła ma postać `https://github.com/<repo>/blob/<rewizja>/<ścieżka>`; dla settings i Issues użyto osobnych odczytów GitHub.

M, P, A i B nie zmieniły rewizji względem R0. Między Game R2 `53c6bdf06a2282d893035a995c46052c88f935b4` a G jest jeden commit i pięć zmienionych ścieżek: koordynacyjny rejestr i checkpoint, nowy packet/plans #353 oraz archiwizacja packetu #338. Ten delta nie zmienia AGENTS, promptów ani workflow. Pozwala zachować dowody dotyczące niezmienionych instrukcji bez ponownego pobierania każdej kopii.

### B2. Co sprawdzono i czego nie należy twierdzić

FACT — zakres R3: enumeracja repozytoriów z drugą stroną, świeże pięć refs main, stan #151/#145, porównanie Game, drzewo Game i katalog promptów Atlas, organizacyjne wyszukiwanie metadanych modeli oraz bezpośrednia inspekcja istotnych konsumentów instrukcji. Ponownie odczytano m.in. G/P standardy promptów, G/P nested dokumentacyjne AGENTS, oba domenowe AGENTS Game, G context routing i Server Seam lead, P execution routing, A documentation IA i lean canary, B recovery evidence oraz ruleset Atlas 22103758. Porównano oficjalne źródła OpenAI O1–O8.

Pozostałe niezmienione rooty, kontrakty META, validator V i szczegółowe ustalenia R0/R2 są wykorzystanymi dowodami z dokładnych rewizji, a nie deklaracją ponownego wykonania wszystkich wcześniejszych odczytów. Wyszukiwanie kodu może zwracać starszy indeks; wynik traktowano jako locator, a istotny prompt Game odczytano na G.

Historyczne liczby R0 — 345 plików, 122 prompty, osiem AGENTS, 29 aktywnych packetów, 19 promptów z profilami modeli — nie są nowym pomiarem ani liczbą wszystkich plików ponownie przejrzanych w R3. Nie przeprowadzono pełnego code review wszystkich plików, eksperymentu modelowego, audytu każdego Issue, odtworzenia backupu ani kontroli wszystkich instalacji agentów.

UNKNOWN — nie uzyskano pełnej konfiguracji Chat/Work/Codex użytkownika, globalnych instrukcji innych sesji, rzeczywiście wczytanego kontekstu, ustawień skilli/hooków, aktualnych limitów i kosztów jego konta ani pełnej administracyjnej konfiguracji organizacji. Dostęp przez GitHub nie dowodzi fizycznego egzekwowania polityki w każdym narzędziu. Brak tych danych ogranicza certyfikację wykonania, ale nie uniemożliwia audytu tekstów i ich konsumentów.

### B3. Rozmiar a rzeczywiste ładowanie

| Platform P | Bajty UTF-8 |
| --- | ---: |
| Root `AGENTS.md` | 26 661 |
| `docs/agents/AGENTS.md` | 8 548 |
| Suma root + nested | 35 209 |
| `docs/agents/PLATFORM_AGENT_BOOTSTRAP.md` | 18 025 |
| `docs/agents/CONTEXT_ROUTING.md` | 7 182 |
| Root + bootstrap + router | 51 868 |
| Powyższe + nested | 60 416 |

To rozmiary plików z GitHub, nie tokeny faktycznie zużyte. Dokumentacja O4 opisuje domyślny limit automatycznego łańcucha AGENTS 32 KiB. D18 dotyczy warunkowo 35 209 B w odpowiedniej ścieżce i konfiguracji; nie całych 60 416 B. Jawne odczyty dodatkowych dokumentów są innym mechanizmem. Nie potwierdzono ucięcia instrukcji w środowisku użytkownika.

## C. OpenAI guidance and portability assessment

### C1. Porównanie zaleceń ze stanem organizacji

| Oficjalna podstawa | Ocena Oteryn | Rekomendowana zmiana |
| --- | --- | --- |
| O1: przejrzeć konfliktujące AGENTS i skills | D1/D3/D6/D9 oraz nested Game nadal zawierają starsze rozstrzygnięcia | Jedno controlling source na decyzję; usunięcie/retirement kolidujących kopii przy adopcji |
| O1: określić follow-through i granice pytania | P nadal miesza ścisłe granice authority z ogólnymi zakazami założeń i sesyjnymi stopami | D5/D6/D23; nie zastępować false stop zasadą nieograniczonej autonomii |
| O1: delegacja, kiedy pomaga; proporcjonalne testy | G/P parallel-first; szerokie Game MQ; starsze reguły re-review | Zależność/risk routing, nie liczba agentów lub testów jako cel |
| O2: porównać dotychczasowy effort i poziom niżej przy migracji do Sol | Prompt Game żąda highest mimo standardu task-delta | Przenieść ustawienia do profilu; mierzyć, nie obniżać hurtowo |
| O3/O4: modele i konfiguracja środowiska to odrębne osie | P routing i M JSON wiążą development loop z nazwą Codex | D2/D22: sprawdzać rzeczywistą capability oraz dozwoloną operację |
| O4: ścieżkowy łańcuch AGENTS z limitem rozmiaru | D7/D8/D18 | Test loadera dla rzeczywistego klienta i katalogu; bez domniemanej cross-repo autoinheritance |
| O5: trafne metadata skilla i stopniowe doczytywanie | D16 jest historyczny i poza pełnym zakresem dostępu | Nie migrować całego governance do obowiązkowego skilla; wąskie użyteczne procedury na żądanie |
| O6: instrukcje i źródła projektu ChatGPT | Materiały repo są użyteczne, ale ich obecność nie dowodzi załadowania | Krótkie wejście wskazujące authority; odczyt właściwej rewizji zamiast uploadu całego katalogu |

OpenAI nie stanowi upoważnienia do działań w Oteryn. Ogólnego przykładu zachęcającego do samodzielnych, odwracalnych działań nie wolno używać do rozszerzenia uprawnień produkcyjnych, hostowych, sekretów ani innego repozytorium. To projektowa granica zachowana niezależnie od modelu.

### C2. Co można współdzielić już teraz

**RECOMMENDATION:** wspólny rdzeń jest uzasadniony dla obecnego Sol i Astry: cel zadania, zakres, niezmienniki domenowe, wiarygodne źródła i akceptacja nie powinny zależeć od rodziny modelu. Instrukcje powinny opisywać wynik i istotne ograniczenia, nie udawać konfiguracji klienta.

| Warstwa | Wspólna dla Astra / Sol | Co wymaga osobnego potwierdzenia |
| --- | --- | --- |
| ADR, specyfikacje, kontrakty i dokumentacja Markdown | Tak, jako treść projektu | Czy właściwe pliki i rewizje zostały dostarczone modelowi |
| Semantyczny rdzeń AGENTS | Tak, z lokalnym zakresem ścieżek | Mechanizm odkrywania, precedence, limit i faktycznie załadowane instrukcje |
| Prompt zadania / alias roli | Tak; alias nie wybiera modelu i nie nadaje uprawnień | Dostępne narzędzia oraz spełniona live allocation |
| Skill | Wspólny materiał źródłowy, kiedy procedura ma sens | Instalacja, metadata, dostępność, trafność aktywacji i narzędzia |
| Reasoning effort | Nie jako sztywny wspólny poziom | Obsługiwane wartości i jakość/koszt danej pary model–środowisko |
| Kontynuacja i pamięć | Wspólne wymaganie prawdziwego checkpointu | Faktyczny mechanizm wznowienia i kontekstu; nie sama nazwa modelu |
| Testy i completion | Wspólne kryteria poprawności | Możliwość wykonania i rzeczywisty wynik, nie worker narrative |

FACT: O3 wymienia Astrę i Sol jako modele dostępne w Codex. INFERENCE, wysoka pewność: przy tym samym kliencie, konfiguracji i katalogu reguły odkrywania AGENTS są cechą tego środowiska, a nie odrębnym formatem Markdown dla każdego modelu. Nie jest to dowód identycznych odpowiedzi obu modeli.

FACT: O8 zastrzega różnicę między wariantem Sol w Chat a wariantem API/Work/Codex. Nie należy dlatego wywodzić identyczności zachowania tylko z nazwy Sol. O6 opisuje źródła i instrukcje projektowe Chat; nie dowodzi automatycznego przejścia po lokalnym drzewie AGENTS jak w danym kliencie Codex.

### C3. Sol 6: stan wiedzy i warunkowa migracja

UNKNOWN: w O1–O3/O7–O8 i sprawdzonym wyszukiwaniu oficjalnych źródeł nie znaleziono potwierdzenia premiery Sol 6, daty 20–27 września 2026, identyfikatora, ustawień effort ani parytetu funkcji z Astrą. Pytania użytkowników na forum nie są zapowiedzią producenta. Brak znalezionej zapowiedzi nie jest dowodem, że aktualizacja nie nastąpi.

FACT: O7 opisuje GPT-6 Astra w ChatGPT jako GPT-6 Pro na kwalifikujących się planach w ramach rollout. Koryguje to starsze założenie „Astra tylko Work/Codex”. Nie potwierdza dostępności na konkretnym koncie w chwili audytu i nie oznacza Sol 6.

**RECOMMENDATION:** przygotować przenośny kontrakt teraz, lecz przyszły profil pozostawić `PENDING_VERIFICATION`. Nie wpisywać wymyślonego identyfikatora API ani daty aktywacji. Po faktycznym udostępnieniu sprawdzić dokumentację, rzeczywisty wybór modelu, loader, narzędzia, granice uprawnień i reprezentatywne zadania. Gdy te warunki są spełnione, zmiana powinna dotyczyć profilu i jedynie wykazanych regresji, nie całego katalogu promptów.

### C4. Effort, podagenci i kontekst

FACT: O1 zaleca przy migracji do Astry zachować dotychczasowy efektywny effort, a `none`/`minimal` zastąpić `low`. To nie nakaz używania najwyższego effortu. O2 zachęca do porównania ustawień na reprezentatywnych zadaniach. Nie należy utożsamiać repozytoryjnej klasy wielkości zadania `low/medium/high` z technicznym parametrem reasoning effort.

RECOMMENDATION: początkowo zmieniać jeden czynnik naraz: instrukcje, model, effort albo delegację. Podagent ma dostać najmniejszy kontekst i capability wystarczające dla niezależnego zadania. Limit jego modelu/effortu egzekwuje konfiguracja dostępnego mechanizmu, nie samo zdanie w Markdown. Brak takiego mechanizmu oznacza brak gwarancji egzekucji, a nie pozwolenie na twierdzenie, że limit działa.

O3 opisuje eksperymentalny mechanizm zarządzania kontekstem Astry w określonych klientach i warunkach. Nie zweryfikowano jego konfiguracji użytkownika. RECOMMENDATION: nie budować obowiązkowego konkurencyjnego systemu pamięci; zachować krótki stan zadania i referencje dowodów w GitHub, bo pamięć modelu nie jest aktualnym lifecycle ani uprawnieniem.

## D. Findings register and updated dispositions

Każde ustalenie poniżej jest powiązane z dokładnymi ścieżkami. Pełne pierwotne proponowane brzmienia i próby pozostają w R0/R2. Zgodność tekstowa nie jest pomiarem zachowania agenta.

### D1. Stary kontroler review — CONSOLIDATE, wysoki

G `AGENTS.md` jawnie superseduje starszy kontroler; `docs/agents/CODEX_REVIEW_POLICY.json` ma `RETIRED`. `docs/agents/OWNER_FUNDED_AI_POLICY.md` nadal stosuje stary mechanizm. Nowe potwierdzenie R3: `docs/agents/AGENTS.md`, sekcja architecture workers, nadal odsyła do standing authorization tego JSON; `prompts/OTV2_SOL_SERVER_SEAM_LEAD.md` wymaga jego odczytu. Usunąć sprzeczne routing/standing-controller treści w całym łańcuchu konsumentów, nie tylko jednym pliku. Zachować niezależność review, ograniczenia reviewer write oraz odrębną zgodę na metered use poza właściwą polityką.

### D2. Nazwa powierzchni zamiast capability — REFACTOR PROFILE, wysoki

M `ecosystem/agent-continuation-policy.json` przypisuje `software_development_loop` tylko do Codex; P `docs/agents/EXECUTION_MODE_ROUTING.md` nakazuje przekazać lokalne wykonanie z Work do Codex. R3 potwierdza to bezpośrednio. HYPOTHESIS: powoduje zbędny handoff, gdy dozwolona capability istnieje w obecnej sesji. Zmienić wspólnie schema/validator/profil i instrukcje. Etykieta Chat/Work/Codex nie jest cennikiem ani dowodem narzędzia.

### D3. Parallel-first — ADOPT THEN CONSOLIDATE, wysoki

G/P rooty nadal odwołują się do starych pinów routingu i wymagają serial exception. M i A dopuszczają proporcjonalny single agent. Nie nadpisywać przyjętej wersji polityki domysłem. Przy jawnej adopcji zastąpić przymus kryterium niezależnych prac i korzyści większej od koordynacji. Jeden writer na branch/worktree oraz lease wspólnych zasobów pozostają.

### D4. Checkpointy jako konkurujący lifecycle — RECONCILE, częściowo naprawione

Historyczna lista 13 zamkniętych Issues z R0 nie jest aktualnym licznikiem. #346 było już zarchiwizowane i released w R2. Porównanie R3 potwierdza dodatkowo przeniesienie packetu #338 do archive i pojawienie się packetu #353. Nie odświeżono wszystkich pozostałych Issues indywidualnie. Nie usuwać zbiorczo packetów tylko według historycznej listy; sprawdzić ownership i terminalność. Nie dodawać testu z zakodowaną listą dzisiaj zamkniętych Issues.

### D5. Budżet napraw mylony z koniecznością interwencji — CLARIFY, wysoki

G/P `docs/agents/ANTI_STALL_AND_EXECUTION_BUDGET.md` oraz P bootstrap: trzy repair cycles prowadzą do BLOCKED/ROTATE. Budżet identycznych nieskutecznych prób nadal potrzebny; nowa użyteczna diagnoza nie jest automatycznie brakiem zgody użytkownika. Docelowo odróżnić STALLED, WAITING_EXTERNAL i realny BLOCKED. Zachować liczniki między sesjami; nie dopuścić resetów przez zmianę narracji.

### D6. Authority dopiero w następnej invocation — CLARIFY, wysoki

P `PLATFORM_AGENT_BOOTSTRAP.md`, Authority freeze: zmiana ma działać dopiero po merge i późniejszym uruchomieniu. Pogodzić to z obowiązkiem aktualizacji materialnie zmienionej authority przed dalszą mutacją. Candidate nie nadaje sobie uprawnień. Zmiana przyjęta na protected main wymaga rozstrzygnięcia zakresu i zgodności, nie automatycznego restartu całej pracy.

### D7. Powielony bootstrap Platform — SHORTEN AS A ROUTE, wysoki koszt kontekstu

P root, `PLATFORM_AGENT_BOOTSTRAP.md`, `docs/agents/AGENTS.md` powielają capability, closeout, communication, recovery i budżety. R3: skrócenie tylko bootstrapu pozostawi wiele tych reguł w nested. Zredukować cały wybrany łańcuch; wyspecjalizowana procedura ma jednego właściciela. WWW-only, production/data/credentials i właściwe grants muszą nadal być czytelne przed działaniem.

### D8. Game nested ładowane poza potrzebą — NARROW TRIGGER, średni

G `docs/agents/CONTEXT_ROUTING.md`, Always, wymaga dokumentacyjnego nested oraz aktywnego checkpointu. R3 potwierdza. Odczytywać najbliższe instrukcje dla dotkniętych ścieżek; dokumentacyjne nested wtedy, kiedy potrzebna jest jego governance/lifecycle. Nie tworzyć programu ani checkpointu wyłącznie dla trywialnego odczytu.

### D9. Powtórne review po każdym SHA — SCALE VERIFICATION, średni

G anti-stall mówi o utracie każdego review po zmianie head, root o material risk-bearing change. Nowy head wymaga aktualnej kwalifikacji integracji i oceny delta. Powtórne niezależne review tylko gdy delta unieważnia wcześniejszy zakres lub konkretny obowiązujący kontrakt wymaga exact-head review. Nie przenosić historycznego CI jako dowodu nowego head.

### D10. Atlas opisuje niewłaściwy required check — UPDATE EVIDENCE, wysoki

A `AGENTS.md` i `docs/maintenance/ATLAS-MAINTENANCE-MODE.md` zawierają starszy opis atlas-gate. Świeży ruleset 22103758 wymaga `Merge authority audit / protected-base validate` i Merge Queue. Job atlas-gate nie jest synonimem required status. Dokument nadal opisuje Stage B jako kandydata, choć ten main ma inventory trzech workflow po cutover. Uzgodnić opis, nie rozluźniać enforcementu. Ruleset pokazuje również PR-only bypass actor; jego techniczna obecność nie jest upoważnieniem do użycia w tym audycie.

### D11. Historyczne Atlas E2E obok maintenance — ON DEMAND, średni

A root, `docs/testing/ATLAS-VERIFICATION-PLATFORM.md` i historyczne prompty zachowują procedury runtime/E2E. Maintenance ogranicza ich aktywację. Przyszła restoration musi jawnie wskazać właściwy kontrakt i etap; stare instrukcje nie włączają testów ani deploymentu. Zachować rozdzielenie verification breadth od `qualification_fixture` / `bounded_real_world` / `real_fullworld`.

### D12. Model i effort w rolach — MOVE TO PROFILE, wysoki dla migracji

R3 odczytał na G `OTV2_SOL_SERVER_SEAM_LEAD.md`: GPT-5.6 Sol i `extra-high_or_highest_available`; polecenie roli nie zmieniło się z ruchem main. Nie traktować historycznego operatora Sol jako selektora modelu. Zachować aliasy, scope, allocation i akceptację; wersję, effort i fallback przechowywać w cienkim profilu. Nie wprowadzać przyszłego Sol 6 bez identyfikatora i testu dostępności.

### D13. Rekurencyjny przegląd wszystkich odsyłaczy — NARROW TRIGGER, średni

G `docs/agents/AGENTS.md` wymaga every referenced file. R3 ponownie potwierdza. Przeglądać zmienioną politykę, bezpośrednich konsumentów i zależności istotne dla authority, safety lub zgodności. Rozszerzać przegląd po odkryciu konkretnej zależności, nie odtwarzać całego grafu przy każdej korekcie.

### D14. Game MQ pełniejsze niż PR — SEPARATE CI WORK, koszt niezmierzony

G `docs/agents/BUILD_TEST_MATRIX.md`: impact routing PR/main, pełny zestaw MQ. Przyszła optymalizacja musi korzystać z kompletnego synthetic-group diff, chronionej authority i fail-closed FULL przy nieznanym wpływie. Mierzyć razem PR, MQ i post-merge. Nie usuwać PG/SIM/security na podstawie samej etykiety docs i nie utożsamiać zaplanowanych oszczędności z wynikiem.

### D15. Dwa braki walidatora V — FIX BEFORE ADOPTION, wysoki

V `tools/governance/central_agent_policy.py`: literalny substring nie normalizuje whitespace; task prompt nie używa kontroli parallel-first obecnej dla overlay. Head V nie zmienił się od R2. Naprawa musi obejmować również D19, a nie tylko zwiększyć liczbę odrzuceń. Istniejący zielony meta-gate nie dowodzi pokrycia brakujących przypadków.

### D16. Zewnętrzne skills/harness — OWNER-CONFIG FOLLOW-UP, nieponowiony

Ustalenia R0 o overlap skill-creator, dużych entry points i szerokiej aktywacji dotyczą wcześniejszej powierzchni wykonania, nie repozytoriów Oteryn. R3 nie potwierdza stanu tych instalacji. Zastosować O5 po odczycie konkretnego środowiska; nie odinstalowywać ani nie tworzyć zamiennika na podstawie historycznego katalogu.

### D17. KEEP — wymagania chroniące funkcjonalność i bezpieczeństwo

Zachować authorization i ownership, brak samonadawania authority przez candidate, GitHub lifecycle, niezależne aktualne Game fencing, recovery i trwałe mutacje. R3 odczytał `apps/game-server/AGENTS.md` oraz `crates/simulation-determinism/AGENTS.md`: zawierają istotne lokalne granice, a nie uniwersalny boilerplate. Zachować rozdział czasu/RNG/protocol/persistence, Atlas Game-owned World/Content, provenance, właściwe browser evidence i deployment boundaries. Nie usuwać recovery backupu, historii, właściwych regresji ani rzeczywistych bramek tylko dla redukcji bajtów.

### D18. Limit loadera Platform — VERIFY CONDITIONAL RISK, wysoki

P root + dokumentacyjny nested mają 35 209 B, wobec domyślnego 32 768 B w O4. Warunkiem ryzyka jest faktyczne automatyczne włączenie obu przy takim limicie. Nie ogłaszać zaobserwowanego truncation. Skrócić duplikaty i sprawdzić właściwy klient/cwd/config; samo podniesienie limitu zwiększa kontekst bez naprawy sprzeczności.

### D19. Fałszywe odrzucenia poprawnych promptów — FIX CONTRACT, wysoki

R2 pokazał na skopiowanych funkcjach V, że locator do audytu review policy oraz lokalny zakaz parallel-first mogą być odrzucone, gdy nakaz parallel-first w task prompt przechodzi. Rozróżnić kontrolowaną strukturę polityki od zwykłego wskazania pliku/negacji/cytatu. Lekki linter może wyłapywać znane kopie, ale nie udawać semantycznego systemu bezpieczeństwa. Regresje dodatnie i ujemne są konieczne.

### D20. Ancestry nie dowodzi protection — NARROW CLAIM, przed adopcją

V `resolve_meta_authority_via_github` wyprowadza `merged_to_protected_main` z compare commitów. Sam ten krok nie sprawdza ochrony gałęzi. R2 osobno potwierdził protected=true w META. Rozdzielić pojęcia albo dostarczyć właściwy dowód przez istniejący odczyt kontrolny. Nie budować dodatkowej usługi atestacyjnej tylko dla tej korekty.

### D21. Bundle CI nie dowodzi adopcji ani zachowania — SEPARATE ACCEPTANCE

V `.github/workflows/ci.yml` i central validator sprawdzają pakiet META. PR #145 pozostaje META-only Draft. Adopcja providerów i modelowe canary to osobne fakty. Nie oznaczać całej organizacji jako zoptymalizowanej tylko po zielonym centralnym teście lub merge META.

### D22. Przenośność modelu pomylona z przenośnością środowiska — NEW

FACT: aktualny P routing i G prompt kodują model/surface; O3/O4/O6/O8 rozróżniają modele i konfigurację wykonania. RECOMMENDATION: wspólny rdzeń zadania, osobny model profile oraz adapter środowiska. Gwarancja wspólnego pliku MD nie jest gwarancją loadera, dostępnych narzędzi, pamięci, podagentów ani identycznych odpowiedzi. Brak opublikowanego Sol 6 uniemożliwia jego certyfikację, nie przygotowanie architektury kompatybilnej z wymianą modelu.

### D23. Każdy UNKNOWN traktowany jak brak możliwości działania — NEW

FACT: P `PROMPTING_STANDARD.md` zawiera blanket rule, aby nigdy nie przekształcać UNKNOWN w assumption; nested nakazuje m.in. jeden bounded phase per session. HYPOTHESIS: połączenie z innymi stopami może hamować nieszkodliwą pracę. RECOMMENDATION: zachować bezwzględne dowody dla permission, branch, schema, secrets, production i acceptance; dla niematerialnego odwracalnego szczegółu dopuścić jawne założenie w już dozwolonym zakresie. Nie fabrykować stanu repozytorium. Sesja może skończyć się technicznie, lecz nie jest to automatyczne ukończenie zadania ani dowód potrzeby decyzji właściciela.

### D24. Jedna semantyka nie oznacza jednej bazy statusów — NEW

FACT: G `PROMPTING_STANDARD.md` wymaga stabilnego `PROMPT_LIFECYCLE.json`; A `DOCUMENTATION_AGENT_IA.md` zabrania odtwarzania mutable prompt/task mirror i przypisuje lifecycle Issues. `ATLAS-LEAN-PROMPT-CANARY.md` jawnie zachowuje ten model. RECOMMENDATION: centralizacja nie może wymuszać nowego rejestru Atlas tylko dla symetrii plików. Stabilny katalog wykonawców i zmienny status zadania to różne rzeczy. Weryfikować unikatowe authority i niedispatchowalność historii; status czytać z GitHub.

## E. Repository-by-repository action matrix

| Repozytorium | Potwierdzony obraz | Najmniejszy użyteczny pakiet | Zachować / acceptance |
| --- | --- | --- | --- |
| META | Dobry docelowy kontrakt V, ale jeszcze Draft; capability enum i walidator wymagają korekt | W istniejącej pracy #142/#145 naprawić D15/D19/D20, dodać D22 jako cienki profil, nie kolejną orkiestrację | Kontrola pinów i authority; dodatnie/ujemne przypadki legalnych promptów; brak provider-write z samego META |
| Game | Standard jest lean, konsumenci nadal mają stare review/effort/parallel-first; nested i routing poszerzają odczyty | Przyjąć merged binding i usunąć kolidujące instrukcje w root + nested + OWNER policy + rolach; oddzielnie uporządkować aktywne cache po live closeout | Session fencing, recovery, native/protocol/determinism, prawdziwe PG/SIM i niezależne high-risk review; nie rozbić aktywnych allocations |
| Platform | Standard task-delta, lecz duży root/bootstrap/nested oraz stare mode/stop semantics | Skrócić cały łańcuch; zmienić routing na capability; ujednolicić continuation i ostrożne assumptions; nie usuwać specjalizacji bezpieczeństwa | WWW-only, auth/payments/data, production permissions, pełne wymagane feature acceptance; wykazać rzeczywisty loaded chain |
| Atlas | Registry-free IA już realizuje ważne uproszczenie; maintenance prose nie zgadza się z required check | Poprawić aktualny opis maintenance i odziedziczyć wspólną politykę bez kopii; historyczne E2E ładować tylko w autoryzowanej restoration | Freeze i protected-base validator, Game truth/provenance, brak deploymentu; osobne shadow/canary przed test restoration |
| Backup | Repo jest archived, recovery text odróżnia historyczny cut od produktu | KEEP; wyłączyć z rutynowego dispatchu rozwojowego, czytać tylko dla recovery/provenance | Nie usuwać release/history ani odtwarzać na canonical Platform bez jawnego incydentu recovery |

To pięć repozytoryjnych dyspozycji, nie pięć nowych projektów. Własność aktywnych prac trzeba sprawdzić przed wdrożeniem każdego pakietu. Nie ma potrzeby tworzenia kolejnych programów audytowych, agentów zatwierdzających lub statusów merge.

Przydatne wzorce do zachowania: G/P minimal prompt contract, A czterosekcyjny lean canary, M proportionate single_agent oraz wąskie domenowe nested Game. Problem rozwiązuje adopcja i usuwanie zbędnych kopii, nie nowy dokument o tym samym tytule w każdym repo.

## F. Proposed execution contract and migration plan

### F1. Wspólny kontrakt, cienkie profile

RECOMMENDATION — zawartość ról: wynik, dozwolony zakres, istotne locators, lokalne constraints/dependencies, dowód akceptacji oraz prawdziwy stop/handoff. Pomijać puste sekcje. Nie kopiować polityki routingu, review, retries i merge do każdej roli.

Profil wykonania zawiera jedynie wybrany, rzeczywiście dostępny model, klient/surface, effort, wymagane capabilities oraz dopuszczalny fallback. Nie przechowuje kopii zasad uprawnień. Stabilne aliasy `Oteryn: sol ...` mogą pozostać jako historyczne identyfikatory ról. Nowa wersja modelu nie zmienia allocation ani acceptance.

Adapter środowiska ma zapewnić właściwe źródła: w Codex prawidłowe AGENTS/path/config, w Chat projektowe wejście i jawny odczyt wymaganych repo files, w Work sprawdzone narzędzia i uprawnienia. Nie implikuje to budowania nowego oprogramowania; najpierw wykorzystać istniejące mechanizmy klienta. Immutable treści można ponownie używać po repo/path/SHA; mutable task/head/checks odświeżać wtedy, kiedy mogą zmienić decyzję.

### F2. Kolejność wdrożenia

1. **Correctness:** naprawy V z D15/D19/D20 i ich własne testy; usunięcie sprzecznych deklaracji completion. Korzystać z istniejącego PR i właściciela. Nowy materiał audytowy nie nadaje sobie policy authority.
2. **Adopcja produktów:** dopiero merged META binding; w każdym pakiecie usunąć stare konkurujące reguły wraz z przyjęciem nowych. Platform i Game wymagają sprawdzenia aktywnych ownership; Atlas pozostaje we freeze. Nie wymuszać rejestru statusów w Atlas.
3. **Przenośność:** sprawdzić wspólny rdzeń na obecnym Sol i Astrze przy rzeczywistych klientach; potem warunkowo nowy Sol po opublikowaniu. Zachować aliasy i rollback profilu.
4. **Koszty:** osobno kalibracja effort/delegacji i osobno impact-based CI/MQ. Nie łączyć tych zmian z testami promptów w jednym wyniku, bo nie będzie wiadomo, skąd pochodzi różnica.

Jeżeli dotychczasowy tekst zawiera przydatne safeguards, nie usuwać go przed zapewnieniem jednoznacznego następcy i sprawdzeniem konsumentów. Nie zwiększać zakresu uprawnień pod pretekstem usuwania konfliktów. Nie redukować testów produkcyjnych w ramach dokumentacyjnego audytu.

## G. Validation and cost measurement

### G1. Faktycznie wykonane versus planowane

R2 wykonał dziesięć deterministycznych prób skopiowanych funkcji V: siedem rozbieżności z jawnym oczekiwaniem audytu, trzy zgodne kontrole. Wyniki P01–P10 i metoda pozostają w R2 oraz dołączonym historycznym pakiecie. To nie 70% awaryjności modelu, nie uruchomienie całego repo ani proof poprawki V. R3 ich nie powtarza jako nowego eksperymentu.

R3 wykonuje inspekcję opisanych źródeł, porównanie wersji i walidację samego deliverable. Nie uruchomiono nowych product tests, model A/B, płatnych podagentów, ręcznego dispatchu CI ani restore backupu. CI automatycznie wywołane publikacją raportu trzeba ocenić na dokładnym final head; jego wynik zostaje w PR/readback, nie jako samoreferencyjny commit w raporcie.

### G2. Bounded canary dla obecnych i przyszłych modeli

RECOMMENDATION — osiem przypadków: drobna dokumentacja; read-only audit z odwołaniem do policy; naprawa jednostkowa; mała wieloplikowa implementacja; migracja danych; UI z rzeczywistym browser proof; zmieniony upstream i wznowienie; fałszywa instrukcja/nieautoryzowany cross-repo lub production request. Używać adekwatnych przykładów Game/Platform/Atlas, nie trzech kopii tego samego technicznego testu.

Najpierw porównać stare i uproszczone instrukcje przy tym samym modelu, kliencie, źródłach, effort i acceptance. Dopiero osobno porównać modele/effort. Dla zachowania niedeterministycznego minimum trzy powtórzenia na wariant może być małym canary, lecz nie statystyczną certyfikacją niezawodności. Nie uruchamiać całej macierzy wszystkich kombinacji z góry; rozszerzać tylko komórki z ryzykiem lub rozbieżnością.

Akceptacja: zachowane wymagane funkcje i invariants, brak nieautoryzowanej operacji/fikcyjnego PASS, poprawny loader i źródła, mniej niepotrzebnych pytań/odczytów/handoffów przy niegorszym wyniku zadania. Nierozwiązana regresja bezpieczeństwa blokuje daną adopcję, nie uzasadnia osłabienia orakla.

### G3. Ekonomia

Miarą docelową jest koszt poprawnie zaakceptowanego zadania. Zapisywać faktycznie udostępnione telemetryczne tokens, liczbę wykorzystanych versus zbędnych odczytów, retry i handoff, czas pracy człowieka, runner-seconds dla PR/MQ/main oraz efekt końcowy. Rozmiar Markdown jest wskaźnikiem wejścia, nie rachunkiem za model.

Nie przeliczać nazw trybów Chat/Work/Codex na pieniądze bez aktualnego planu i telemetryki. Czas kalendarzowy workflow, suma czasów jobów i naliczone koszty to różne dane. Brak billing data nie oznacza darmowego wykonania. Nie ogłaszać procentowej oszczędności z samego usunięcia plików.

### G4. Warunek aktywacji przyszłego Sol

Profil przyszłego Sol może opuścić `PENDING_VERIFICATION` dopiero po potwierdzeniu: rzeczywistego modelu/wersji w używanym środowisku; dokumentacji loadera i capabilities; poprawnej aktywacji instrukcji; wyników reprezentatywnych przypadków oraz zachowanych uprawnień i acceptance. Sama data lub cyfra 6 nie spełnia żadnego z tych warunków. W razie regresji przywrócić poprzedni profil lub minimalną instrukcję naprawiającą wykazany problem, nie pełny historyczny szablon.

## H. Conclusion, gaps and source register

Podstawa: pięć repozytoriów z jawną dyspozycją, dokładne rewizje, ponowna inspekcja istotnych konsumentów i domenowych granic, historyczne kontrprzykłady walidatora oraz porównanie O1–O8. Pozostają UNKNOWN: faktycznie ładowane instrukcje i ustawienia każdego klienta, niewidoczne repo/administration, pełne bieżące ownership, wykonanie canary, rzeczywiste koszty oraz parametry nieopublikowanego Sol 6.

**Wniosek:** wspólny rdzeń promptów i plików MD można projektować i przyjmować już dla obecnego Sol i Astry. Nie ma podstaw do obietnicy identycznego zachowania przyszłego Sol ani przeniesienia funkcji środowiska z samej nazwy modelu. Docelowa aktualizacja modelu ma być małą zmianą profilu z dowodem zgodności, nie kolejną reorganizacją Oteryn. Zoptymalizować decyzje, odczyty, koordynację i powtórzenia przy zachowaniu poprawności, funkcjonalności i granic uprawnień.

### Źródła OpenAI — sprawdzono 2026-09-06

| ID | Oficjalne źródło | Zastosowanie / granica |
| --- | --- | --- |
| O1 | [Model guidance — GPT-6 Astra](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6-astra) | Instrukcje, follow-through, delegacja, testy, migration effort; API guidance nie jest konfiguracją Chat |
| O2 | [Model guidance — GPT-5.6 Sol](https://developers.openai.com/api/docs/guides/latest-model) | Odczytany wariant strony dla Sol; URL jest zmienny, sprawdzić wybrany model przed ponownym użyciem |
| O3 | [Models](https://learn.chatgpt.com/docs/models) | Rzeczywiste modele/klienci, effort i warunkowy context management |
| O4 | [AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md) | Discovery, precedence, limit; nie dowód ustawień użytkownika |
| O5 | [Build skills](https://learn.chatgpt.com/docs/build-skills) | Metadata, wybór i ładowanie potrzebnej procedury |
| O6 | [Projects in ChatGPT](https://help.openai.com/en/articles/10169521-using-projects-in-chatgpt) | Instrukcje/źródła projektu, nie domniemana zgodność loaderów |
| O7 | [GPT-5.6 and GPT-6 Pro in ChatGPT](https://help.openai.com/en/articles/20001354-gpt-56-and-gpt-6-pro-in-chatgpt) | Astra jako GPT-6 Pro; rollout nie dowodzi dostępności konkretnego konta |
| O8 | [GPT-6 Astra: A new generation of intelligence](https://openai.com/index/gpt-6-astra/) | Opis wariantów i ograniczeń porównania; nie zapowiedź Sol 6 |

### Źródła repozytoryjne i locators

- M: `AGENTS.md`; `docs/agents/contracts/AGENT_EXECUTION_ACCESS_AND_CONTINUATION_POLICY.md`; `BOUNDED_AUTONOMOUS_EXECUTION_POLICY.md`; `PERSISTENT_AUTONOMOUS_CONTINUATION_POLICY.md`; `ecosystem/agent-continuation-policy.json`; `docs/governance/AI_REVIEW_POLICY.md`. Dla skróconych nazw kontraktów obowiązuje ten sam katalog `docs/agents/contracts/`.
- V: `docs/agents/policy/ORGANIZATION_AGENT_POLICY.md`; `PROMPTING_STANDARD.md` w tym samym katalogu; `tools/governance/central_agent_policy.py`; `.github/workflows/ci.yml`; [PR #145](https://github.com/Oteryn/Oteryn/pull/145), [Issue #142](https://github.com/Oteryn/Oteryn/issues/142).
- G: `AGENTS.md`; `docs/agents/AGENTS.md`; `apps/game-server/AGENTS.md`; `crates/simulation-determinism/AGENTS.md`; `docs/agents/{PROMPTING_STANDARD,CONTEXT_ROUTING,ANTI_STALL_AND_EXECUTION_BUDGET,BUILD_TEST_MATRIX,OWNER_FUNDED_AI_POLICY}.md`; `docs/agents/CODEX_REVIEW_POLICY.json`; `docs/agents/prompts/OTV2_SOL_SERVER_SEAM_LEAD.md`; compare `53c6bdf06a2282d893035a995c46052c88f935b4...d12b26815d9569c52920d96affdd4a5eb872b8ec`.
- P: `AGENTS.md`; `docs/agents/AGENTS.md`; `docs/agents/{PLATFORM_AGENT_BOOTSTRAP,CONTEXT_ROUTING,PROMPTING_STANDARD,EXECUTION_MODE_ROUTING,ANTI_STALL_AND_EXECUTION_BUDGET}.md`.
- A: `AGENTS.md`; `docs/agents/DOCUMENTATION_AGENT_IA.md`; `docs/agents/prompts/ATLAS-LEAN-PROMPT-CANARY.md`; `docs/maintenance/ATLAS-MAINTENANCE-MODE.md`; `tools/maintenance/verify-maintenance-diff.mjs`; [ruleset 22103758](https://github.com/Oteryn/Oteryn-Atlas/rules/22103758).
- B: `RECOVERY_EVIDENCE.md` i repo metadata archived. Nie powtórzono restore drill ani weryfikacji release asset bytes.

Wszystkie rekomendacje zachowują status dowodu audytowego. Publikacja raportu nie jest wdrożeniem optymalizacji ani przyjęciem centralnej polityki przez produkty.
