import { Box, Text } from "ink";
import type { Translator } from "../../infra/bases/i18n";

type AppProps = {
  initialPrompt?: string;
  translator: Translator;
};

export function App({ initialPrompt, translator }: AppProps) {
  return (
    <Box flexDirection="column">
      <Text bold>{translator.t("tui.title")}</Text>
      <Text>{translator.t("tui.foundation")}</Text>
      {initialPrompt ? (
        <Text>{translator.t("tui.prompt", { prompt: initialPrompt })}</Text>
      ) : (
        <Text>{translator.t("tui.helpHint")}</Text>
      )}
    </Box>
  );
}
