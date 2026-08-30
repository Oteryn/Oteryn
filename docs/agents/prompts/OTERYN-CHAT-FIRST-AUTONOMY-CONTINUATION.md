# OTERYN-CHAT-FIRST-AUTONOMY-CONTINUATION

## Alias

`OTERYN-CHAT-FIRST-AUTONOMY-CONTINUATION`

## Prompt

Przejmij jako supervising coordinator lifecycle `Oteryn/Oteryn#108` i kontynuuj projekt organizacyjnej polityki wykonywania długich zadań agentowych.

### Source of truth

GitHub live state jest jedynym source of truth dla repozytoriów, Issue/PR, branch/head SHA, policy, checks, reviews i merge state.

Najpierw odtwórz aktualny stan. Nie ufaj SHA, statusom, dokumentacji ani wartościom produktowym zapisanym w tym promptcie bez ponownego sprawdzenia.

Obowiązkowo odśwież co najmniej:

- `Oteryn/Oteryn` protected `main` i aktualne `AGENTS.md`;
- Issue `#108`;
- META `#69` i PR `#71` — bounded autonomous execution / anti-loop;
- META `#72` — execution-stall lifecycle;
- META `#102` i aktualny rollout Merge Queue/review-fingerprint/anti-loop;
- `ecosystem/agent-execution-routing-policy.json`;
- aktualny stan bounded-execution adoption w Game, Platform i Atlas;
- Platform `docs/agents/ANTI_STALL_AND_EXECUTION_BUDGET.md`, `EXECUTION_PROTOCOL.md`, `PROJECT_LANES.json`, `GOVERNANCE_CONTRACT.json` oraz aktualny Control Room/schema-first ownership;
- wszystkie nowsze PR/Issue/policy, które przejęły ownership nad execution budgets, context rotation, checkpointing, resume semantics albo merge queue.

Przeczytaj `docs/agents/CHAT_FIRST_AUTONOMOUS_EXECUTION_HANDOFF.md` jako trwały zapis ustaleń, ale traktuj jego snapshoty jako provenance, nie live authority.

### Aktualne fakty produktowe OpenAI

Jeżeli właściwości Chat, Work, Codex, Scheduled Tasks, connected apps, event triggers, usage/credits albo context limits są materialne dla designu, zweryfikuj je ponownie wyłącznie na aktualnych oficjalnych źródłach OpenAI. Nie zakładaj, że zachowanie z 2026-08-30 nadal obowiązuje.

Nie wymyślaj nieopublikowanego limitu typu `Chat = 25 min`, `Work = 2 h` ani dokładnej liczby pozostałych tokenów kontekstu, jeżeli aktualny runtime/dokumentacja tego nie podaje.

### Cel

Zaprojektuj jedną spójną, organizacyjną politykę, która daje maksymalną praktyczną autonomię przy minimalnym zużyciu płatnej/współdzielonej puli Work/Codex.

Docelowa zasada operacyjna:

> **Chat-first, GitHub-native async, Work-by-exception.**

Nie traktuj `high effort` jako automatycznego powodu użycia Work. Execution surface i effort są odrębnymi decyzjami.

### Nienegocjowalne rozdzielenie limitów

Design musi jawnie rozdzielić co najmniej:

1. **task lifetime** — życie całego owner-visible zadania/programu;
2. **worker/turn/session lifetime** — życie jednej aktywnej sesji;
3. **tool/command timeout** — limit pojedynczej operacji/build/test/network/log stream;
4. **external-wait budget** — bounded observation CI/review/dependency;
5. **retry/no-progress budget** — anti-loop;
6. **context budget/context pressure** — zdolność bieżącej sesji do bezpiecznego reasoning.

Limit jednej warstwy nie może automatycznie kończyć innej warstwy.

W szczególności:

- worker/session timeout != task timeout;
- tool timeout != task timeout;
- context rotation != task timeout;
- phase completion != task completion;
- preflight freshness != task timeout;
- `WAITING_EXTERNAL` != failure;
- checkpoint != no-op/retrigger commit.

### Task lifetime

Domyślnie całe zadanie nie powinno kończyć się z powodu arbitralnego wall-clock budgetu.

Terminalne wyjście powinno odpowiadać rzeczywistemu stanowi, np.:

- `DONE` — zweryfikowane terminalne zakończenie;
- owner/permission decision required — brak bezpiecznej autonomicznej ścieżki;
- safety/policy approval required;
- terminal `STALLED` po wyczerpaniu właściwych bounded recovery paths i braku nowej materialnej hipotezy/akcji.

