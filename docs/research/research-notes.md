# Research Notes

Last updated: 2026-05-16

These notes summarize public material relevant to building a Poetiq-inspired harness generator. They should be treated as implementation guidance, not as authoritative claims about Poetiq's private system.

## Public Poetiq Claims

Poetiq describes its approach as building an intelligent ecosystem around existing LLMs rather than training new model weights. Their homepage says their system is intended to extract and synthesize fragmented information from LLMs, using self-improvement to adapt to model quirks and task demands.

Sources:

- [Poetiq homepage](https://poetiq.ai/)
- [Traversing the Frontier of Superintelligence](https://poetiq.ai/posts/arcagi_announcement/)
- [ARC-AGI-2 SOTA at Half the Cost](https://poetiq.ai/posts/arcagi_verified/)
- [Recursive Self-Improvement Delivers New State-of-the-Art Coding Performance](https://poetiq.ai/posts/recursive_self_improvement_coding/)

Key takeaways:

- The system is described as model-agnostic.
- The public examples focus on test-time reasoning, not fine-tuning.
- Poetiq reports improvements on ARC-AGI, Humanity's Last Exam/SimpleQA, and LiveCodeBench Pro.
- Public posts emphasize optimizing the whole harness: question strategy, sequential chains of questions, answer assembly, verification, model routing, and stopping decisions.
- For coding, Poetiq says the Meta-System created a LiveCodeBench Pro harness from scratch and optimized for accuracy, runtime, and memory.
- Poetiq's open ARC-AGI repository is a reproducibility artifact for specific benchmark configurations, not a full release of the private Meta-System.

## Related Research

### Meta-Harness

The Meta-Harness paper frames a harness as the code that controls what information is stored, retrieved, and presented to the model. It proposes an outer-loop system that searches over harness code using prior candidate source code, scores, and execution traces.

Source: [Meta-Harness: End-to-End Optimization of Model Harnesses](https://arxiv.org/abs/2603.28052)

Implications for this project:

- Store candidate harnesses as code, not just prompt strings.
- Persist the full archive: source, scorecards, traces, failure notes, and configuration.
- Let the proposer inspect prior evidence through a filesystem-style workspace.
- Evaluate candidate harnesses on held-out tasks and across models to reduce overfitting.

### AI Harness Engineering

The AI Harness Engineering paper argues that software-agent performance emerges from the model, harness, and environment together. It identifies responsibilities such as task specification, context selection, tool access, observability, failure attribution, verification, permissions, and intervention recording.

Source: [AI Harness Engineering: A Runtime Substrate for Foundation-Model Software Agents](https://arxiv.org/abs/2605.13357)

Implications for this project:

- Treat observability and verification as first-class features.
- Every run should produce an auditable episode package.
- Permissions, sandboxing, and intervention logs should be part of the harness, not bolted on later.

### Automated Design of Agentic Systems

Automated Design of Agentic Systems describes search over agentic systems, including code-defined agents, evaluation functions, and archives of previous discoveries.

Source: [Automated Design of Agentic Systems](https://openreview.net/pdf?id=D01WR1yVW2)

Implications for this project:

- Define the search space explicitly.
- Start with constrained candidate code so generated harnesses remain runnable and reviewable.
- Use validation scores to guide exploration, but maintain novelty and diversity to avoid local optima.

## Design Assumptions

- The first useful version does not need autonomous code generation. A prompt/config search loop can validate the runner, trace, and scoring layers first.
- Code search should be introduced only after deterministic candidate validation, sandboxing, and rollback are in place.
- The project should distinguish between the **inner harness** that solves tasks and the **outer optimizer** that proposes better harnesses.
- Model-provider abstraction is necessary from the start because model-agnostic claims are central to the premise.
- The system should prioritize reproducibility over headline scores.
- The first benchmark family is YouTube podcast speaker attribution. This requires speech-to-text, speaker diarization, speaker-name resolution, and human-labeled references.
- Official YouTube Data API caption download requires authorization and sufficient permissions for the caption track, so the project should support local user-provided media/captions as the default ingestion path.
- Current transcription/diarization options include OpenAI's diarized transcription API and pyannote-based diarization systems. The harness should treat these as replaceable providers rather than hard-code one backend.

Sources:

- [YouTube Data API captions.download](https://developers.google.com/youtube/v3/docs/captions/download)
- [OpenAI Audio Transcriptions API](https://platform.openai.com/docs/api-reference/audio/transcriptions)
- [OpenAI gpt-4o-transcribe-diarize model](https://developers.openai.com/api/docs/models/gpt-4o-transcribe-diarize)
- [pyannote.audio documentation](https://pyannote.github.io/pyannote-audio/)
- [pyannoteAI diarization documentation](https://docs.pyannote.ai/introduction)

## Open Questions

- What is the smallest task family that demonstrates clear harness lift over a naive baseline?
- Should the first candidate search space be YAML configs, Python classes, or a restricted DSL?
- Which traces are essential for improvement: full prompts, tool calls, model outputs, evaluator feedback, token counts, costs, or all of them?
- How should the system detect overfitting to the validation split?
- Which judge metrics can be deterministic, and which require LLM-as-judge scoring?
