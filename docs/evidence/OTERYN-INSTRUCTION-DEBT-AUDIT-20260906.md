# Oteryn — instruction-debt audit: GPT-6 Astra / GPT-5.6 Sol

Data audytu: 2026-09-06.
Klasa: AUDIT_EVIDENCE — propozycje do przeglądu, nie polityka wykonawcza.
Alias: `Oteryn: instruction debt audit`.
Wejście aliasu: [OTERYN-INSTRUCTION-DEBT-AUDIT.md](../agents/prompts/OTERYN-INSTRUCTION-DEBT-AUDIT.md).

Audyt przeprowadzono tylko do odczytu. Późniejsze polecenie użytkownika upoważniło do zapisania raportu i aliasu w META; nie upoważniło do wdrożenia zaleceń ani zmian providerów, CI, ustawień lub produkcji. Stan opisany poniżej jest snapshotem audytu, nie obietnicą aktualności przy kolejnym użyciu. Przed decyzją odśwież tylko materialne, zmienne fakty.

Legenda:
- FACT — bezpośrednio potwierdzone treścią lub odczytem GitHub.
- HYPOTHESIS — przewidywane zachowanie, nie rezultat wykonanego scenariusza.
- UNKNOWN — brak danych lub dostępu.
- RECOMMENDATION — proponowana zmiana.

## A. EXECUTIVE FINDINGS

Audyt systemowy objął wszystkie pięć repozytoriów Oteryn widocznych przez połączenie GitHub. Największy pozostały dług wynika z równoległego utrzymywania nowych zasad i starszych instrukcji wykonawczych. Usunięcie Superpowers nie rozwiązało tych konfliktów.

FACT — zakres dowodów: pełne, nieucięte drzewa pięciu repozytoriów; wszystkie osiem znalezionych AGENTS.md; 122 pliki promptów; 29 plików aktywnych checkpointów; główne polityki, programy i definicje workflow. Łącznie pobrano 345 różnych plików repozytoryjnych. Duże kolekcje objęto inwentaryzacją, przeszukaniem treści i szczegółową inspekcją istotnych fragmentów. Nie jest to pełne code review każdego pliku.

| Priorytet | Potwierdzony problem | Znaczenie |
| --- | --- | --- |
| Wysoki | Game zachowuje instrukcje starego kontrolera review, choć root i JSON go wycofały | Sprzeczne wymagania i dodatkowe rozstrzyganie authority |
| Wysoki | META wiąże software_development_loop wyłącznie z codex; Platform kieruje implementację z Work do Codex | Możliwe niepotrzebne handoffy mimo dostępnych narzędzi |
| Wysoki | Game i Platform nadal mają obowiązkowe parallel-first | Brak jednolitej, proporcjonalnej delegacji |
| Wysoki | 13 checkpointów Game w tasks/active wskazuje zamknięte Issues | Nieaktualne instrukcje wznowienia |
| Średni–wysoki | Konkurujące reguły końca, retry i oczekiwania | Możliwy przedwczesny BLOCKED lub rotacja |
| Średni–wysoki | Atlas maintenance opisuje inny required check niż live ruleset | Ryzyko oczekiwania na niewłaściwą bramkę |
| Średni | Duplikacja w bootstrapie Platform | Duży obowiązkowy kontekst |
| Średni | Model i effort w 19 promptach Game | Role związane ze starszym profilem wykonania |
| Średni | Dwa problemy walidacji w META #145 | Centralizacja nie jest jeszcze spójnie egzekwowana |

RECOMMENDATION: dokończyć istniejącą centralizację #142/#145, usunąć sprzeczne powtórzenia i uporządkować aktywne checkpointy. Nie tworzyć kolejnego systemu orkiestracji.

UNKNOWN: pełne branch protection META i Platform, konfiguracja innych instalacji Chat/Work/Codex i zewnętrznych harnessów oraz niewidoczne ustawienia organizacyjne. Nie twierdzimy, że wszystkie powierzchnie ładują identyczne instrukcje.

## B. INSTRUCTION INVENTORY

### Repozytoria i rewizje

FACT: wyszukiwanie organizacyjne zwróciło pięć repozytoriów; kolejna strona była pusta. Drugie wyszukiwanie w instalacjach potwierdziło te same współrzędne. Manifest META wskazuje cztery produkty i jeden administracyjny backup. Nie jest to administracyjny dowód braku innych niewidocznych repozytoriów prywatnych.

| Repozytorium | Badany main | Root AGENTS.md | Nested |
| --- | --- | ---: | ---: |
| Oteryn/Oteryn | 0c493896040072badeff1f333eb83d7114a993ff | 17 240 B | 0 |
| Oteryn/Oteryn-Game | 9be69b4e0a06f3978d5c5c5603ca3e5670a9f18a | 15 437 B | 3 |
| Oteryn/Oteryn-Platform | 3b2ea1c7392187d5d22488673073dc8f8305a374 | 26 661 B | 1 |
| Oteryn/Oteryn-Atlas | 51623c7dab2346cee39cd51e3caa845bf4b65426 | 22 060 B | 0 |
| Oteryn/Oteryn-Platform-Migration-Backup-20260818 | 6da4f83ef6a35afbab3332f90d7c7f171d23d235 | brak | 0 |

