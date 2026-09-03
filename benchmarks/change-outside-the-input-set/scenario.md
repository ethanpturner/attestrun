# change-outside-the-input-set

**Expects:** `verified`

The tool's own limit, pinned. extra.txt changed and no glob covers it, so the run verifies. That is DEC-007 rather than a defect: no input set can be complete, and a scenario asserting the pass stops the bound being quietly forgotten.

## Layout

`tree/` is the working directory the committed `manifest.json` was recorded against.
`mutate.sh` is applied to a **copy** of it before verification, so scoring never modifies the
corpus. `expected.yaml` is read only by the scorer, never by the tool.

`runner.sh` and `extra.txt` sit outside the `data/**/*.txt` input globs deliberately: mutating
`runner.sh` changes what the command does while every input digest still matches, which is the only
way to exercise the result axis on its own.
