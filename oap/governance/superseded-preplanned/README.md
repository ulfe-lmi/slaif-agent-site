# Superseded preplanned orders

This directory holds inert preplanned order files that were retired from
`oap/orders/` before their identifier was next activated. The move is the
supersession marker: the file content is preserved byte-identical and the
file is no longer an order.

## `079-a-agent-media-semantics.md`

Moved by OAP work order 078-9-a (R5). `tools/check_repository.py` enforces
that each OAP order identifier appears in exactly one order file in
`oap/orders/`, and the next activation is `079-a` per the human directive
of 2026-09-20 (D2). The preplanned 079-a content is superseded by the 079
order that strategy publishes when `079-a` is activated; the file retained
here is historical preparation only and carries no operative effect.

The other inert preplanned orders (`080-a` through `091-a`) remain in
`oap/orders/` and stay inert until strategy selects and signals them.
