# Audit log of commands (acceptance 9)

Allowed class: source and GitHub inspection only. No command touched a running service, container, Graylog, FALCON, Redis, database, broker or credential store. No hostnames or addresses are recorded in this public log.

| # | Command class | What | Where | Within allowed list |
|---|---|---|---|---|
| 1 | file read | brief, PID, portfolio, decision register, operating model (read-only files of the programme repository and the dispatch brief) | local filesystem | yes |
| 2 | `git clone`, `git checkout -b` | fresh clone of `maff0000/falcon` from GitHub; branch `wo/GOLD-AUD-E-evidence` from `origin/main` at `8f218ec1b85b932285b042a7b1ae64dbd11eebee` | audit worktree | yes |
| 3 | `git clone` | fresh read-only clones of `maff0000/HELIOS` (`7f7193d...`) and `maff0000/tron` (`5577039...`, branch `wo/WO-TRON-D1` `37d5f00...`) from GitHub, outside the falcon clone | audit worktree | yes |
| 4 | `gh api` (GET) | repository visibility; head commit of `main`; pull request list (numbers, states, merge SHAs) | GitHub | yes (read) |
| 5 | `git show`, `git ls-tree`, `git archive` | read `GOAL-TRIGGER-001` candidate at `64c843b...`; list and read TRON and HELIOS files at the audited revisions | local clones | yes |
| 6 | file read, `grep`, `sed`, `python3` (json/re parsing) | all registries, schemas, fixtures, content pack, documents, source files | local copies | yes |
| 7 | `python3 docs/evidence/GOLD-AUD-E/regenerate_ep3.py --check` | EP-3 regeneration check | local | yes |
| 8 | `python3 docs/evidence/GOLD-AUD-E/verify_stale_lines.py` | EP-10 line and needle verification | local | yes |
| 9 | `python3 docs/evidence/GOLD-AUD-E/ep09_reference_model.py` | EP-9 reference model tests (in-process, no network, no sockets) | local | yes |
| 10 | CI-equivalent checks | structure, manifest cross-check and internal link check re-implemented from `.github/workflows/ci.yml`; `python3 -m unittest discover -s tests -p "test_*.py"`; `gitleaks` scan of the working tree and history | local | yes |
| 11 | `git add <named files>`, `git commit` | local commit only on the evidence branch | audit worktree | yes |

Not run, by design: `docker`, `systemctl`, any HTTP call to a FALCON or Graylog endpoint, any credential read, any `git push`, any pull request, any GitHub comment.

Results of items 7 to 10 are recorded in the private handback; re-run them to reproduce.
