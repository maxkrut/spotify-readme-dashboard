# Contributing

Help make Spotify README Dashboard more useful, accurate and enjoyable to explore. Developers, designers, music metadata enthusiasts and coding agents are welcome to contribute to the analytics, interface, automation and documentation.

You can start with a small fix, a visual proposal, a reproducible bug report or a better explanation. You do not need Spotify credentials or access to the maintainer's private library to work on the project.

## Where you can help

| Area | Ideas for contributions | Start here |
| --- | --- | --- |
| Analytics and logic | Clearer metrics, correct denominators, comparisons over time, missing-data handling and useful new insights. | [dashboard_insights.py](scripts/dashboard_insights.py), [dashboard semantics](DATA.md#dashboard-semantics) |
| Interface and visualization | More readable charts, better information hierarchy, mobile layouts, accessible labels and color choices, and useful empty states. | [build_readme.py](scripts/build_readme.py), [README](README.md) |
| Metadata quality | Better artist identity matching, evidence-backed genre and country corrections, and clearer coverage reporting. | [data reference](DATA.md), [genre audit](scripts/audit_genres.py) |
| Export and automation | More reliable imports, clearer failures, efficient API use and easier GitHub Actions setup. | [export_spotify.py](scripts/export_spotify.py), [update workflow](.github/workflows/update-readme.yml) |
| Tests and performance | Reproductions of real bugs, edge cases, and measured improvements for large libraries. | [tests](tests), [image validator](scripts/validate_dashboard.py) |
| Documentation and onboarding | Simpler setup steps, examples, troubleshooting and explanations of what the charts actually measure. | [SETUP.md](SETUP.md), [DATA.md](DATA.md) |

Good first contributions include fixing a clipped chart label, explaining an unavailable metric, improving a confusing setup step or adding a regression case for an incorrect calculation.

## Propose an idea or report a problem

Search the existing [issues](https://github.com/maxkrut/spotify-readme-dashboard/issues) and [pull requests](https://github.com/maxkrut/spotify-readme-dashboard/pulls) first. For a substantial new metric, redesign or architectural change, open an issue describing the user need and proposed approach so we can discuss the direction before a large implementation. Small fixes can go straight to a pull request.

For bugs, include the expected and actual behavior, reproduction steps and a minimal public or synthetic example. For interface proposals, a sketch or annotated screenshot is useful. For analytics, explain the inputs, calculation and how missing data should appear.

## Run the project locally

1. Fork the repository, clone your fork and create a branch for your change. Use a fork when contributing upstream; **Use this template** is intended for publishing your own dashboard.
2. Use Python 3.12 or newer in your existing development environment. The dashboard scripts use the standard library; the test suite needs the packages in `requirements-dev.txt`.
3. From the repository root, run:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest tests -q
python scripts/build_readme.py --input data/tracks.example.csv --output .codex-tmp/example/README.md --cache-dir .codex-tmp/empty-cache
python scripts/validate_dashboard.py .codex-tmp/example/README.md
```

Use an empty directory for `--cache-dir` so private listening snapshots cannot affect the example. Open `.codex-tmp/example/README.md` in a Markdown viewer to inspect the result. These commands match the public [CI checks](.github/workflows/checks.yml); preview files stay in an ignored directory.

For a live integration with your own Spotify account, follow [SETUP.md](SETUP.md). Keep that separate from the public example used in a contribution.

## Work on the source of the result

- **README and charts:** change `scripts/build_readme.py` and the relevant calculation code. The README and dashboard SVGs are generated, so edits made only to the output will be overwritten by the next update. When changing introductory text or navigation, keep the checked-in README and its generator in sync.
- **Visual changes:** show before/after previews and check light and dark GitHub themes, narrow screens, long labels and empty data. The interface runs inside GitHub Markdown; account for its HTML and styling limitations. Logo sources and build notes are in [design/logo/SOURCE.txt](design/logo/SOURCE.txt).
- **Analytics:** preserve the distinctions between saved tracks, observed listening events and Spotify top-item snapshots. Explain denominators and time windows; unavailable data must not become a zero or an invented historical value. Update [DATA.md](DATA.md) when calculation semantics change.
- **Metadata:** prefer exact IDs for ambiguous artists and attach evidence links to curated corrections. Keep changes scoped to the recordings or artists the evidence supports.
- **Tests:** add a focused regression test for a behavior change or bug fix. Use small synthetic fixtures and mocked API responses rather than live credentials. Documentation-only changes do not need new tests.

Build previews into a separate output directory. Do not replace the published personal dashboard with the example dataset in a pull request. Include relevant generated assets when needed to review a visual change, and leave unrelated library refreshes out of the diff.

## Working with coding agents

Agent-assisted and agent-authored contributions are welcome under the same review expectations as other contributions. Give the agent a concrete problem, expected behavior and a way to verify the result.

Read this guide, [DATA.md](DATA.md) and the relevant code before editing. Use public examples, keep the change focused, preserve unrelated work and update generated-content sources alongside their output. Do not weaken a failing test or validation rule just to make the checks pass; explain any intentional behavior change.

The person submitting a pull request should review the complete diff and be able to explain it. State which checks actually ran, their results and any remaining limitations. If a check could not run, say so rather than claiming it passed.

## Send a pull request

Describe the problem, what changes for the user and how you verified it. Link the relevant issue, include screenshots for visual changes and explain any changes to data formats or metric definitions. Keep each pull request focused enough to review on its own.

Before submitting, inspect the diff for unrelated generated files and private data. Never include `.env`, tokens, private exports, caches or logs containing credentials in a commit, issue, screenshot or agent prompt. Use a minimal synthetic reproduction instead.

Contributions are reviewed before merging. Questions, documentation improvements and thoughtful feedback are useful contributions too. The project uses the [MIT License](LICENSE); preserve attribution and applicable licenses for any material you add.
