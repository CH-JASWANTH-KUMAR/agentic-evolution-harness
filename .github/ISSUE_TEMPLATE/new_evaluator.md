---
name: New Evaluator Proposal
about: Propose or request a new evaluator plugin
title: "[EVALUATOR] "
labels: []
assignees: ""
---

### Evaluator Name
What should the evaluator be registered as? (e.g., `fuzzy_match`, `levenshtein`, `regex_capture`)

### Motivation
Why is this evaluator needed? What agent capabilities or failure modes does it test?

### Proposed Options / Parameters
What configurable options should this evaluator accept?
- `threshold: float`
- `ignore_case: bool`
- `...`

### Expected Output
How should the normalized score (0.0 to 1.0) and explanation be computed?

### Would you like to implement this?
- [ ] Yes, I would like to submit a Pull Request!
- [ ] No, this is an idea for someone else to implement.
