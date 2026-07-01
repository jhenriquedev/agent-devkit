import { Text } from "ink";
import { useTokens } from "../TokensContext";
import type { RiskName, StatusName } from "../tokens";

export type PillProps = {
  label: string;
  status?: StatusName;
  risk?: RiskName;
  color?: string;
};

export function Pill({ label, status, risk, color }: PillProps) {
  const tokens = useTokens();
  const tone =
    color ??
    (status !== undefined
      ? tokens.statusColor(status)
      : risk !== undefined
        ? tokens.riskColor(risk)
        : tokens.color("textMuted"));

  return (
    <Text color={tone}>
      {tokens.glyphs.bulletActive} {label}
    </Text>
  );
}
