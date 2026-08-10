# Architecture Decision Records

An Architecture Decision Record (ADR) captures a significant design decision for pydantic-forms: the context
that led to it, the decision itself, and its consequences. Once accepted, an ADR is not rewritten — if a decision
is later changed, a new ADR supersedes it and both are kept for history.

Problems that don't have a decision yet belong on the [Open Questions](questions.md) page instead. Move them
here once they're actually resolved.

## Statuses

| Status | Meaning |
|--------|---------|
| Proposed | Written up, still under discussion. An ADR is Proposed for as long as its pull request is open. |
| Accepted | Agreed and in effect. Merging the pull request is what accepts an ADR, so set this in the branch before merge. |
| Rejected | Considered and decided against. Merged anyway, so the reasoning is on record and the option isn't reopened without new arguments. |
| Superseded | Replaced by a later ADR. The record itself still stands as written; see [Changing an earlier decision](#changing-an-earlier-decision). |

The status on the record is the authoritative one — the table below repeats it for browsing, so update both.

## Records

| ID | Title | Status |
|----|-------|--------|
| _none yet_ | | |

## Adding a new ADR

1. Copy [`template.md`](template.md) to a new file named `NNNN-short-title.md` in this directory, using the next
   sequential number (zero-padded to 4 digits).
2. Fill in Context, Decision, and Consequences.
3. Add a row to the table above.
4. Add the page to `nav:` in `mkdocs.yml`. The template itself is deliberately not listed there.

Numbers are claimed when the file is written, so two open pull requests can end up on the same one. Whoever
merges second renumbers.

## Changing an earlier decision

An accepted ADR is never rewritten, because the reasoning it records was true at the time and stays useful. To
change a decision:

1. Write a new ADR for the new decision, with a **Supersedes** line linking to the old one.
2. In the old ADR, set the status to `Superseded` and add a **Superseded by** line linking to the new one. This
   is the only edit ever made to an accepted record — leave its Context, Decision, and Consequences alone.
3. Update the status of both records in the table above.
