---
name: tkay-grafana
description: Conventions for Grafana dashboards, panels and template variables. Use when creating or editing a dashboard, naming or labelling a template variable / picker / dropdown, writing panel descriptions, or reviewing dashboard JSON. Covers what belongs in a variable label versus a panel description.
---

# Grafana conventions

These are my house rules for dashboards, on top of Grafana's own JSON model.

## Variables get NAMES, not notes

**A variable's label is one or two words.** `Pod`, `Cluster`, `Category`,
`blacklisted`. Never a parenthetical or a trailing clause explaining which
panels the picker reaches, what the values mean, or when to use it -
`Category (verdict panels only)` and `blacklisted (validation-result panels
only)` are exactly the shape I do not want. Strip it to the name.

**Why:** the picker row is chrome I look at fifty times a day. A sentence
padded into a label widens the dropdown, truncates before it finishes
explaining itself, and duplicates something that already has a home: every
panel a picker cannot reach says so in its own description. Two copies of that
fact means one goes stale, and the label is the copy nobody updates.

## Fix the pattern, not the instance

When you catch one, tell me about every other variable with the same shape on
the boards in that repo - I would rather fix the pattern than one label.