Nie osłabiaj anti-loop tylko po to, żeby task trwał dłużej.

### Chat-first

Regularny Chat powinien być primary supervising/execution surface, gdy aktualnie dostępne narzędzia pozwalają wykonać pracę bezpiecznie i poprawnie.

Chat powinien kontynuować użyteczną pracę w bieżącej turze tak długo, jak platforma na to pozwala i istnieje realny progress. Nie kończ dobrowolnie całego taska tylko dlatego, że:

- zakończyła się jedna faza;
- osiągnięto miękki foreground checkpoint budget;
- wykonano checkpoint;
- timeoutowała pojedyncza komenda;
- context pressure wymaga compaction;
- worker powinien się zrotować.

Jednocześnie nie udawaj, że zwykły Chat potrafi po zakończeniu odpowiedzi niewidzialnie stworzyć sobie nową foreground turę. Silent rotation jest dozwolone tylko wtedy, gdy istnieje rzeczywisty mechanizm automatycznego resume.

### Work/Codex-by-exception

Work/Codex wybieraj dopiero wtedy, gdy ich unikalne możliwości materialnie uzasadniają wspólny agentic usage, np.:

- potrzebne jest rzeczywiście persistent/background cloud execution;
- potrzebny jest Work Cloud Browser;
- potrzebny jest event-triggered connected-app resume;
- Codex jest wyraźnie lepszym execution environment dla repo/code/terminal workflow;
- delegated/persistent agent execution daje realną przewagę względem Chat + GitHub-native execution.

Nie używaj Work tylko dlatego, że task jest długi, wieloplikowy albo `high` effort.

### GitHub-native async

Preferuj GitHub Actions/repository-approved runners dla ciężkich deterministycznych operacji, takich jak build, pełne testy, E2E, static analysis czy merge-group qualification.

Agent ma analizować wynik pracy runnera, a nie konsumować kosztowną sesję agentową tylko po to, żeby czekać na compute.

Projektuj finalną integrację zgodnie z aktualnym #102: Merge Queue/auto-merge/same-head re-evaluation powinny redukować polling, chase-moving-main i no-op/retrigger history churn. Nie twórz drugiej konkurencyjnej merge authority.

### Scheduled continuation

Sprawdź aktualne możliwości Scheduled Tasks. Jeżeli nadal są dostępne w Chat i mogą używać GitHub, oceń je jako ekonomiczny periodic resume/monitoring tier.

Nie zakładaj event-triggered GitHub webhook continuation w zwykłym Chat; jeżeli nadal wymaga Work, sklasyfikuj to jako świadomą eskalację.

Nie deklaruj automatic resume, jeśli task/trigger faktycznie nie został skonfigurowany.

### Context pressure

Context limit traktuj jako osobny execution budget.

Nie próbuj utrzymywać całego programu w jednej rosnącej rozmowie. Projekt ma preferować:

> minimal active context + durable GitHub/repository state.

Gdy context pressure rośnie:

1. externalize large evidence/logs/artifacts;
2. compact aktywny stan do materialnych faktów;
3. zapisz durable checkpoint;
4. kontynuuj w tej samej sesji, jeśli nadal jest bezpiecznie;
5. zrotuj sesję, gdy dalszy reasoning byłby niebezpieczny/nieefektywny;
6. następna sesja ma wczytać live GitHub + checkpoint + tylko potrzebne evidence, a nie rekonstruować całą historię chatu.

Nie raportuj `context limit` jako generic blocker, jeśli bezpieczny checkpoint + realny resume path pozwala kontynuować.

### Checkpointing

Checkpoint wykonuj po **materialnych milestone**, nie po każdym tool call.

Obowiązkowo rozważ checkpoint:

- po coherent `investigate/design/implement/validate/integrate/close` phase;
- po materialnym fixie lub odkryciu;
- po materialnie nowym wyniku validation;
- przed heavy/long-running/failure-prone operation;
- przed external waiting;
- przed context/session rotation;
- przed release worker ownership;
- po zmianie materialnego finding/blockera.

Design docelowego checkpointu powinien obejmować co najmniej:

- repository;
- governing Issue/task;
- PR;
- branch;
- exact task head SHA;
- phase/lifecycle state;
- last material progress;
- completed material work;
- validation/evidence references;
- first material failure;
- rejected hypotheses, gdy istotne;
- retry/budget counters, gdy istotne;
- context pressure, gdy istotne;
- blockers;
- dokładnie jeden konkretny `next_action`.

Nie kopiuj tego przykładu jako nowej konkurencyjnej schema bez porównania z aktualnymi META/Platform contracts.

