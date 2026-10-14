# Attention Adherence in a Structured LLM Memory System

## An empirical study on local inference (cases of study: Gemma4 26B and Qwen3.6 35B)

### Abstract

Large language models deployed locally for long-running agentic work share a common failure mode: the erosion of instruction adherence as the context window fills. The **Strict LLM Memory System** is a tool-driven, LLM-agnostic memory framework that governs short- and long-term memory through a structured system prompt (the *legend*) and a small set of Python CLI tools. The framework is model-agnostic and carries no preference for any model family or size: any tool-calling LLM can drive it. A dedicated legend variant for Gemma4 exists only because that family requires a flattened prompt structure and is validated by its own harness; the base memory system itself has no usage limits. This article reports on a revision program aimed at improving the *attention adherence* of the legend — the probability that the model honours its safety and workflow rules under realistic load — and presents the measured outcomes on two local models. The work raised the overall adherence of the Gemma4 26B legend from 63% to 100% and that of the Qwen3.6 35B legend from 63% to 87%, with the halt-on-tool-failure gap closed and a smaller residual confined to clarification on ambiguous orders, the latter traced in part to the inference configuration of the reasoning-distilled build.

### 1. The problem

In long sessions, an agent that must operate inside a strict perimeter (a project root), halt on destructive actions, stop on tool failure, and recap its intent before writing cannot rely on the model's implicit discipline alone. Empirically, when the legend was left in its original form, both target models exhibited three recurring failure classes:

1. **Impulsive action**: executing a write or tool call without first stating intent, leading to skipped steps and untraceable operations.
2. **Looping on failure**: on a tool error or an empty archive search, the model would improvise "next steps" — searching elsewhere, recreating missing files, or narrating hypothetical causes — instead of halting and asking for guidance.
3. **Ambiguity bypass**: acting on vague orders ("fix the thing") without requesting clarification.

A baseline measurement against a fixed set of behavioural probes returned 63% overall for both models: safety probes (root perimeter, destructive-action halt) were already saturated at 100%, but the procedural probes (intent recap, halt-on-failure, ambiguity handling) scored between 0% and 80%.

Memory layers for LLM agents broadly divide into OS-style paging of the context window and retrieval over vector stores. The system studied here is deliberately neither: it is a lightweight contract layer — a structured system prompt plus a handful of CLI tools, with no dependency beyond the Python standard library — that trades recall machinery for measurable rule adherence on models small enough to run locally. The object of study is not what the memory stores but whether the model obeys it.

### 2. Approach

The legend was revised along three orthogonal axes, each addressing one failure class. Throughout the program the tool set, the memory format, and the workflow were held unchanged — the revision touched the prompt alone; the workflow has since evolved separately, toward progressive memory (§6).

- **Structural reorganisation of the prompt** to exploit the known attention gradient of transformer decoders, placing the rules that must always hold at the positions of highest attentional weight, and the reference material consulted at every action near the prompt's closing boundary.
- **Introduction of an explicit intent-disclosure step** that the model must emit before any write or tool invocation, forcing the model to re-contextualise its state immediately before acting.
- **Reformulation of the governing rules in a telegraphic, imperative register**, isolating the critical halt tokens so that they carry maximal attentional weight and are not dissolved into prose.

Each revision was validated empirically against the same probe set, with multiple sampling runs at non-zero temperature to test stability rather than single-shot success. Two frozen legends — the original and the candidate — were compared head-to-head per probe, and only changes that produced no regression on any other probe were retained.

### 3. Results

| Probe family | Gemma4 26B (orig.) | Gemma4 26B (revised) | Qwen3.6 35B (orig.) | Qwen3.6 35B (revised) |
|---|---|---|---|---|
| Root perimeter | 100% | 100% | 100% | 100% |
| Destructive-action halt | 100% | 100% | 100% | 100% |
| Halt on tool failure | 100% | 100% | 40% | 100% |
| Intent disclosure before action | 0% | 100% | 0% | 100% |
| Halt on empty search results | 0% | 100% | 80% | 100% |
| Clarification on ambiguous orders | 80% | 100% | 60% | 20% |
| **Overall** | **63%** | **100%** | **63%** | **87%** |

The Gemma4 legend reached a perfect score and was promoted to the shipped version. The Qwen3.6 legend reached 87% overall, with five of six probe families at 100%; the residual is confined to a single probe family (clarification on ambiguous orders), and the earlier halt-on-tool-failure residual is now closed.

A secondary, unanticipated finding concerns **output economy**. Under the same legend, the two models differ markedly in verbosity: Gemma4 26B emits on the order of 176 output tokens per response, with a structured, explanatory style; Qwen3.6 35B emits on the order of 55–70 tokens per response, in a terse, telegraphic style. For local inference where output tokens are the bottleneck, Qwen3.6 is roughly three times more economical per turn, at the cost of the one unresolved probe. The choice between the two is therefore governed by the binding constraint — VRAM/output budget versus maximal behavioural strictness. These economy figures hold for the non-reasoning weight on which the measurements above were first taken; on a reasoning-distilled weight of the same model the chain-of-thought inflates output by a factor of roughly three to five, and the cost advantage of Qwen3.6 over Gemma4 narrows or reverses depending on whether the chain-of-thought is persisted into the transcript.

