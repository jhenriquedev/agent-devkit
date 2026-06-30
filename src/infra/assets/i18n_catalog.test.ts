import { I18nCatalog } from "./i18n_catalog";

describe("i18n catalog", () => {
  it("loads the embedded languages and translates known keys", async () => {
    const catalog = new I18nCatalog();

    const languages = await catalog.loadLanguages();
    const portuguese = await catalog.translate("pt-BR", "preferences.title");
    const english = await catalog.translate("en-US", "preferences.title");
    const french = await catalog.translate("fr-FR", "preferences.title");
    const chinese = await catalog.translate("zh-CN", "preferences.title");
    const japanese = await catalog.translate("ja-JP", "preferences.title");

    expect(languages.isOk()).toBe(true);
    expect(languages.unwrap().map((language) => language.id)).toEqual([
      "pt-BR",
      "en-US",
      "fr-FR",
      "zh-CN",
      "ja-JP",
    ]);
    expect(portuguese.unwrap()).toBe("Preferencias do Agent DevKit");
    expect(english.unwrap()).toBe("Agent DevKit Preferences");
    expect(french.unwrap()).toBe("Preferences Agent DevKit");
    expect(chinese.unwrap()).toBe("Agent DevKit 偏好设置");
    expect(japanese.unwrap()).toBe("Agent DevKit 設定");
  });
});
