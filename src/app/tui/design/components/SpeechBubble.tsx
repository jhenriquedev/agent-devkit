import { Box, Text } from "ink";
import { useTokens } from "../TokensContext";
import { Kit } from "./Kit";

export type SpeechBubbleProps = {
  text: string;
  mood?: string;
  label?: string;
  animate?: boolean;
};

export function SpeechBubble({
  text,
  mood = "thinking",
  label,
  animate = true,
}: SpeechBubbleProps) {
  const tokens = useTokens();

  return (
    <Box gap={1}>
      <Kit mood={mood} animate={animate} />
      <Box
        flexDirection="column"
        borderStyle="round"
        borderColor={tokens.color("border")}
        paddingX={1}
      >
        {label !== undefined ? <Text color={tokens.color("textDim")}>{label}</Text> : null}
        <Text color={tokens.color("text")}>{text}</Text>
      </Box>
    </Box>
  );
}
