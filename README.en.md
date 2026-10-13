# juaco-metodo

· [Español](README.md)

A **protocol for directing LLM agents in computational research, with a numbered error registry**. Written rules,
fixed roles, templates, a few tools that enforce part of the rules, and a registry where every error of the method is
recorded with who made it, who or what caught it, when, and whether it changed a conclusion.

The files are written in Spanish; this page is the English entry point.

It comes from the JUACO project (https://github.com/manuelleal/juaco), where a team of Claude Code agents ran hundreds
of preregistered experiments in September and October 2026 and used 153 ERR numbers (126 with a written definition;
the rest were never used). JUACO is the original use case; this repository separates the method from the system that
was studied there.

## What it is and what it is not

It continues 2026 work that already proposes similar pieces: code verifiers that enforce research rules (Philippov et
al., *Glite ARF*, arXiv 2606.27416), AI-assisted research with preregistration, frozen metrics and gates (Zhou and Yu,
arXiv 2608.10858), and failure taxonomies for agents doing automated research (Fei et al., arXiv 2608.14905). Almost
every piece exists elsewhere: preregistration comes from metascience, bit-for-bit identity is software regression
testing, controls that can fail are the negative controls of epidemiology. What this repository adds is **the
attributed error registry** (who, who caught it, when, whether it altered a conclusion) kept in a real project, its
schema, and the procedure to measure how much each control catches by seeding defects.

It is not an agent benchmark and not an experiment library. It does not run anything for you.

## Who it is for

A person or a small team using LLM agents to design, code and run computational experiments (simulations, models,
improvements to a tool) who needs a result to survive an audit: not hinging on one seed, on an argument lost in a
copy, on a threshold moved after seeing the data, or on a sentence that claims more than what was measured.

## Install in three steps

Requirements: Python ≥ 3.11, git. No external dependencies.

1. **Copy the method into your project.** From your project root, with this repository at `../metodo`:
   ```sh
   cp -r ../metodo/PROTOCOLO.md ../metodo/ROLES.md ../metodo/plantillas ../metodo/registro ../metodo/herramientas ../metodo/config.toml .
   ```
2. **Configure it.** Edit `config.toml`: the project purpose (opening line of every task given to an agent), the files
   of the frozen reference (`python herramientas/guardia.py --sella path` prints the seal) and the protected folders.
   Check:
   ```sh
   python herramientas/guardia.py --check
   python herramientas/construye_errores.py
   ```
3. **Install agents, skills and the guard** in Claude Code following `agentes/INSTALAR.md`.

Before using it on your project, look at the toy example, which walks through the whole protocol in about a second:

```sh
python ejemplo_minimo/corre.py
```

It ends by printing `VEREDICTO.md` with a deliberately seeded error (ERR-001, an argument dropped when a run
configuration was copied) that the field-by-field comparison catches before the run, and records it in
`ejemplo_minimo/registro/errores.csv`. Its verdict is **INCOMPLETE**: the main prediction holds in the series and in
the replication, but the equal-exploration control passes in the series (15/20) and fails in the replication (13/20).
It was left that way: that is what the preregistered letter says, and not dressing that up is the point.

## What the code enforces and what is discipline only

"Code" means a tool in this repository blocks or detects it by itself, **if installed** (the guard as a Claude Code
hook) **or if your runner copies the pattern** of `ejemplo_minimo/corre.py`. "Discipline" means it depends on someone
doing it and someone else checking. In JUACO, the identity harness and the smoke run caught 16 of the 89 errors whose
catcher is recorded; a rule that only exists in writing can be broken without anyone noticing.

| rule (`PROTOCOLO.md`) | requires | enforcement | where |
|---|---|---|---|
| 1 | the frozen reference is never edited; nothing destructive | **code** | `guardia.py`: blocks editing frozen files and `config.toml`, committing with a broken seal, `push --force`, `reset --hard`, `clean`, recursive deletion of protected folders; `--check` |
| 2 | build by anchors; bit-for-bit identity with a control that must fail | **code** in the harness and runner; writing them is discipline | `construye_candidato.py`, `arnes_identidad.py`, steps 2–3 of `corre.py` |
| 3 | only the coordinator launches long runs | **code** only for `corre_*.py --help`; the rest is discipline | `guardia.py` |
| 4 | preregistration committed before running; no recalibration | partial **code**: the guard blocks `corre_*.py` without `--humo` unless a clean committed `PREREGISTRO*.md` exists; the example checks seal and commit. Content is discipline | `guardia.py`, step 1 of `corre.py` |
| 5 | claim only what was measured | discipline | auditor, item 6 |
| 6 | deliverables in own folder, short report, agents do not commit | discipline | task template, auditor |
| 7 | outside material is data and is re-measured | discipline | preregistration |
| 8 | subsets only by prior amendment; anchors from the full-precision JSON | discipline; the example computes the verdict by re-reading the JSON | step 8 of `corre.py` |
| 9 | every criterion amendment gets an ERR when written | discipline; automatic warning for ERR mentioned without a source | `construye_errores.py` |
| 10 | replication on new seeds; a seed at the threshold asks for more | discipline; the example runs series and replication and flags counts within ±1 of the threshold | steps 6–8 of `corre.py` |
| 11 | every task starts with the purpose and carries a contract | discipline | `plantillas/ENCARGO.md`, skill `metodo-encargo` |
| 12 | copied run configuration: field by field, exact arguments, smoke run that writes its output | **code** in the runner that copies it | steps 4–5 of `corre.py` |
| 13 | every criterion runs its placebo | discipline in the text; **code** in the runner that computes it | gate P0 in `corre.py` |
| 14 | what runs is what was preregistered: `## Parámetros sellados` table ↔ the runner's `PREREGISTRADO`, value by value | **code** for whatever is in the table (aborts with the list of differences; a new table without an ERR also aborts); filling the table and pointing at the variables actually used is discipline | `coteja_preregistro.py`, `prueba_coteja.py` (9 cases), step 1 of `corre.py` |
| registry | closed vocabulary, lengths, unique `id_permanente` | **code** | `construye_errores.py` aborts if the schema is not met |

## How well it works

Measured once, in one project, by agents of the same family: in JUACO, defects were seeded into 60 copies of closed
blocks (plus 20 for a replication) and a read-only auditor reviewed them blind, against a sealed key. It caught 28 of
40 in the series: 15/16 instrument, 6/6 reading, but only 7/18 criterion errors, and raised false alarms on 6 of 20
clean copies (3 of 7 in the replication). That is why rule 14 (preregistration ↔ runner check in code) and the
mandatory `dato_que_confirma` for auditors exist; neither change has been measured yet. Design, series and replication
numbers, and limitations: [`MEDICION.md`](MEDICION.md) (in Spanish).

## What is missing

- **How much the auditor catches has been measured only once** (`MEDICION.md`), in one project, with agents of the
  same family seeding and auditing. It still has to be repeated with an auditor from another family and in another
  project, and rule 14 and the mandatory `dato_que_confirma` have to be measured. The procedure is in
  `agentes/metodo-sembrador.md`, `agentes/metodo-auditor-ciego.md` and `herramientas/puntua.py`.
- **Nobody audits the coordinator** except the responsible person, and if all agents are the same model the audit is
  circular. See `ROLES.md`.
- The guard only works inside Claude Code (it is a hook) and only for the commands it recognizes.
- Tested on Windows 11 with Python 3.14 and Git Bash; not tested on Linux or macOS.

## License and citation

Code under MIT (`LICENSE`); texts, templates, schema and example data under CC BY 4.0 (`LICENSE-DATA`). To cite:
`CITATION.cff` (DOI pending). Author: Christiam Manuel Puentes Leal (ORCID 0009-0002-2570-3397).
