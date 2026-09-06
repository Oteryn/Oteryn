# Oteryn/Oteryn — kompleksowy audyt repozytorium, uzupełnienie R2

## 1. Audit status

`COMPLETE_WITHIN_ACCESSIBLE_SCOPE`

> **Publication note:** audyt jest semantycznie związany z `main@0c493896040072badeff1f333eb83d7114a993ff` (`tree=77c33f4c2d3bffcd5983e35928d870d618cb5f68`). Po zakończeniu audytu chroniony `main` przesunął się do `d0d5a54c5f06db9423d14b17e7f8eadefd15c6fb` przez PR #152. Publikacja jest oparta na późniejszym `main`, ale nie przypisuje późniejszej zmiany do zakresu audytu.

Poprzednia deklaracja zakończenia była przedwczesna. Uzupełnienie wykorzystało dostępne drogi read-only do pełnego checkoutu, wykonania aktywnych zestawów testów, odczytu ustawień GitHub, historii CI i właściwych zewnętrznych źródeł instrukcji. Kryteria zakończenia pochodzą z oryginalnego promptu audytowego.

Materiały towarzyszące:

- `COVERAGE-LEDGER.md` — 78/78 śledzonych ścieżek audytowanego snapshotu;
- `PROMPT-COMPLIANCE-MATRIX.md` — rozliczenie kontraktu zakończenia;
- `VERIFICATION-SUMMARY.md` — public-safe podsumowanie wykonanych kontroli i live-state evidence.

W trakcie audytu nie wykonywano poprawek, zmian ustawień, zdalnych write operations ani nowych testów. Publikacja raportu nastąpiła później na wyraźne polecenie użytkownika.

## 2. Repository snapshot

| Element | Zweryfikowany stan |
|---|---|
| Repozytorium | `Oteryn/Oteryn`, publiczne META |
| Audytowana gałąź | `main` |
| Audytowany SHA | `0c493896040072badeff1f333eb83d7114a993ff` |
| Drzewo | `77c33f4c2d3bffcd5983e35928d870d618cb5f68` |
| Inwentarz | 78 plików, 844 834 bajty |
| Kategorie | 53 Markdown, 14 Python, 7 JSON, 3 YAML, 1 CODEOWNERS |
| Typ | warstwa koordynacji, kontraktów i governance; nie runtime Game/Platform/Atlas |
| Technologie | Python, JSON, YAML/GitHub Actions, Git, Markdown |
| Working tree | świeży tymczasowy detached checkout; początkowo i końcowo czysty; `git fsck` PASS |

Wszystkie 78 blobów zostały porównane z tożsamościami Git; nie wykryto niezgodności. Surowe dane lokalnego hosta nie są publikowane w tym publicznym repozytorium.

## 3. Executive assessment

**INFERENCE — wysoka pewność:** granica architektoniczna META jest właściwa i nie wymaga przepisywania od zera. Repozytorium pozostaje cienką warstwą koordynacji, nie kopiuje provider runtime ani schematów produktów jako drugiego źródła prawdy. Bieżący `meta-gate` jest mały, szybki i zgodny z Merge Queue.

Największy dług jest skoncentrowany w pięciu obszarach:

1. nieukończone wycofanie starego systemu AI-review;
2. powielone obowiązki instrukcyjne i testy wymagające dosłownych kopii;
3. słabsza niż deklarowana walidacja przyszłych manifestów release;
4. zbyt słaba reprezentacja izolacji branch/worktree;
5. konkretne luki security/ergonomics: private vulnerability reporting wyłączone, CodeQL default setup nie skonfigurowany, jeden test CLI nieprzenośny na Windows.

Nie potwierdzono P0 ani P1, utraty danych, obejścia ochrony `main` ani awarii obecnego Linux `meta-gate`.

## 4. Architecture assessment

### Kontrakty ekosystemu

`README.md`, ADR 0001/0002/0005, `ecosystem/repositories.json`, schema kompatybilności oraz dokumenty testing/release definiują odpowiedzialności czterech repozytoriów. META przechowuje koordynację i tożsamości, a provider repositories pozostają właścicielami implementacji i schematów. Ten kierunek jest odpowiedni i powinien zostać zachowany.

### Narzędzia wykonania agentów

- `agent_execution_routing.py` — walidacja preflight, execution target i lane planning;
- `remote_desktop_call_gate.py` — wiązanie dokładnego host action/tool/arguments;
- `bounded_execution_guard.py` — retry/freeze/progress semantics;
- `agent_continuation_policy.py` — walidacja continuation przez zaufane adaptery;
- `governance_drift_audit.py` — read-only porównanie obserwacji z desired state;
- `provider_policy_adoption.py` — sprawdzanie adopcji providerów.

