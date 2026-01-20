# Test Scenarios

Quick reference of all test cases. Full details in [`docs/05_testing_protocol.md`](../docs/05_testing_protocol.md).

## Test Matrix

| ID | Scenario | Category | Priority |
|---|---|---|---|
| TC-01 | Normal startup and operation | Functional | High |
| TC-02 | Emergency stop during operation | Safety | Critical |
| TC-03 | Jam detection at infeed | Fault Handling | High |
| TC-04 | Jam detection at diverter | Fault Handling | High |
| TC-05 | Jam detection at outfeed B | Fault Handling | Medium |
| TC-06 | Jam detection at outfeed C | Fault Handling | Medium |
| TC-07 | Fault clear rejected while PE blocked | Fault Handling | High |
| TC-08 | Diverter routing pattern | Functional | High |
| TC-09 | Manual mode jog control | Functional | Medium |
| TC-10 | Manual mode safety interlock | Safety | Critical |
| TC-11 | Adjustable jam timeout from HMI | Parameter | Medium |
| TC-12 | Metrics accuracy | Metrics | High |
| TC-13 | Bad parameter - low jam timeout | CI Experiment | Low |
| TC-14 | Start rejected during fault | Safety | High |

## Results Summary

| ID | Status | Date | Notes |
|---|---|---|---|
| TC-01 | -- | -- | -- |
| TC-02 | -- | -- | -- |
| TC-03 | -- | -- | -- |
| TC-04 | -- | -- | -- |
| TC-05 | -- | -- | -- |
| TC-06 | -- | -- | -- |
| TC-07 | -- | -- | -- |
| TC-08 | -- | -- | -- |
| TC-09 | -- | -- | -- |
| TC-10 | -- | -- | -- |
| TC-11 | -- | -- | -- |
| TC-12 | -- | -- | -- |
| TC-13 | -- | -- | -- |
| TC-14 | -- | -- | -- |

Fill in as tests are executed. Store screenshots and logs in `tests/results/`.
