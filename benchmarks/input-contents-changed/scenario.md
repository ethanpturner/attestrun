# input-contents-changed

**Expects:** `contradicted`

An input's contents moved, so the manifest's claim about them is false. The command still runs identically, which is why the result axis stays verified -- the two axes are independent and a contradiction on either is enough.

## Layout

`tree/` is the working directory the committed `manifest.json` was recorded against.
`mutate.sh` is applied to a **copy** of it before verification, so scoring never modifies the
corpus. `expected.yaml` is read only by the scorer, never by the tool.

`runner.sh` and `extra.txt` sit outside the `data/**/*.txt` input globs deliberately: mutating
`runner.sh` changes what the command does while every input digest still matches, which is the only
way to exercise the result axis on its own.