To są walidatory/predykaty. Nie należy przedstawiać ich jako samodzielnego schedulera ani transportowego firewalla.

### CI i integracja

`.github/workflows/ci.yml` składa walidację struktury, desired state i sześć aktywnych zestawów testów w jeden zewnętrzny `meta-gate` działający dla PR i `merge_group`. GitHub jest właściwym integration authority.

### Lifecycle gałęzi

`.github/workflows/terminal-branch-lifecycle.yml` korzysta z przypiętej implementacji Platform. Odczyt/inwentarz jest oddzielony od write path, a usunięcie refa używa expected-SHA semantics. Nie znaleziono bezwarunkowego mechanizmu kasowania gałęzi po samej nazwie.

## 5. Coverage ledger

Tracked-file coverage dla audytowanego snapshotu:

- total: **78**;
- `DIRECT`: **78**;
- `GROUPED`: **0**;
- `N/A`: **0**;
- `UNVERIFIED`: **0**.

Pełne ścieżki i blob SHAs: `COVERAGE-LEDGER.md`.

| Domena | Status | Podstawa / granica |
|---|---|---|
| A Purpose | AUDITED | README, manifest, ADR-y, current work |
| B Architecture | AUDITED | wszystkie moduły i materialne zależności workflow |
| C Implementation | AUDITED | 14 Python, składnia, wykonania i dead-code review |
| D Interfaces/contracts | AUDITED | schema, JSON policy, CLI, adaptery |
| E Data/persistence | AUDITED | checkpointy, refy, recovery contract; bez produkcyjnego restore |
| F Dependencies | AUDITED | importy, Actions pins, Dependabot; brak ogólnego certyfikatu CVE |
| G Security/privacy | AUDITED | code + repository settings; bez odczytu secret values |
| H Reliability | AUDITED | retries, continuation, lifecycle, fsck, failure paths |
| I Performance/cost | AUDITED | CI history i obserwowana latencja; bez billing/token A/B |
| J Tests | AUDITED | 7 plików testowych; 6 aktywnych + 1 osierocony |
| K Build | AUDITED | repo-native validation; brak osobnego product build |
| L CI | AUDITED | workflow sources, backend records, Merge Queue, 268 runów |
| M Release/deploy | AUDITED | schema/procedure; 0 bieżących releases/tags/deployments |
| N Config/infra | AUDITED | repo config, Actions, environments |
| O Operations | AUDITED | CLI/errors/log evidence; brak usługi runtime META |
| P Documentation | AUDITED | wszystkie 53 Markdown |
| Q Instructions/skills | AUDITED | root, prompty, specs/plans, odkryte właściwe external instruction sources |
| R DX/ergonomics | AUDITED | świeży checkout, rzeczywiste komendy, portability defect |
| S Governance | AUDITED | protection, required gate, MQ, merge methods, security automation |
| T Current work | AUDITED | otwarte PR/Issues i historyczne korekty |
| U Compatibility | AUDITED | faktyczne Windows/Linux wyniki; nie pełna macierz platform |
| V User-facing quality | N/A | META nie zawiera produktu UI |
| W Simplification | AUDITED | konkretne redukcje z zależnościami |

## 6. Findings

### AUD-01 — P2 — isolation identity is under-specified

**FACT:** routing przechowuje branch i worktree w jednym polu `branch_and_worktree` i porównuje ten tekst jako całość.

**INFERENCE — wysoka pewność:** różne teksty nie dowodzą niezależnej unikalności obu współrzędnych. To luka dowodu izolacji, nie zaobserwowany konflikt pracy.

**RECOMMENDATION:** reprezentować branch i worktree osobno i walidować oba identyfikatory niezależnie.

### AUD-02 — P2 — release validation is weaker than the declared schema

**FACT:** `ci.yml` sprawdza część warunków manifestu ręcznie zamiast egzekwować wszystkie ograniczenia `compatibility.schema.json`. W czasie audytu nie było żadnego release manifestu.

**Impact:** przyszły manifest może przejść kontrolę słabszą od dokumentowanego kontraktu.

**RECOMMENDATION:** jeden walidator instancji schematu oraz odrębne sprawdzenie rzeczywistych provider evidence przed pierwszym ekosystemowym release.

### AUD-03 — P2 — orphaned AI-review compatibility code

