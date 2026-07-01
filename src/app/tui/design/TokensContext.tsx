import { createContext, type ReactNode, useContext, useMemo } from "react";
import type { DesignSemantics, KitSprite } from "../../../infra/bases/design";
import type { ThemeDefinition } from "../../../infra/bases/theme";
import { resolveTokens, type Tokens } from "./tokens";

export type TokensValue = Tokens & { kit: KitSprite };

const TokensContext = createContext<TokensValue | null>(null);

export type TokensProviderProps = {
  theme: ThemeDefinition;
  semantics: DesignSemantics;
  kit: KitSprite;
  children: ReactNode;
};

export function TokensProvider({ theme, semantics, kit, children }: TokensProviderProps) {
  const value = useMemo<TokensValue>(
    () => ({ ...resolveTokens(theme, semantics), kit }),
    [theme, semantics, kit],
  );

  return <TokensContext.Provider value={value}>{children}</TokensContext.Provider>;
}

export function useTokens(): TokensValue {
  const value = useContext(TokensContext);

  if (value === null) {
    throw new Error("useTokens must be used within a TokensProvider.");
  }

  return value;
}
