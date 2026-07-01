import { Box, Text, useInput } from "ink";
import { useState } from "react";
import { useTokens } from "../TokensContext";

export type PromptInputProps = {
  placeholder?: string;
  onSubmit?: (value: string) => void;
  isActive?: boolean;
};

export function PromptInput({ placeholder, onSubmit, isActive = true }: PromptInputProps) {
  const tokens = useTokens();
  const [value, setValue] = useState("");

  useInput(
    (input, key) => {
      if (key.return) {
        onSubmit?.(value);
        setValue("");
      } else if (key.backspace || key.delete) {
        setValue((current) => current.slice(0, -1));
      } else if (input.length > 0 && !key.ctrl && !key.meta) {
        setValue((current) => current + input);
      }
    },
    { isActive },
  );

  const showPlaceholder = value.length === 0 && placeholder !== undefined;

  return (
    <Box gap={1}>
      <Text color={tokens.color("primary")}>{tokens.glyphs.prompt}</Text>
      <Text color={showPlaceholder ? tokens.color("textDim") : tokens.color("text")}>
        {showPlaceholder ? placeholder : value}
      </Text>
    </Box>
  );
}
