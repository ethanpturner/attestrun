# removed-and-changed

**Expects:** `unverifiable`

Precedence. One input is unreadable and another moved; unverifiable outranks contradicted (DEC-004), because a run that was not fully checked cannot support the stronger claim that it is wrong.

## Layout

`tree/` is the working directory the committed `manifest.json` was recorded against.
`mutate.sh` is applied to a **copy** of it before verification, so scoring never modifies the
corpus. `expected.yaml` is read only by the scorer, never by the tool.

`runner.sh` and `extra.txt` sit outside the `data/**/*.txt` input globs deliberately: mutating
`runner.sh` changes what the command does while every input digest still matches, which is the only
way to exercise the result axis on its own.