**FACT:** `tools/governance/test_verify_ai_review_evidence_compat_v1.py` nie startuje z powodu `ModuleNotFoundError` dla usuniętego `test_verify_ai_review_evidence_core`. Powiązany adapter również odwołuje się do wycofanego core. Zestaw nie jest częścią obecnego `meta-gate`.

**Impact:** martwe wejście, myląca powierzchnia testowa i ryzyko przypadkowego odtworzenia starej architektury review.

**RECOMMENDATION:** po dependency search usunąć osieroconą parę i aktywne odwołania, zamiast odbudowywać stary system.

### AUD-04 — P2 — tests require duplicated instruction wording

**FACT:** `test_remote_desktop_action_gate.py` wymaga tych samych canonical phrases w root instructions i centralnym kontrakcie.

**Impact:** bezpieczne uproszczenie tekstu może być odrzucane przez test mimo zachowania predykatów bezpieczeństwa.

**RECOMMENDATION:** migrować instrukcję, jej consumer i test razem; testować zachowanie/authority boundary zamiast duplikacji prozy, gdy to możliwe.

### AUD-05 — P2 — superseded execution plans retain imperative language

**FACT:** historyczne `docs/superpowers` nadal zawierają dawne `REQUIRED SUB-SKILL`, review fingerprints/attestations i inne procedury wycofane przez ADR 0005. Część aktualnych promptów zawiera także sztywne wymagania liczby agentów.

**Impact:** dodatkowy context cost i ryzyko uruchomienia starej procedury.

**RECOMMENDATION:** oznaczyć zastąpione entrypoints jednoznacznie jako historyczne, zachowując unikalne rationale.

### AUD-07 — P2 — bounded test harness is not portable to Windows

**FACT:** `test_bounded_execution_guard.py` uruchamia child process literalnym `python3`. Na badanym Windows wykonanie daje 20 PASS + 1 harness ERROR (exit 9009), podczas gdy niezmieniony test w Linux daje 21/21 PASS.

**Impact:** lokalna weryfikacja może generować fałszywą awarię i niepotrzebne reruny CI.

**RECOMMENDATION:** użyć bieżącego interpretera (`sys.executable`) i zachować Linux/Windows regression.

### AUD-08 — P2 — private vulnerability reporting disabled

**FACT:** live repository setting zwrócił private vulnerability reporting `disabled`; dokumentowany baseline organizacji oczekuje prywatnej ścieżki zgłaszania dla publicznych repozytoriów.

**Impact:** poufne zgłoszenie wymaga alternatywnego kanału, mimo że `SECURITY.md` odwołuje się do prywatnego raportowania, gdy jest dostępne.

**RECOMMENDATION:** osobna autoryzowana decyzja: włączyć GitHub private reporting albo wskazać rzeczywisty prywatny kanał.

### AUD-09 — P2 — no confirmed CodeQL/code-scanning analysis

**FACT:** CodeQL default setup był `not-configured`, endpoint analiz zwrócił brak analizy, a audytowane workflow nie zawierały CodeQL.

**INFERENCE — wysoka pewność:** w badanym stanie nie ma potwierdzonego repozytoryjnego code scanning dla Python/Actions. Niewidocznego zewnętrznego skanera nie wykluczono.

**RECOMMENDATION:** ocenić minimalny skan Python/Actions, niekoniecznie jako nowy required status.

### P3 findings

- **AUD-06:** capability mapping jest miejscami zbyt związane z nazwami konkretnych powierzchni Work/Codex; oddzielić capability od execution profile.
- **PR151-01:** alias instruction-debt audit kopiuje zmienny zakres raportu i może się zestarzeć; preferować referencję do revision/registry.
- **PR151-02:** wcześniejszy raport opisuje pakiet prób bez jednoznacznego trwałego locatora w publikowanej części; uzupełnić reprodukowalność.
- **PR145-01:** body PR #145 opisuje historyczny SHA jako current; oddzielić historyczne TDD evidence od live HEAD.

## 7. Tests, CI and build assessment

### Faktycznie wykonane repository-native tests

| Zestaw | Wynik |
|---|---|
| `test_agent_execution_routing.py` | PASS |
| `test_remote_desktop_action_gate.py` | PASS |
| `test_merge_queue_workflow_contract.py` | PASS |
| `test_agent_continuation_policy.py` | 26/26 PASS |
| `test_agent_continuation_review_repairs.py` | 4/4 PASS |
| `test_bounded_execution_guard.py` | Windows: 20 PASS + 1 harness ERROR; Linux: 21/21 PASS |
| `test_verify_ai_review_evidence_compat_v1.py` | import error przed testami; poza aktywnym gate |

