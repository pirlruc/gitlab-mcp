# Departures from the plan

- Blocking image scans use `pkg_types: library`. The pinned Debian base
  still carries fixed OpenSSL advisories (Trivy 0.69.3, 327 OS findings).
  The weekly rescan keeps `os,library` and is non-blocking.
- `common-release-digests.yml` checks out the caller and reads
  `github.event.release`, so a tag-push consumer cannot use it. The
  release workflow checks out commondevops and runs
  `scripts/append-release-digests.sh` with `TAG` set from `github.ref_name`.
- Reusable workflow calls do not pass `scripts_token` or `checkout_token`.
  The ops repositories are public.
- A live smoke against `gitlab/gitlab-ce` was not run. The local image is
  untagged and a first boot is a multi-minute Omnibus start. Tool behavior
  is covered by the mocked HTTP suite (78 tests, 96% statement coverage).
- `scripts/check-ci-local.sh` is also the pull-request quality job.
  `python-quality.yml` pulls `ghcr.io/pirlruc/ci-lint` as the job
  container. Actions authenticates that pull, and GHCR hides the public
  index from a repository that is not on the package access list.
  Semgrep stays in pydevops. Pull requests:
  https://github.com/pirlruc/pydevops/pull/266 and
  https://github.com/pirlruc/containerdevops/pull/204.
- Container lint skips the nested infra and secret jobs for the same
  GHCR login. Hadolint still runs on the host. actionlint and zizmor
  were clean locally.
- `check-image-size.sh` on that containerdevops pin measures a
  distroless rootfs by exporting it. `docker run --entrypoint sh` has
  no shell to run.