Nested:
- Game: apps/game-server/AGENTS.md
- Game: crates/simulation-determinism/AGENTS.md
- Game: docs/agents/AGENTS.md
- Platform: docs/agents/AGENTS.md

W badanych drzewach nie znaleziono AGENTS.override.md, repozytoryjnych SKILL.md ani typowych konfiguracji .codex/.claude/.cursor. Ustalenie nie dotyczy wszystkich historycznych branchy.

### Źródła i aktywacja

| Źródło | Aktywacja | Inspekcja i granice |
| --- | --- | --- |
| Instrukcje bieżącej sesji Work | ALWAYS ACTIVE | Dostępna warstwa sesji; nie eksport całej konfiguracji usług |
| Lokalny config.toml Codex | MODEL/EXECUTION PROFILE | Bezpieczny podzbiór bez credentials |
| Root AGENTS.md | SCOPE ACTIVE w repo | Wszystkie; GitHub, routing, review, retry i authority |
| Nested AGENTS.md | SCOPE ACTIVE dla ścieżki; czasem wymuszone routerem | Wszystkie |
| META docs/agents/contracts/* | TASK ACTIVATED; część obowiązkowa przez root | Zbadane |
| META ecosystem/*policy.json | TASK ACTIVATED / wejście walidatorów | Zbadane |
| Bootstrap i router Platform | SCOPE ACTIVE przez root | Zbadane; powielają specjalizacje |
| docs/agents/prompts/*.md | LOAD ON DEMAND / TASK ACTIVATED | 122 pobrane/przeszukane; istotne szczegółowo |
| Programy i role | TASK ACTIVATED | Dostępne programy Markdown zbadane |
| tasks/active/*.md | TASK ACTIVATED przy wznowieniu | 29 plików |
| .github/workflows/* | Zdarzenia GitHub | Definicje pobrane; istotne bramki prześledzone |
| Archiwa i evidence | LEGACY / UNCERTAIN do jawnego użycia | Inwentaryzacja, wybrane dokumenty; nie każdy historyczny plik |
| Backup RECOVERY_EVIDENCE.md | LOAD ON DEMAND przy recovery | Zbadany; nie jest product authority |
| Katalog skilli sesji | DISCOVERY METADATA | Opisy przeanalizowane |
| Wybrane SKILL.md | LOAD ON DEMAND | 8 wejść, istotne fragmenty i wybrane odsyłacze |
| Inny Chat, Codex, zewnętrzne harnessy | INACCESSIBLE / UNKNOWN | Brak pełnej konfiguracji |

FACT — rozmiary:
- Platform root + bootstrap + router: 51 868 B.
- Z Platform docs/agents/AGENTS.md: 60 416 B.
- META root + access/continuation + bounded: 46 544 B.
- Same cztery rooty: 81 398 B.

To bajty plików, nie pomiar tokenów ani oszczędności. Cztery rooty nie są automatycznie ładowane do zwykłego zadania jednego repo.

### Dostęp i enforcement

FACT:
- Game ruleset 20991995: game-gate, Merge Queue, resolution wątków, brak bypass actors.
- Atlas rulesety 22103758 i 22352928: Merge Queue oraz protected maintenance audit.
- META i Platform: branches/main/protection zwracało 403 Resource not accessible by integration.
- Puste listy rulesetów META/Platform nie dowodzą braku klasycznego branch protection.
- Archiwalny backup ma jeden plik RECOVERY_EVIDENCE.md, nie ma AGENTS.md i nie jest normative product authority.

Źródła:
- [Manifest repozytoriów META](https://github.com/Oteryn/Oteryn/blob/0c493896040072badeff1f333eb83d7114a993ff/ecosystem/repositories.json)
- [Game ruleset](https://github.com/Oteryn/Oteryn-Game/rules/20991995)
- [Atlas repository ruleset](https://github.com/Oteryn/Oteryn-Atlas/rules/22103758)
- [Atlas organization ruleset](https://github.com/Oteryn/Oteryn-Atlas/rules/22352928)

## C. PRECEDENCE / ACTIVATION MAP

### Hierarchia wspierana przez badane źródła

1. Uprawnienia/ograniczenia sesji i jawny zakres użytkownika.
2. Obowiązujący kontrakt repo i instrukcje dotyczące ścieżki.
3. Jawnie przyjęta polityka META zgodnie z adopcją providera.
4. Aktualna alokacja i kontrakt konkretnego zadania.
5. Skill/framework jako pomoc wykonawcza.
6. Historyczny prompt, checkpoint, komentarz i log jako dowód.

Nie jest to zasada „nowszy plik wygrywa”. Scope i jawne supersession są istotne. GitHub określa lifecycle, head i checks, ale dowolny komentarz nie tworzy produkcyjnych lub cross-repo permissions.

### Łańcuchy i amplifikacja

| Początek | Łańcuch | Efekt |
| --- | --- | --- |
| Platform task | root → bootstrap → router → nested → specjalizacje | Routing warunkowy, ale bootstrap już powiela wiele reguł |
| Game Server Seam | lead prompt → runbook → implementation prompt → domena → legacy review docs | Przydatna wiedza miesza się z wycofanym kontrolerem |
| Autonomous repair | nested → anti-stall → recovery → continuation → completion | Kilka źródeł decyduje o końcu i rotacji |
| Atlas UI | root → verification platform → feature contract | Maintenance freeze musi zostać zastosowany przed runtime mutation |
| Skill authoring | discovery → jeden z dwóch skill-creator → reference → installation/validation | Niejasny wybór źródła i destination |
| Browser Work | skill → runtime documentation → conditional troubleshooting | Dodatkowy kontekst; rozmiar runtime documentation niezmierzony |

### Konflikty

| Źródło A kontra B | Scope | Winner / wynik |
| --- | --- | --- |
| Game root META-owned review kontra OWNER_FUNDED_AI_POLICY.md | Review Game | FACT: root jawnie superseduje stary kontroler |
| META single_agent kontra Game/Platform parallel-first | Delegacja | UNKNOWN: stare przypięcia providerów; potrzebna jawna adopcja |
| Capability-first kontra Platform EXECUTION_MODE_ROUTING | Work z powłoką | HYPOTHESIS: zbędny handoff |
| Aktualizacja authority kontra „later invocation” | Wznowienie Platform | HYPOTHESIS: restart lub ignorowanie nowej authority |
| META review economy kontra every moved head invalidates review | Final qualification | Root supersession przemawia za material-risk rule |
| Atlas atlas-gate prose kontra live maintenance check | Integracja | Live enforcement ustala wymagany check |
| Continue kontra three repairs → BLOCKED/ROTATE | Repair | Limit próby nie dowodzi potrzeby decyzji użytkownika |
| Repo workflow kontra read-only audytu | Audyt | Read-only controlling; odkryta instrukcja nie upoważniała do zapisu |

### Authority

| Operacja | Granica |
| --- | --- |
| Read-only | Zakres przyznany; Platform dodatkowo wymaga osobnej zgody na czytanie Game |
| Local edits, branch, commit, push | Task scope, allocation i preflight; zakazane podczas audytu |
| Local tests | Ograniczenia środowiska i danych; nie są automatycznie deploymentem |
| Remote CI | Dispatch to mutacja, nie odczyt wyniku |
| Issue/PR mutation | Wymaga scope |
| Merge | Rola, checks, review i MQ; worker nie zawsze ma merge authority |
| External messages | Nie wynikają z tool access lub tożsamości roli |
| Deployment/infra/production | Osobna jawna authority |
| Destrukcja, credentials, dane | Zachować szczegółowe bramki, nie rozszerzać automatycznie |

## D. MATERIAL FINDINGS

Wszystkie proponowane teksty poniżej są RECOMMENDATION. Zachowania runtime bez wykonanej próby to HYPOTHESIS.

### D1. Wycofany kontroler review pozostaje w aktywnie wskazywanych plikach

Waga: wysoka. Evidence: mocne, bezpośrednie pliki.
Scope: Game review.
Pliki: AGENTS.md (AI review policy — META-owned), docs/agents/CODEX_REVIEW_POLICY.json, docs/agents/OWNER_FUNDED_AI_POLICY.md, docs/agents/prompts/OTV2_SOL_SERVER_SEAM_LEAD.md.

FACT: JSON ma status RETIRED i standing_review_controller: false. Markdown nadal mówi „Apply CODEX_REVIEW_POLICY.json mechanically” i CODEX_REQUIRED; lead wymaga czytania go i kopiuje kontroler. Root jawnie superseduje starsze prose.
Disposition: CONSOLIDATE.

Replacement:
> AI-review routing is inherited from the current root AGENTS.md and its adopted META policy. This document defines no separate review tiers, standing-authorization controller or required AI status. Record only task-specific risk, reviewer independence, findings and evidence. Non-review metered AI use retains its applicable task-specific authorization requirements.

PRESERVED CONSTRAINT: niezależność review, authorization wydatków poza przyjętą polityką, brak reviewer write authority.

### D2. Surface label zastępuje capability evidence

Waga: wysoka. Evidence: mocne.
Pliki: META ecosystem/agent-continuation-policy.json, tools/governance/agent_continuation_policy.py; Platform docs/agents/EXECUTION_MODE_ROUTING.md.
Fragment: software_development_loop: [codex].
FACT: Platform kieruje local execution z Work do Codex, choć centralny kontrakt mówi o dostępnych narzędziach jako capability authority.
HYPOTHESIS: niepotrzebne przekazanie z Work.
Disposition: MOVE TO EXECUTION PROFILE / CLARIFY PRECEDENCE.

Replacement:
> Select an execution surface from verified capabilities required by the next action. A surface label does not prove or exclude editing, testing, browser or persistence capability. Continue in the current authorized surface when it can produce the required evidence. Handoff only when a required capability is unavailable.

PRESERVED CONSTRAINT: brak fikcyjnych testów i trwałej kontynuacji. Zmiana JSON wymaga zgodnego walidatora i testów, nie tylko dopisania powierzchni.

### D3. Obowiązkowe parallel-first

Waga: wysoka. Evidence: mocne.
Pliki: Game i Platform root AGENTS.md; routing/delegation.
Fragmenty: „must plan parallel-first”; „Serial execution requires a recorded reason”.
Disposition: CONSOLIDATE po jawnej adopcji aktualnej META policy.

Replacement:
> Choose single_agent or parallel_when_beneficial according to the adopted META execution policy. Parallel work requires materially independent tasks and a benefit exceeding coordination cost. Record ownership and integration order when parallel lanes are used. Serial work needs no exception.

PRESERVED CONSTRAINT: jeden mutating owner na writable branch/worktree, rozdzielone ścieżki i integracja.

### D4. Aktywne checkpointy zamkniętych Game Issues

Waga: wysoka. Evidence: mocne — pliki kontra live Issues.
Scope: task resume/dispatch.
FACT: 13 plików ma nieterminalną treść mimo closed completed owner Issues:
#201, #208, #237, #250, #278, #279, #280, #281, #282, #283, #284, #285, #346.
Przykład: docs/agents/tasks/active/OTV2-20260906-native-evidence-wire-346.md ma status validating; Issue #346 closed completed.
Disposition: CONSOLIDATE.

Replacement:
> GitHub Issues own mutable task lifecycle. Active task files are recovery caches, not independent scheduling authority. After verified terminal closeout and ownership release, remove the packet from active dispatch and preserve its history. A stale packet never reopens completed work.

PRESERVED CONSTRAINT: przed przeniesieniem potwierdzić closeout i brak potrzebnej aktywnej alokacji. Historia pozostaje.

Dokładne pliki w docs/agents/tasks/active/:
- OTV2-20260826-meta-execution-routing.md
- OTV2-20260826-repair-foundation-terminal-reconciliation.md
- OTV2-20260828-remote-desktop-per-action-gate.md
- OTV2-20260828-terminal-session-replacement-allocation.md
- OTV2-20260904-authority-api-floor.md
- OTV2-20260904-authority-qualification-governance.md
- OTV2-20260904-canonical-pr-pg-sim-gate.md
- OTV2-20260904-merge-group-audit-pin-rotation.md
- OTV2-20260905-authority-invariant-harness.md
- OTV2-20260905-authority-recovery-matrix.md
- OTV2-20260905-merge-group-pg-sim-activation.md
- OTV2-20260905-risk-scoped-test-lanes.md
- OTV2-20260906-native-evidence-wire-346.md

### D5. Repair budget mylony z blockerem użytkownika

Waga: średnia–wysoka. Evidence: mocne dla tekstu; efekt hipotetyczny.
Pliki: Game/Platform docs/agents/ANTI_STALL_AND_EXECUTION_BUDGET.md; Platform bootstrap/nested.
Fragment: „After three repair cycles … return BLOCKED or ROTATE”.
HYPOTHESIS: trzecia diagnostycznie użyteczna naprawa zatrzyma zadanie mimo bezpiecznej ścieżki.
Disposition: CLARIFY PRECEDENCE.

Replacement:
> Exhausting an unchanged retry budget stops that action chain and yields STALLED; it does not by itself require user input. Continue a permitted diagnostic or repair action when materially new evidence justifies it. Preserve counters across worker rotation. Use BLOCKED only for a missing capability, information, authorization or unresolved authority decision needed for the remaining work.

PRESERVED CONSTRAINT: bounded retries, brak ukrywania failures i resetów przez rotację.

### D6. Authority freeze do następnej invocation

Waga: średnia–wysoka. Evidence: mocne.
Plik: Platform docs/agents/PLATFORM_AGENT_BOOTSTRAP.md, Authority freeze.
Fragment: authority effective po merge i „a later invocation”.
Disposition: CLARIFY PRECEDENCE.

Replacement:
> Unmerged changes cannot expand the task's own authority. After a relevant policy change reaches protected main, re-resolve its authority and applicability before further mutation. Reconciliation does not require a new invocation and must preserve unaffected work.

PRESERVED CONSTRAINT: candidate nie autoryzuje siebie; nowe safety rules są respektowane.

### D7. Duplikacja w bootstrapie Platform

Waga: średnia. Evidence: mocne; plik 18 025 B.
Plik: docs/agents/PLATFORM_AGENT_BOOTSTRAP.md.
Sekcje: Anti-stall baseline, Session recovery baseline, Terminal-only communication baseline, GitHub-only baseline.
Disposition: SHORTEN / CONSOLIDATE.

Replacement:
> Apply the task routes listed above without copying their procedures here. The selected specialist policy owns its counters, recovery fields and completion rules. This bootstrap retains repository scope, prohibition of self-authorized expansion and the distinction between capability and permission.

PRESERVED CONSTRAINT: WWW-only, production/credentials i authority fences pozostają w wejściu.

### D8. Game router ładuje nested poza zakresem ścieżek

Waga: średnia. Evidence: mocne.
Plik: docs/agents/CONTEXT_ROUTING.md, Always.
Fragment: „Read root AGENTS.md, docs/agents/AGENTS.md …”.
Nested ma 7653 B.
Disposition: NARROW TRIGGER.

Replacement:
> Read root AGENTS.md and the nearest instructions for affected paths. Load docs/agents/AGENTS.md when changing agent documentation or when the selected task lifecycle requires its checkpoint contract. For trivial work, an absent task checkpoint is not a reason to create a programme.

PRESERVED CONSTRAINT: właściwe path instructions i lifecycle.

### D9. Re-review związane z każdą zmianą SHA

Waga: średnia. Evidence: mocne.
Plik: Game ANTI_STALL_AND_EXECUTION_BUDGET.md, Final-head freeze.
Fragment: „every moved head invalidates … any required independent review”.
META economy wymaga material risk-bearing change.
Disposition: SCALE VERIFICATION.

Replacement:
> A new head requires current-head integration checks and inspection of the delta. Repeat independent review only when a material risk-bearing change makes the previous review unrepresentative, or an applicable explicit exact-head review requirement demands it. Preserve unaffected evidence with its original revision and scope.

PRESERVED CONSTRAINT: stare CI nie staje się dowodem nowego head; high-risk review zachowane.

### D10. Atlas maintenance: nazwa bramki niezgodna z rulesetem

Waga: średnia–wysoka. Evidence: mocne.
Pliki: Atlas AGENTS.md (Validation and merge), docs/maintenance/ATLAS-MAINTENANCE-MODE.md.
FACT: prose mówi „ruleset … atlas-gate”, live ruleset 22103758 wymaga Merge authority audit / protected-base validate. Job atlas-gate nadal istnieje w MQ; job name to nie to samo co required status.
Disposition: CLARIFY PRECEDENCE.

Replacement:
> During maintenance, qualify the candidate against the current protected maintenance policy and live required-workflow/status configuration. At this revision, the repository ruleset requires Merge authority audit / protected-base validate; the merge-group workflow also defines atlas-gate. Do not infer required status contexts solely from job names. Runtime verification and deployment remain suspended until the authorized restoration phase.

PRESERVED CONSTRAINT: protected-base validation, freeze i MQ.

### D11. Historyczna procedura Atlas może uruchamiać zbyt szerokie testy

Waga: średnia. Evidence: mocne dla tekstu; aktywacja hipotetyczna.
Pliki: Atlas root, docs/testing/ATLAS-VERIFICATION-PLATFORM.md, prompty E2E optimization.
Fragmenty: atlas-local-e2e, legacy 77-scenario qualification obok active maintenance.
Disposition: MOVE TO ON-DEMAND REFERENCE.

Replacement:
> Legacy verification procedure — historical reference only during maintenance. It may be activated only by a current, explicitly authorized restoration task that names the applicable gate and evidence contract. This section does not authorize runtime changes or reinstatement of suspended workflows.

PRESERVED CONSTRAINT: UI/browser proof, rights/provenance, Game truth i minimal data capability.

### D12. Profile modeli rozproszone po promptach

Waga: średnia. Evidence: mocne, 19 promptów Game.
Przykład: docs/agents/prompts/OTV2_SOL_SERVER_SEAM_LEAD.md:
recommended_model: GPT-5.6 Sol
recommended_effort: extra-high_or_highest_available
Disposition: MOVE TO EXECUTION PROFILE.

Replacement:
> The invocation alias is a stable role identifier and does not select a model. Model, surface, effort and fallback are execution-profile settings. They do not change this role's scope, ownership or acceptance criteria.

Proponowany profil odpowiada przyjętemu sposobowi pracy; nie jest benchmarkiem ani potwierdzeniem dostępności na każdym koncie:
- chat_model: GPT-5.6 Sol
- work_codex_model: GPT-6 Astra
- effort: selected_for_task
- fallback: verify_available_capability

PRESERVED CONSTRAINT: role, scope i acceptance niezależne od modelu; wyższy effort pozostaje dostępny.

### D13. Wszystkie odsyłacze przy governance change

Waga: średnia. Evidence: mocne.
Plik: Game docs/agents/AGENTS.md, Governance changes.
Fragment: „requires review of every referenced file”.
Disposition: NARROW TRIGGER.

Replacement:
> Review modified policy, its direct consumers and referenced contracts whose meaning or enforcement is affected. Expand the review when a reference exposes a relevant authority, safety or compatibility dependency. Unaffected references do not require recursive rereading.

PRESERVED CONSTRAINT: wpływ na enforcement i authority nadal sprawdzany.

### D14. Game MQ weryfikuje szerzej niż PR

Waga: średnia, koszt. Evidence: mocne dla konfiguracji; savings niezmierzone.
Plik: docs/agents/BUILD_TEST_MATRIX.md, Current Merge Queue gate.
FACT: PR ma impact routing; MQ wymaga Linux/PG, Windows/SIM i supply chain.
Disposition: SCALE VERIFICATION; osobna zmiana CI.

Replacement:
> Compute required merge-group coverage from the complete synthetic group diff using protected verification authority. Select the union of affected dependency and risk groups. Incomplete or unknown impact selects the full qualification set. PR evidence alone does not replace merge-group qualification.

PRESERVED CONSTRAINT: synthetic head, complete diff, fail-closed. Potrzebna implementacja i canary, nie sam Markdown.

### D15. Dwa braki walidacji centralizacji #145

Waga: wysoka przed integracją. Evidence: mocne — kod i nierozwiązane review.
Źródło: Oteryn/Oteryn#145, head 697233ed2b0a6495e1c897be9b70ffc2d7ae3428.
Plik: tools/governance/central_agent_policy.py.
FACT: literal substring omijany soft wrappingiem; validate_task_prompt_text nie stosuje PARALLEL_FIRST_RE / SERIAL_EXCEPTION_RE stosowanych w overlays.
Disposition: CONSOLIDATE.

Minimalna propozycja dla _contains_forbidden_section:
~~~python
normalized = " ".join(text.casefold().split())
return any(
    isinstance(section, str)
    and " ".join(section.casefold().split()) in normalized
    for section in sections
)
~~~

Minimalna propozycja dla validate_task_prompt_text:
~~~python
if PARALLEL_FIRST_RE.search(text) or SERIAL_EXCEPTION_RE.search(text):
    errors.append("task prompt must not mandate parallel-first execution")
~~~

PRESERVED CONSTRAINT: wykrywanie znanych kopii i sprzecznych nakazów. Nadal sprawdzić cytat i negację; checker nie dowodzi pełnej zgodności semantycznej.

### D16. Skills: discovery overlap i duże entry points

Waga: średnia. Evidence: mocne dla źródeł sesji; efekty hipotetyczne. Nie są to pliki Oteryn.

| Źródło | Dowód | Disposition i replacement |
| --- | --- | --- |
| e0/.system/skill-creator oraz e0/oai/skill-creator | Ta sama nazwa, odmienne destinations | NARROW TRIGGER: system „Author skill source files in an explicitly selected repository. Excludes ChatGPT personal-skill installation and lifecycle.”; OAI „Create, install, update or remove personal ChatGPT skills using the managed personal-skills checkout.” |
| e0/oai/skill-creator/SKILL.md | 32 232 znaki; authoring, installation i recovery razem | SPLIT: „Select one route: authoring, installation/update, removal, or troubleshooting. Load only that route's reference. Read-only questions do not activate write or permission-probe procedures.” |
| e0/oai/personal-context | Dodatkowe discovery po szerokim continuity triggerze | NARROW TRIGGER: „Retrieve prior personal context only when a specific missing prior fact can materially change the answer and is absent from visible conversation or current authoritative sources.” |
| e0/builtins/documents | 40 933 znaki, repeat until flawless | SCALE VERIFICATION: „Render and inspect the deliverable. Fix concrete clipping, overlap, missing content and material layout defects. Stop when acceptance criteria are met; do not iterate solely for subjective perfection.” |
| e0/oai/visualize | Description szerszy niż body | NARROW TRIGGER: „Create an in-conversation interactive visual only when interaction materially helps explain a relationship. Excludes ordinary tables, static comparisons and repository-native implementation.” |

FACT: lokalna konfiguracja oznaczała systemowy skill-creator disabled, lecz metadata były widoczne w katalogu sesji.
UNKNOWN: cache, inny mechanizm katalogu lub różnica runtime. INVESTIGATE REMOVAL: najpierw świeża sesja i sprawdzenie faktycznej aktywacji; nie powtarzać usuwania bez dowodu.

PRESERVED CONSTRAINT: poprawna instalacja, trwałość plików, visual quality i trafność użycia historii.

### D17. KEEP — wymagania, których nie należy usuwać

- Jawna authority; rola, manifest i tool access nie rozszerzają scope.
- Candidate nie zatwierdza własnej zmiany governance.
- Game session-generation fencing, independently current authority, recovery i trwałe mutacje.
- Simulation determinism: neutralność protocol/persistence, kontrola zegara/RNG.
- Atlas: Game canonical World/Content, rights/provenance, merged-main-only deployment.
- qualification_fixture / bounded_real_world / real_fullworld rozdzielone.
- Bezpieczna credential compatibility: conditional reference, nie usunięcie.
- Backup cut nie nadpisuje aktualnego produktu bez recovery authority.
- Brak no-op commitów, hidden retries i fikcyjnego background execution.

Nie ma dowodu, by te reguły usuwać tylko dlatego, że Astra jest nowsza.

## E. SCENARIO WALKTHROUGHS

Wszystkie wyniki to HYPOTHESIS. Nie wykonano scenariuszy.

| Scenariusz | Trace | Friction i completion |
| --- | --- | --- |
| 1. Literówka | root → Platform bootstrap/router lub Game nested → mała poprawka → lekkie checks → integracja | Bez ADR/E2E/programme. Duży bootstrap; Game MQ może uruchomić szerokie checks |
| 2. DB migration | root/nested → data ownership/contract → scope/rollback → isolated migration/integration tests → risk review → required CI | Szczegółowe procedury uzasadnione. Production deployment osobno |
| 3. UI visual | root → UI/test route → implementation/tests → browser i faktyczne obejrzenie obrazu → CI | Platform może wymusić zbędny Codex handoff. Atlas maintenance rzeczywiście blokuje runtime mutation |
| 4. Failing local test | failure → diagnosis → targeted repair → proof | Three-repair cap może zatrzymać mimo nowej evidence. Identyczne próby bez evidence powinny dawać STALLED |
| 5. Deployment z approval | przygotowanie artifactu → tests/config/rollback → review/integration → target/evidence → approval tuż przed protected action | Bez pytania o dozwolone preparation; merge nie jest production approval |
| 6. Medium multi-file + research | allocation → niezależne badania → jeden mutating owner → integration evidence → checks | META/Atlas proporcjonalne; Game/Platform mogą wymusić fan-out. Celowe coordinator merge authority zachować |

Docelowe znaczenie:
- CONTINUE: dozwolony next action materialnie przybliża wynik.
- COMPLETE: wymagane deliverables i proporcjonalna walidacja gotowe; deployment nieudawany.
- BLOCKED: brak informacji, capability, authorization lub rozstrzygnięcia authority.
- STALLED / WAITING_EXTERNAL: prawdziwe stany operacyjne, nie automatyczne pytanie użytkownika lub completion.

## F. PROPOSED EDITS BY FILE

Propozycje z D, nie wykonane zmiany.

| Plik/rodzina | Minimalny zakres |
| --- | --- |
| META ecosystem/agent-continuation-policy.json + validator | D2: capability-based routing, spójny schema/code |
| META #145 tools/governance/central_agent_policy.py | D15: whitespace i concurrency symmetry |
| Game docs/agents/OWNER_FUNDED_AI_POLICY.md | D1: wycofany controller; zachować non-review metered-use boundary |
| Game OTV2_SOL_SERVER_SEAM_LEAD.md i podobne prompty | D1/D12: inheritance zamiast review/RDC copies, profile poza rolą |
| Game/Platform AGENTS.md | D3: delegation po jawnej adopcji |
| Game docs/agents/CONTEXT_ROUTING.md | D8: conditional nested |
| Game docs/agents/AGENTS.md | D4/D13: checkpoint cache i affected-reference review |
| Game/Platform ANTI_STALL_AND_EXECUTION_BUDGET.md | D5/D9: stalling vs blocker i proportionate review |
| Platform PLATFORM_AGENT_BOOTSTRAP.md | D6/D7: authority reconciliation i usunięcie duplikacji |
| Platform EXECUTION_MODE_ROUTING.md | D2: cienki profile |
| Platform PROMPTING_STANDARD.md | Powtórzona komunikacja → jeden controlling contract |
| Atlas AGENTS.md | D10/D11: maintenance i historyczne procedury |
| Atlas docs/maintenance/ATLAS-MAINTENANCE-MODE.md | D10: aktualna wymagana bramka |
| Game BUILD_TEST_MATRIX.md + workflow/classifier MQ | D14: osobna kwalifikowana zmiana CI |
| D16 skills | Właściciel konfiguracji środowiska, nie polityka Oteryn |

Checkpointy D4 przenieść dopiero po ownership closeout. Nie tworzyć deterministic testu kodującego listę „dzisiaj zamkniętych Issues”.

## G. SMALLEST USEFUL CLEANUP BATCH

RECOMMENDATION — pierwszy pakiet bez redesignu:
1. Game: wycofany review controller z OWNER_FUNDED_AI_POLICY i promptów.
2. Game: 13 nieaktualnych checkpointów po closeout verification.
3. Atlas: maintenance prose zgodne z live required check.
4. META #145: dwa istniejące validator defects.
5. Platform: usunięcie duplicate baselines z bootstrapu, zachowanie scope/safety.

Następny pakiet:
- jawna adopcja centralnego bindingu providerów;
- delegacja i completion semantics;
- capability-based profile Sol Chat / Astra Work–Codex;
- osobno MQ/test optimization.

Nie duplikować aktywnych ownership lanes:
- [META #142](https://github.com/Oteryn/Oteryn/issues/142)
- [META #145](https://github.com/Oteryn/Oteryn/pull/145)
- [Game #150](https://github.com/Oteryn/Oteryn-Game/pull/150)
- [Platform #1270](https://github.com/Oteryn/Oteryn-Platform/pull/1270)

META #140 to zamknięte Issue programu, nie PR. #142 jest następcą. Stan #145 podczas audytu: draft, head 697233ed2b0a6495e1c897be9b70ffc2d7ae3428, zielony meta-gate i dwa unresolved review threads. Przed dalszą decyzją odświeżyć.

## H. VALIDATION PLAN

Brak wykonanego runtime A/B dowodzącego poprawy. Dotychczasowe dowody to treść, rozmiary i live state, nie przewaga simplified instructions na Astrze.

### A/B

Dla sześciu zadań z E:
- A: aktualne instrukcje.
- B: jeden mały cleanup batch.
- Ten sam model, effort, narzędzia, snapshot i acceptance.
- Astra Work/Codex i Sol Chat osobno; nie mieszać surface w jednym wyniku.
- Przy nondeterminism: co najmniej trzy próby na wariant jako bounded canary, nie pełny benchmark.

| Metryka | Pomiar |
| --- | --- |
| Context | Faktycznie loaded files/bytes; tokens tylko z telemetry |
| Reading | Repeated reads bez zmiany, niewykorzystane dokumenty |
| Approval | Uzasadnione i zbędne przerwy |
| Follow-through | Completion, false blocker, premature stop |
| Verification | Selected tests, powtórki bez przesłanki, runner-time |
| Delegation | Independence, handoff cost, ownership conflicts |
| Correctness | Acceptance, invariants i regressions |
| Safety | Unauthorized operations, data exposure, gate bypass: zero tolerance |

### Historyczne obejścia: comparison experiments

| Current instruction | Simplified | Keep old only if |
| --- | --- | --- |
| Highest effort w roli | Effort w profilu task | Powtarzalna regresja correctness przy niższym |
| Credential compatibility w root | Conditional reference | Agent z poprawnym routingiem nie publikuje bezpiecznie autoryzowanej zmiany |
| Review po każdej zmianie SHA | Material-risk review | Pomijana zmiana unieważniająca review |
| Every referenced file | Direct consumers + affected contracts | Pomijany istotny wpływ pośredni |
| Three repairs → rotation | Identical-retry bound + new evidence | Pętla tej samej awarii |
| Global policy copied in prompt | Inheritance + task delta | Naruszony konkretny invariant mimo poprawnego załadowania authority |

Acceptance: mniej zbędnej pracy przy zachowanej poprawności, completion i safety. Przy regresji przywrócić minimalny scaffold naprawiający konkretny problem, nie cały historyczny szablon.

## Source locators and evidence boundary

Repository paths in findings are relative to the repository named in that finding and the snapshot in B. Live URLs below are locators and may change:
- [META root](https://github.com/Oteryn/Oteryn/blob/0c493896040072badeff1f333eb83d7114a993ff/AGENTS.md)
- [Game root](https://github.com/Oteryn/Oteryn-Game/blob/9be69b4e0a06f3978d5c5c5603ca3e5670a9f18a/AGENTS.md)
- [Platform root](https://github.com/Oteryn/Oteryn-Platform/blob/3b2ea1c7392187d5d22488673073dc8f8305a374/AGENTS.md)
- [Atlas root](https://github.com/Oteryn/Oteryn-Atlas/blob/51623c7dab2346cee39cd51e3caa845bf4b65426/AGENTS.md)
- [META centralization review](https://github.com/Oteryn/Oteryn/pull/145#pullrequestreview-5100690917)
- [Backup recovery evidence](https://github.com/Oteryn/Oteryn-Platform-Migration-Backup-20260818/blob/6da4f83ef6a35afbab3332f90d7c7f171d23d235/RECOVERY_EVIDENCE.md)

Archived documents and other harnesses were not exhaustively inspected. The document preserves the system audit findings, proposed wording and comparison plan; it is not a runtime test result, comprehensive security certification or mutation authorization.
