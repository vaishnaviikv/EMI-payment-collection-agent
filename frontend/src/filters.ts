export const stageGroups: Record<string, string[]> = {
  promise_to_pay: ["promise_to_pay", "PTP_TODAY", "PTP_TOMORROW", "PTP_FUTURE", "PTP_PARTIAL"],
  paid: ["paid", "ALREADY_PAID"],
  follow_up: ["follow_up", "CALLBACK_SCHEDULED"],
  unreachable: ["unreachable", "BUSY", "RNR", "VM", "DSCN"],
};

export function matchesStageGroup(stageCode: string, selectedGroup: string): boolean {
  if (selectedGroup === "all") return true;
  return (stageGroups[selectedGroup] || [selectedGroup]).includes(stageCode);
}