Wykonano również niezmienione bloki walidacyjne `ci.yml`, parsowanie JSON/YAML, składnię Python, schema declaration check oraz ograniczony Ruff; wyniki PASS. Szczegóły: `VERIFICATION-SUMMARY.md`.

### CI history

W audytowanym okresie uzgodniono 268 workflow runów. Dla bieżącego `META CI`: 165 runów — 112 success, 45 failure, 8 cancelled. Wszystkie obserwowane `merge_group` dla tego workflow zakończyły się sukcesem (12/12), podobnie push (13/13). Porażki dotyczyły PR candidates, nie audytowanego `main`.

Obserwowany proxy czasu `updated_at-created_at`: mediana 12 s, p95 27 s, max 37 s. To nie jest billed duration ani CPU time. Dane nie uzasadniają wyłączania testów META jako głównej optymalizacji kosztu.

## 8. Security, reliability and performance assessment

**Verified controls:** protected `main`, jeden app-bound `meta-gate`, read-only default workflow token, admin enforcement, linear history, conversation resolution, force-push/deletion disabled, secret scanning i push protection enabled, Dependabot security updates enabled.

**Verified gaps:** private vulnerability reporting disabled; CodeQL default setup not configured; server-side `allowed_actions=all` i brak globalnego SHA-pinning enforcement, mimo że audytowane workflow korzystają z pinów SHA.

**Reliability:** bounded retries, continuation i branch lifecycle mają znaczące negative-path coverage. Historyczny lifecycle failure został zinterpretowany jako świadoma odmowa niebezpiecznego cleanupu, nie automatycznie jako flake.

**Performance:** brak dowodu CPU/RSS/network hotspotu. Mierzono tylko zachowanie i czas workflow; nie wykonywano billing/token/model A/B.

## 9. Instruction-debt assessment

W audytowanym drzewie znajduje się jeden root `AGENTS.md`, 12 promptów/aliasów oraz 18 planów/specyfikacji `docs/superpowers`. Nie ma repozytoryjnych nested AGENTS/override/SKILL.md ani hook config.

Dodatkowo rozliczono właściwe zewnętrzne instruction sources dostępne w środowisku audytu: globalne instrukcje, metadane siedmiu skills oraz pełne entrypointy `review-agent` i `openai-docs`. Dane specyficzne dla lokalnej maszyny nie są utrwalane w tym publicznym repozytorium i nie są traktowane jako repo authority.

Najważniejsze problemy:

- historyczne procedury nadal brzmią imperatywnie;
- część reguł jest kopiowana w wielu powierzchniach;
- testy utrwalają kopie prozy;
- prompt workerów miejscami nadmiernie określa execution shape zamiast celu i constraints;
- duża część wiedzy powinna być warunkowo ładowana lub mechanicznie egzekwowana, nie stale powtarzana.

**RECOMMENDATION:** model docelowy powinien być: krótki bootstrap/root, jedno źródło reguły globalnej, provider overlay tylko dla domain-specific invariants, prompt zadania jako delta, deterministic predicate w kodzie tam, gdzie wymagane jest mechaniczne enforcement.

## 10. Documentation and repository knowledge assessment

Źródła prawdy powinny pozostać rozdzielone:

- GitHub live state — PR, check, merge, protection i lifecycle;
- ADR 0001 — topology/ownership;
- ADR 0005 — obecny prosty governance target;
- provider repositories — ich implementacja i schematy;
- machine validators — rzeczywiste egzekwowane predykaty.

Największy documentation drift dotyczy historycznych planów i body PR-ów, które nadal wyglądają jak bieżące authority. Historyczne audyty powinny zachować datę/snapshot, nie być przepisywane jako bieżący stan.

W chwili końcowego odczytu audytu: #140 było closed/completed, #142 open, #102 open/reopened, #59 open. PR #151, #145, #143, #89 i #60 były otwarte. Stan ten jest historyczny względem późniejszej publikacji i nie powinien zastępować nowego live readbacku.

## 11. Governance assessment

Live readback na końcu audytu:

| Powierzchnia | Stan |
|---|---|
| protected `main` | tak |
| required gate | `meta-gate`, App 15368 |
| strict freshness | false |
| required approvals | 0 |
| CODEOWNER approval | false |
| stale review dismissal | false |
| admin enforcement | true |
| linear history | true |
| conversation resolution | true |
| force push / delete main | disabled / disabled |
| merge method | squash; merge/rebase disabled |
| auto-merge | enabled |
| delete source branch on merge | enabled |
| Merge Queue | SQUASH / ALLGREEN; build max 5; merge max 5; min 1; wait 300 s; timeout 3600 s |

