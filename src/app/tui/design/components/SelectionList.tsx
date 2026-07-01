import { Box, Text, useInput } from "ink";
import { useState } from "react";
import { useTokens } from "../TokensContext";

export type SelectionItem = {
  label: string;
  value: string;
  hint?: string;
};

export type SelectionListProps = {
  items: SelectionItem[];
  onSelect?: (value: string) => void;
  isActive?: boolean;
};

export function SelectionList({ items, onSelect, isActive = true }: SelectionListProps) {
  const tokens = useTokens();
  const [index, setIndex] = useState(0);

  useInput(
    (_input, key) => {
      if (items.length === 0) {
        return;
      }

      if (key.upArrow) {
        setIndex((current) => (current - 1 + items.length) % items.length);
      } else if (key.downArrow) {
        setIndex((current) => (current + 1) % items.length);
      } else if (key.return) {
        onSelect?.(items[index]?.value ?? "");
      }
    },
    { isActive },
  );

  return (
    <Box flexDirection="column">
      {items.map((item, itemIndex) => {
        const selected = itemIndex === index;

        return (
          <Box key={item.value} gap={1}>
            <Text color={tokens.color("primary")}>{selected ? tokens.glyphs.prompt : " "}</Text>
            <Text color={selected ? tokens.color("text") : tokens.color("textMuted")}>
              {item.label}
            </Text>
            {item.hint !== undefined ? (
              <Text color={tokens.statusColor("ok")}>{item.hint}</Text>
            ) : null}
          </Box>
        );
      })}
    </Box>
  );
}
