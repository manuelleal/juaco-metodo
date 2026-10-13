# Instalar los agentes y las skills en Claude Code

Los agentes (`agentes/*.md`) y las skills (`skills/*/SKILL.md`) son archivos de texto para Claude Code. Se pueden
instalar para un solo proyecto o para todos.

## Opción A: sólo en tu proyecto (recomendada para probar)

Desde la raíz de tu proyecto, con este repositorio en `../metodo`:

```sh
mkdir -p .claude/agents .claude/skills
cp ../metodo/agentes/metodo-*.md .claude/agents/
cp -r ../metodo/skills/metodo-* .claude/skills/
```

## Opción B: para todos tus proyectos

```sh
mkdir -p ~/.claude/agents ~/.claude/skills
cp metodo/agentes/metodo-*.md ~/.claude/agents/
cp -r metodo/skills/metodo-* ~/.claude/skills/
```

En Windows con PowerShell: `Copy-Item metodo\agentes\metodo-*.md $HOME\.claude\agents\` y
`Copy-Item -Recurse metodo\skills\metodo-* $HOME\.claude\skills\`.

**Antes de copiar, mira si ya existen archivos con el mismo nombre** (`ls ~/.claude/agents/metodo-*`): `cp` los
sobrescribe sin preguntar. En la máquina donde nació este repositorio ya hay un `metodo-sembrador.md` y un
`metodo-auditor-ciego.md` en `~/.claude/agents/`, versiones anteriores atadas a JUACO; haz una copia de respaldo o
instala con la opción A.

## La guardia (opcional, recomendada)

1. Copia `herramientas/` y `config.toml` a la raíz de tu proyecto y edita `config.toml` (propósito, congelados,
   carpetas protegidas). Para sellar un archivo: `python herramientas/guardia.py --sella ruta/al/archivo`.
2. Copia `herramientas/ejemplo_settings.json` a `.claude/settings.json` de tu proyecto (o funde su bloque `hooks` con
   el que ya tengas).
3. Comprueba: `python herramientas/prueba_guardia.py` debe terminar en `21/21`. Dentro de Claude Code, pídele que
   edite un congelado: debe aparecer `GUARDIA (bloqueado)`.

Requisitos: Python ≥ 3.11 (usa `tomllib`), `git`, y `sh` en el PATH (en Windows viene con Git for Windows).

## Comprobar que quedaron instalados

En Claude Code, `/agents` lista los agentes `metodo-*`; las skills aparecen al escribir `/metodo-`.
