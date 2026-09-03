# unchanged

**Expects:** `verified`

Nothing moved. The baseline: if this does not verify, no other scenario's result means anything.

## Layout

`tree/` is the working directory the committed `manifest.json` was recorded against.
`mutate.sh` is applied to a **copy** of it before verification, so scoring never modifies the
corpus. `expected.yaml` is read only by the scorer, never by the tool.

`runner.sh` and `extra.txt` sit outside the `data/**/*.txt` input globs deliberately: mutating
`runner.sh` changes what the command does while every input digest still matches, which is the only
way to exercise the result axis on its own.
