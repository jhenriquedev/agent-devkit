import { Box, Text } from "ink";
import { useTokens } from "../TokensContext";

export type StepState = "done" | "active" | "idle";

export type Step = {
  label: string;
  state: StepState;
};

export type StepListProps = {
  steps: Step[];
};

export function StepList({ steps }: StepListProps) {
  const tokens = useTokens();

  const glyphFor = (state: StepState): string => {
    if (state === "done") {
      return tokens.glyphs.check;
    }

    return state === "active" ? tokens.glyphs.bulletActive : tokens.glyphs.bulletIdle;
  };

  const glyphColor = (state: StepState): string => {
    if (state === "done") {
      return tokens.statusColor("ok");
    }

    return state === "active" ? tokens.color("primary") : tokens.color("textDim");
  };

  return (
    <Box flexDirection="column">
      {steps.map((step) => (
        <Box key={step.label} gap={1}>
          <Text color={glyphColor(step.state)}>{glyphFor(step.state)}</Text>
          <Text color={step.state === "idle" ? tokens.color("textDim") : tokens.color("text")}>
            {step.label}
          </Text>
        </Box>
      ))}
    </Box>
  );
}
