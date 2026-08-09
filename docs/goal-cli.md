# Goal-oriented CLI

Wilfred can plan and execute a natural-language goal through a configured planner provider.

Example:

`wilfred goal "what is your status?" --provider openai --model MODEL`

OpenAI credentials are never accepted as CLI arguments. The provider reads `WILFRED_OPENAI_API_KEY` from the environment.

`--confirmed` is the only goal CLI flag that explicitly grants ACTION confirmation. Without it, confirmation defaults to false.

DANGEROUS tools remain governed by the execution policy and are denied by the default policy.

The planner selects a registered tool and constructs its arguments. It does not execute tools or bypass execution policy.

The current planner contract produces one validated `ToolPlan` per goal. Multi-tool planning chains are not part of this CLI contract yet.

The command emits planning and execution results as JSON.
