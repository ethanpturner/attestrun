# exit-status-changed

**Expects:** `contradicted`

Every input still matches; the command now exits non-zero. The exit status is the determinative signal on re-execution (DEC-008), and this is the only scenario where the result axis alone carries the verdict.

## Layout

`tree/` is the working directory the committed `manifest.json` was recorded against.
`mutate.sh` is applied to a **copy** of it before verification, so scoring never modifies the
corpus. `expected.yaml` is read only by the scorer, never by the tool.

`runner.sh` and `extra.txt` sit outside the `data/**/*.txt` input globs deliberately: mutating
`runner.sh` changes what the command does while every input digest still matches, which is the only
way to exercise the result axis on its own.
