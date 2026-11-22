# Every list is numbered, every table has a number column

**A list in a reply to me is numbered, never a bare dash, and a table's
first column numbers its rows under a `#` header**, so I answer "3" or
"row 2" instead of describing the item back to you. The reading list's
`R<n>`, the `Q<n>` of proposals and questions, a review's `B<n>` and the
tree's outline numbers are this rule with a letter in front; every other
list and table takes plain numbers. A list of one is numbered too, so every
list reads the same and a point is named the same way whether or not a
second one joins it. The one dash left under a label is "none", which is
no item, so it takes no number.

- **Every list starts with numbers, wherever it sits.** Its first level is
  `1`, `2`, and only an item's own sub-items go `a`, `b`, then `i`, `ii`,
  the way the tree does. Depth counts from the list's own top, never from
  the reply's margin: a list under a label line, a ❓ line or a dashed
  line is a list of its own and starts at `1` again, however deep that
  line sits. A reply that repeats a list or a table from an earlier reply
  keeps each item's number.
- **Every number that names an item is bold, wherever it stands**: a list
  item is a dash opening with its bold number, `- **1.** <item>`, at every
  depth, and a sub-item `- **a.** <item>`; a row number is `**1**`; so are
  `**R1.**`, `❓ **Q1**`, `**B1**` and the tree's `**1.b**`; and so is a
  number in prose that refers to an item - "see **Q3**", "**Why Not 2**",
  "**row 2**". Never a plain `1.` marker: markdown cannot bold it, and the
  terminal renders a `1.` list nested in another list with letters, so it
  shows as `a.`. Inside a code fence nothing is bolded, since the asterisks
  would show. The case that taught it, a Why Yes under a judgement:

  ```
  ❌ - **Why Yes?**
       1. <first>       (shows as "a.")
  ✅ - **Why Yes?**
       - **1.** <first>
  ```
- **Label lines keep their dash**, since nobody answers a label by number -
  "Call", "Why Yes?"; every point under a label is numbered, a single one
  included, so "Why Not 1" names one. The case that taught it, a Why Yes
  of one point beside a Gains of one:

  ```
  ❌ - **Why Yes?**
       - <the one point>
  ✅ - **Why Yes?**
       - **1.** <the one point>
  ```
- **A row's number is its name in my answer**, and the number column comes
  first, whatever the table is about.
- **It is for replies to me in chat** - never a commit message, a chat post
  or a file, whose own conventions hold.
