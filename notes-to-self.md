# Notes to self

## Mylio Setup

When transferring Mylio photo library to a new Mac, setup as a new machine (don't replace existing device). Start syncing over WiFi to see where Mylio expects the image folder as well as 'Generated Images.bundle' to be. Then quit Mylio and replace both the image folder and the bundle of preview images with files from the last Time Machine backup of the old Mac. When reopening Mylio, it will scan all the images it finds much quicker than loading over the network from the old machine and realize there's nothing left to sync.

## `tsc` as `pre-commit` hook

2022-07-30: TypeScript compiler can be used as pre-commit hook in `--noEmit` mode:

```yml
ci:
  skip = [tsc]

repos:
  - repo: local
    hooks:
      - id: tsc
        name: TypeScript
        entry: pnpm tsc --noEmit
        language: system
        types: [ts]
```

[Probably best](https://twitter.com/messages/843173484343644161-1317920112700231682) to not run TypeScript in CI since it requires all `node_modules` for type checking.

## When having lost work in VS Code

Incident on 2022-08-04: I had a `functorch_ensemble.ipynb` notebook which I renamed to a regular Python script `.py` and continued editing for 2 hours. After saving all files, I noticed 1 remaining blue dot indicating an unsaved file. This happens often when using the interactive window so I thought nothing of it, closed the workspace and left for lunch. I later reopened the folder and saw the `functorch_ensemble.py` had the original JSON content from the Jupyter notebook in it. All my edits were missing.

Recovery: Following this [superuser answer](https://superuser.com/a/1723403), I was able to recover my changes from `~/Library/Application\ Support/Code/User/History` by grepping for the term `accuracy_dict` which I knew I had added late in the 2h editing process. So any matching file would be a more recent backup.

```sh
find . -name "*.py" -exec grep accuracy_dict {} +
```