### 4. Difficulties overcome

Three difficulties emerged during the work and are worth recording.

**4.1 Behavioural coupling, revisited.** The probe families are not independent on a given model, and a rule introduced to fix one family can regress another. An earlier observation held that on Qwen3.6 an explicit rule directing the model to request clarification on ambiguous input resolved the ambiguity probe (60% → 100%) but regressed the halt-on-failure probe (40% → 20%). Re-examining this on a reasoning-distilled weight, with an output budget large enough for the chain-of-thought and reasoning parsing disabled, told a more instrumental story: halt-on-failure recovered to 100% and the residual migrated instead to clarification-on-ambiguous (100% → 20%). The earlier coupling was therefore partly a budget artefact rather than a genuine interaction of rules, and a rollback to the original legend would still forfeit the gains on five other families and return the overall score to 63%. The revised legend keeps the targeted failure-halt rule — not a rollback — and the single open item is now to recover the clarification behaviour on the reasoning-distilled build without losing the failure-halt gain.

**4.2 Token economy versus adherence.** The revised Gemma4 legend grows from roughly 973 to roughly 1 226 tokens (measured with a cl100k-base tokenizer). Because the legend is loaded once per session, the additional ~250 tokens amortise across the entire run. The trade is deliberate: a single missed halt or unauthorised destructive action costs more in wasted work or corrupted state than a few hundred tokens paid once. The framework therefore treats adherence and raw token economy as competing objectives and exposes the original, leaner structure as the reference to trim toward when VRAM dominates.

**4.3 Measurement validity.** Scoring free-form model output against expected behaviours is non-trivial. A naïve keyword match produces both false positives and false negatives: a model that *declines* to take forbidden next-steps still contains the phrase "next steps" inside a negation, while a genuinely compliant response may enumerate the very actions it refuses. The scoring logic was refined to distinguish an affirmation of restraint ("I cannot proceed with next-steps") from an affirmative proposal ("Next steps: I will...") by combining negation-aware matching for verbal predicates with strict, non-negation-tolerant matching for structural markers (section headers, numbered action lists). Auto-scoring remains approximate, but because it is applied identically across legends, the deltas are reliable; surprising cells are always cross-checked against the raw responses.

**4.4 Sensitivity to the inference configuration.** Re-running the validation on a reasoning-distilled weight of Qwen3.6 35B exposed a measurement hazard that had been implicit before. With reasoning parsing enabled and the default output budget of 400 tokens, the model spent essentially the entire budget on chain-of-thought and returned an empty response field, which the keyword scorer read as a hard failure on every probe — a regression that was entirely artefactual. Two adjustments restored a valid measurement: raising the output budget to about 2048 tokens so that the solicited answer emerges after the chain-of-thought, and disabling reasoning parsing so the final answer is not written to a separate field the scorer ignores. Under this pinned configuration the revised legend measures 87% overall on Qwen3.6, with halt-on-failure recovered to 100% and a smaller residual on clarification-on-ambiguous. The episode is a reminder that, for reasoning-distilled models, attention-adherence scores are meaningful only once the inference pipeline is pinned down; comparing legends across unrelated inference settings is not apples-to-apples.

### 5. Conclusion

A structured memory system's value is not only in what it stores but in whether the model actually obeys it. The revision program reported here raised adherence on the two target models by +37 and +24 percentage points respectively, with Gemma4 26B reaching a perfect score and Qwen3.6 35B reaching 87% under a pinned inference configuration, the halt-on-failure gap closed and a smaller residual confined to clarification on ambiguous orders. The work confirms that attention adherence is a tunable property of a structured prompt, that gains on one behaviour can interact with gains on another, and that the token cost of stricter behaviour is small and amortising. The open item — recovering the clarification-on-ambiguous behaviour on the reasoning-distilled Qwen3.6 build without regressing its sibling probes — is left as the next step.

### 6. Current state of the system

Subsequent to the program reported here, the workflow moved to **progressive memory**, closing the last write path the adherence campaign had left implicit. Committed entries are never rewritten: every correction is a new entry appended to the log (same date, different title). The CLI edit command is confined to drafting — it writes drafts to `temp.md` from stdin and refuses any other target with a message that states the rule and the sanctioned path, so an illegal invocation fails instructively instead of silently succeeding. The tool pool is closed over the memory lifecycle (draft → commit → compression → read-only access): one command per stage, no memory file reachable outside the CLI. Prompt rules and tool-surface enforcement are two layers of the same contract — the prompt states the rule, the tool refuses the violation.

### Materials

The framework — both legend variants, the CLI tool set, and the per-probe validation scores — is public at https://github.com/cosmok82/Strict_LLM_Memory_System. The frozen harness and its transcripts remain private.
