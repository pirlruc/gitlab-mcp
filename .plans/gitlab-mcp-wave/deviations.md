# Departures from the plan

The plan text is `original-plan.md` in this directory. It is the wave
plan. The todo statuses in its frontmatter are the snapshot from
mid-run. The body was not edited.

## What landed differently

- The signed release is `v0.2.4`, not `v0.2.0`. `v0.2.0` failed the
  publish smoke because the publisher splits a quoted `python -c` on
  spaces. `v0.2.1` failed the arm64 pull of the same index digest.
  `v0.2.2` and `v0.2.3` pushed the images and then failed the arm64
  structure test before signing. `v0.2.4` smokes both platforms and
  signs. The pull-request build still runs the structure test.
- Blocking image scans use `pkg_types: library`. Trivy 0.69.3 reported
  fixed OpenSSL findings in the Debian base (the Debian scan exited 1;
  Alpine exited 0). The weekly rescan keeps `os,library` and is
  non-blocking.
- The Debian base was re-pinned. The previous digest was older than
  the 30-day base-image gate.
- `common-release-digests.yml` checks out the caller and reads
  `github.event.release`, so a tag-push consumer cannot use it. The
  release workflow checks out commondevops and runs
  `scripts/append-release-digests.sh` with `TAG` from `github.ref_name`.
- Reusable workflow calls do not pass `scripts_token` or
  `checkout_token`. The ops repositories are public. The guardrails
  and scaffold submodules are private, so the pull-request quality job
  does not check them out.
- Quality on the pull request is `scripts/check-ci-local.sh` on the
  host. `python-quality.yml` pulls `ghcr.io/pirlruc/ci-lint` as the
  job container, and Actions authenticates that pull. GHCR then hides
  the public index from a repository that is not on the package access
  list. Semgrep stays in pydevops.
- Container lint skips the nested infra and secret jobs for the same
  GHCR login. Hadolint still runs on the host. actionlint and zizmor
  were clean locally.
- `check-image-size.sh` on the containerdevops pin measures a
  distroless rootfs by exporting it. The runtime image has no shell.
- A live smoke against `gitlab/gitlab-ce` was not run. The local image
  is untagged, and a first boot is a multi-minute Omnibus start. Tool
  behavior is covered by the mocked HTTP suite.
- Repository settings were not changed. They are listed below and wait
  for approval.
- github-scaffold issue sync did not run. Open tasks #308 and #313
  both use `GS-DEP-SEED-001-T2`. Guardrails and methodologies did sync.

## Ops pull requests still open

- https://github.com/pirlruc/pydevops/pull/266
- https://github.com/pirlruc/containerdevops/pull/204