Limit `maximumEntriesToMerge` nie jest sam w sobie dowodem liczby zmian w syntetycznym merge-group buildzie. Nie wykonano mutacyjnego testu bypass/direct push ani nowego canary.

## 12. Simplification opportunities

1. **Wycofać osierocony AI-review compatibility adapter/test** po dependency search.
2. **Usunąć duplikację prozy razem z testami wymagającymi duplikacji**, zachowując underlying safety predicates.
3. **Jednoznacznie oznaczyć superseded plans/specs** przy aktywnych entrypoints.
4. **Uzgodnić jeden release validator** oraz osobne identity fields dla branch/worktree.
5. **Naprawić interpreter portability** i aktualność aliasów/PR descriptions.
6. **Nie tworzyć nowego orchestration/governance subsystemu** dla problemów już pokrytych przez GitHub Merge Queue, jeden aggregate gate i istniejące validators.

## 13. Remediation roadmap

### Immediate

Brak potwierdzonego P0/P1 wymagającego awaryjnego wyłączenia CI. Nie przedstawiać historycznych SHA/raportów jako bieżącego live state.

### Near-term

- AUD-07: poprawić harness i sprawdzić Windows/Linux;
- AUD-01: rozdzielić branch/worktree identity;
- AUD-03: usunąć orphaned review compatibility path wraz z konsumentami;
- AUD-08/AUD-09: osobne autoryzowane decyzje o private reporting i code scanning.

### Medium-term

Wykorzystać istniejące #142/#145 do migracji globalnych instrukcji zamiast otwierać konkurencyjny program. Migrować source-of-truth, references i validators łącznie. Przed pierwszym rzeczywistym ecosystem release domknąć AUD-02.

### Optional

Udokumentować wspierany runtime Python, zmierzyć realny bootstrap/context cost po uproszczeniu, ocenić globalne Actions allowlist/SHA enforcement oraz intencję licencyjną repozytorium.

## 14. Unverified and inaccessible surfaces

| Granica | Wpływ |
|---|---|
| brak osobnego boolean wymogu MQ w użytym API / brak negatywnego testu wszystkich bypass paths | nie rozszerzano dowodu ponad odczytane protection + MQ + historyczne merge_group |
| efektywny instruction-loading trace we wszystkich Chat/Work/Codex clients | zbadane pliki/config nie dowodzą ładowania w każdej sesji |
| runtime schedulera continuation i transportowego RDC enforcement | testy adapterów nie są dowodem działającego schedulera/firewalla |
| bieżący restore Synology/production recovery | kontrakty/handoff nie są świeżym restore testem |
| pełna historia sekretów, każdy zewnętrzny skaner i org-wide account recovery | repo readback nie jest audytem wszystkich kont/systemów |
| billing/token/model A/B i wszystkie platformy | nie wykonano takich pomiarów |

Pełny kod Game/Platform/Atlas nie jest brakującą powierzchnią tego audytu META; ich bezpośrednio używane zależności workflow zostały skontrolowane.

## 15. Final coverage reconciliation

- **Are all tracked paths accounted for?** Tak — 78/78.
- **Are all audit domains accounted for?** Tak — A–U i W `AUDITED`, V `N/A`.
- **Are all discovered instruction sources accounted for?** Tak w odkrytym zakresie, z jawną granicą runtime loading.
- **Are all discovered active CI workflows accounted for?** Tak — źródła repo, backend workflow records i materialne reusable dependencies.
- **Are all discovered build/test systems accounted for?** Tak — sześć aktywnych zestawów wykonano; osierocone wejście również sprawdzono.
- **Are all accessible governance surfaces accounted for?** Tak w zakresie read-only; konkretne granice wymieniono w §14.
- **Did the cross-check pass identify remaining unexplored repository surfaces?** Wykrył luki wcześniejszego etapu i zostały one uzupełnione; nie pozostała nierozliczona ścieżka audytowanego `main`.
- **Is further audit work possible with the same read-only access?** Nie pozostaje znana materialna luka bieżącego snapshotu możliwa do zamknięcia tymi samymi metodami. Dalsze canary/runtime/model A/B wymagałyby innego środowiska, przyszłego zdarzenia lub odrębnej zgody.

**Wniosek:** dostępny zakres audytu został domknięty bez wdrażania napraw. Najlepszy dalszy kierunek to przyrostowa redukcja martwych mechanizmów i duplikacji, naprawa konkretnych kontraktów oraz zachowanie prostego GitHub-native modelu integracji — bez budowy kolejnej warstwy governance.
