import { Box, Text } from "ink";

type AppProps = {
  initialPrompt?: string;
};

export function App({ initialPrompt }: AppProps) {
  return (
    <Box flexDirection="column">
      <Text bold>Agent DevKit</Text>
      <Text>v0.4.0 technical foundation</Text>
      {initialPrompt ? (
        <Text>Prompt: {initialPrompt}</Text>
      ) : (
        <Text>Run agent --help for CLI options.</Text>
      )}
    </Box>
  );
}
