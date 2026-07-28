import { describe, expect, it } from "vitest";
import { matchesStageGroup } from "./filters";

describe("dashboard stage filters", () => {
  it.each(["promise_to_pay", "PTP_TODAY", "PTP_TOMORROW", "PTP_FUTURE", "PTP_PARTIAL"])(
    "groups %s under Promise to pay",
    (stage) => expect(matchesStageGroup(stage, "promise_to_pay")).toBe(true),
  );

  it("groups Gnani codes under the other normalized filters", () => {
    expect(matchesStageGroup("ALREADY_PAID", "paid")).toBe(true);
    expect(matchesStageGroup("CALLBACK_SCHEDULED", "follow_up")).toBe(true);
    expect(matchesStageGroup("DSCN", "unreachable")).toBe(true);
  });

  it("does not mix unrelated outcomes", () => {
    expect(matchesStageGroup("RTP_FINANCIAL", "promise_to_pay")).toBe(false);
    expect(matchesStageGroup("PTP_FUTURE", "paid")).toBe(false);
  });
});
