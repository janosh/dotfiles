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
        entry: yarn tsc --noEmit
        language: system
        types: [ts]
```

[Probably best](https://twitter.com/messages/843173484343644161-1317920112700231682) to not run TypeScript in CI since it requires all `node_modules` for type checking.
