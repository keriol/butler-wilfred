# Provider latency acknowledgement

Voice and conversational consumers can emit a short acknowledgement before Wilfred starts goal planning, avoiding perceived silence.

The acknowledgement is optional and belongs to the interaction layer, not to a planner provider.

A consumer supplies an `OutputAdapter` through `acknowledgement_adapter` and localized `acknowledgement_text`, for example `"Ci sto pensando."`.

`WilfredRuntime.execute_goal()` attempts delivery immediately before calling the planner.

Delivery is best-effort. Failure does not block planning.

An acknowledgement never confirms an ACTION or DANGEROUS tool and never changes execution policy.

Wilfred provides no default phrase. Consumers choose wording and concrete output integration.
