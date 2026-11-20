# Tools

## Read tools

| Tool | GitLab API |
|------|------------|
| `list_merge_requests` | `GET /merge_requests`, `/projects/:id/merge_requests`, `/groups/:id/merge_requests` |
| `search_merge_requests` | `GET /search` (scope=`merge_requests`) |
| `get_merge_request` | `GET /projects/:id/merge_requests/:iid` |
| `get_merge_request_diffs` | `GET .../diffs` |
| `list_merge_request_commits` | `GET .../commits` |
| `list_merge_request_diff_versions` | `GET .../versions` |
| `get_merge_request_diff_version` | `GET .../versions/:version_id` |
| `list_merge_request_discussions` | `GET .../discussions` |
| `get_merge_request_discussion` | `GET .../discussions/:discussion_id` |
| `list_merge_request_pipelines` | `GET .../pipelines` |
| `get_merge_request_approvals` | `GET .../approvals` (Free-tier aware) |
| `list_merge_request_participants` | `GET .../participants` |
| `list_merge_request_reviewers` | `GET .../reviewers` |

## Write tools (registered only when `GITLAB_READ_ONLY=0`)

| Tool | GitLab API |
|------|------------|
| `create_merge_request_thread` | `POST .../discussions` (optional diff position) |
| `reply_to_merge_request_thread` | `POST .../discussions/:id/notes` |
| `set_merge_request_thread_resolved` | `PUT .../discussions/:id?resolved=` |
| `update_merge_request` | `PUT .../merge_requests/:iid` |

### Update allowlist

`update_merge_request` accepts only:

`title`, `description`, `labels`, `add_labels`, `remove_labels`, `milestone_id`

Fields such as `state_event`, `target_branch`, and merge-related keys are
rejected before the request is built.

## Also registered

`GITLAB_TOOLSETS` selects `merge_requests`, `issues`, `work_items`, `search`,
`wiki`, `core`, `repository`, and `ci`. `all` registers every set.
`get_merge_request` accepts a `url` only when its host matches `GITLAB_URL`.
Job logs and artifact files are truncated (`truncated: true`) rather than returned whole.

## Explicitly unavailable

Merge, close, reopen, delete, rebase, approve, Duo Agent Platform, Orbit, and
vulnerability tools. `accept_merge_request` stays blocked.