### No-op/retrigger prohibition

Nie twórz pustych/no-op/checkpoint/retrigger commits wyłącznie po to, żeby zapisać oczekiwanie albo obudzić CI/review.

Po technical candidate freeze użyj autoryzowanego Issue/task/control-plane metadata surface, chyba że tracked-file update jest sam w sobie materialną i dozwoloną zmianą.

### User communication

Docelowo owner-facing noise ma być minimalny.

Nie przerywaj użytkownikowi wyłącznie dlatego, że nastąpiło:

- phase completion;
- zwykły checkpoint;
- recoverable tool timeout;
- context compaction;
- worker/session rotation **jeżeli istnieje prawdziwy automatic continuation path**;
- lease renewal/release;
- bounded retry progression.

Powiadom użytkownika, gdy:

- cały task jest terminalnie `DONE`;
- potrzebna jest konkretna owner decision/permission;
- potrzebne jest safety/protected/irreversible approval;
- osiągnięto terminal stalled state po bounded recovery;
- execution zatrzymuje się i **nie ma** realnego automatic resume, więc potrzebne będzie ponowne wywołanie przez ownera.

Nigdy nie twierdź, że praca będzie kontynuowana w tle, jeżeli faktycznie nie istnieje mechanizm, który ją wznowi.

### Reconciliation i overlap

Nie duplikuj istniejącego bounded-execution PR #71 ani merge-queue lifecycle #102.

Jeżeli któryś z tych lifecycle został do czasu uruchomienia tego promptu scalony, zamknięty, superseded albo rozszerzony, zachowaj wykonane elementy i zaprojektuj najmniejszy brakujący delta.

Platform ma już dojrzały Control Room / anti-stall model. Nie twórz drugiego Platform orchestration schema. Ustal, jak przyjąć organizacyjne minimum bez utraty istniejących mocniejszych mechanizmów.

Game/Atlas mają przyjąć organizacyjną semantykę dopiero przez właściwy provider-owned rollout i aktualne live authority.

### Effort i multi-agent

Sklasyfikuj effort na podstawie aktualnego scope po reconciliation.

Użyj `parallel_when_beneficial` tylko gdy istnieją co najmniej dwa materialnie niezależne workstreamy i korzyść przewyższa coordination/integration cost. Użyj najmniejszej użytecznej liczby lanes.

Nie pozwalaj równoległym writerom modyfikować tych samych policy/workflow/schema. Shared policy, merge queue, checkpoint schema i integration surfaces wymagają jednego ownera/lease i seryjnej integracji.

### Wymagany output tego continuation

W pierwszej kolejności doprowadź do jednego spójnego, zweryfikowanego **designu**, a nie do przypadkowej serii patchy.

Zapisz w META:

1. aktualny live-state reconciliation / overlap map;
2. design organizacyjnego task/worker/tool/wait/retry/context lifecycle;
3. executor-selection model `Chat-first / GitHub-native async / Work-by-exception`;
4. durable checkpoint + compaction + resume semantics;
5. user-notification semantics;
6. provider adoption/migration path dla META/Game/Platform/Atlas;
7. deterministic validation/drift strategy;
8. implementation plan po zaakceptowaniu designu zgodnie z aktualnymi repo instructions.

Nie wdrażaj canonical policy/runtime zmian tylko na podstawie starego handoffu. Najpierw zakończ reconciliation i design review wymagany przez aktualne instructions.

### Safety

- Nie osłabiaj branch protection, required checks, exact-head evidence, review authority, merge-queue safety ani anti-loop limits.
- Nie obchodź hard platform/tool limits przez udawanie, że ich nie ma.
- Nie konsumuj Work/Codex/owner-funded AI tylko po to, żeby utrzymać długą sesję, jeśli tańsza bezpieczna ścieżka daje ten sam wynik.
- Nie twórz automatyzacji/scheduled tasks bez potrzeby i bez zgodności z aktualnymi uprawnieniami/planem.
- Nie zmieniaj provider runtime, produkcji, sekretów ani danych w tym lifecycle.

### Terminalny wynik tej fazy

Zakończ dopiero, gdy design i jego durable repo/Issue/PR state są spójne, live-state reconciliation jest aktualne, nie ma nierozstrzygniętego ownership conflict i istnieje jednoznaczny następny etap.

Jeżeli przed implementacją aktualne instructions wymagają owner review/approval designu, zatrzymaj się na tym jednym rzeczywistym gate z dokładnym path/PR i bez wykonywania policy rollout przed zatwierdzeniem.
