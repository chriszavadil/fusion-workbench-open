# Fusion research baton protocol

This project is not intended to run continuously in the background. It is intended to resume cleanly and work deeply whenever an active reasoning session is available.

## Core rule

A milestone, operational repair, reproduced baseline, failed test, completed simulation, or status report is a checkpoint—not a stopping condition.

After every checkpoint, the active worker must immediately:

1. record what changed;
2. classify the result as scientific evidence, infrastructure evidence, prior-art evidence, or no useful evidence;
3. select the highest-value unblocked next task;
4. execute it in the same active turn;
5. repeat until a real stop condition is reached.

## Research cycle

```text
LOAD BATON
  -> VERIFY CURRENT EVIDENCE
  -> RANK UNBLOCKED TASKS
  -> EXECUTE TOP TASK
  -> FALSIFY / VALIDATE
  -> UPDATE BATON
  -> SELECT NEXT TASK
  -> REPEAT
```

Intermediate progress is communicated as commentary updates. A final response is not used merely because a test finished or a report was generated.

## Parallelism rule

When one branch is waiting on compute, access, review, or a long solver run, continue an independent branch such as:

- prior-art verification;
- proof development;
- model-reduction checks;
- adversarial test design;
- independent-solver comparison;
- plant-impact translation;
- evidence packaging and reproducibility tests.

A blocked branch does not stop the program unless every useful branch is blocked.

## Baton contents

`CURRENT_RESEARCH_BATON.json` records:

- the verified scientific state;
- current candidate and validation level;
- ranked next actions;
- active blockers;
- recently completed checkpoints;
- explicit stop conditions;
- claim boundaries.

At the beginning of every new reasoning turn, read the baton before asking questions or selecting work. At the end of every substantial cycle, update it before reporting.

## What counts as a real stop

Stop only when one of the following is true:

- the current candidate is prospectively validated and the next step requires external experimental validation;
- the candidate is falsified and the ranked queue contains no useful follow-on branch;
- every remaining branch requires credentials, restricted data, physical hardware, explicit spending, or a safety decision;
- the user explicitly pauses the program;
- the active reasoning/tool budget is exhausted, in which case the baton must contain the exact next action so the following turn resumes without reconstruction.

## What does not count as a stop

- fixing our own script or workflow;
- producing a report;
- completing one simulation;
- reproducing prior art;
- discovering that one method is infeasible;
- finding a minor software defect;
- waiting for one branch while others remain available;
- reaching an interesting but unvalidated mathematical observation.

## Breakthrough language

An operational fix is never a breakthrough. A scientific breakthrough candidate requires all of the following:

- a nontrivial result not already established by prior art;
- prospective or held-out validation;
- an independent check or falsification attempt;
- a clear engineering consequence;
- explicit limitations and claim boundaries.

Until those conditions hold, use terms such as checkpoint, finding, counterexample candidate, reproduced result, or validation result.
