# Failure Modes

## False Assignment

A real person is assigned to a segment spoken by someone else. This is the primary risk and should be treated as more severe than an unknown label.

## False Merge

Two different people are collapsed into one identity.

## False Split

One person is split into multiple speaker or person identities.

## Unknown Miss

An unknown speaker is incorrectly forced into the known-speaker registry.

## Weak Evidence Assignment

The resolver assigns a person using insufficient or unsupported evidence, such as short audio, low-quality face detection, or transcript-only inference.

## Registry Poisoning

Incorrect automatic labels are fed back into the known-person registry and influence future assignments.

## Biometric Leakage

Raw embeddings, face crops, raw frames, or other sensitive internals are exposed through public artifacts.

## Metric Gaming

A strategy improves raw identity accuracy or recall while increasing false assignments, false merges, or unsafe automatic identity decisions.

