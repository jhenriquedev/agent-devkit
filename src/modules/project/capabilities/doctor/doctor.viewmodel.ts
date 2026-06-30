import { I18nCatalog } from "../../../../infra/assets/i18n_catalog";
import type { Translator } from "../../../../infra/bases/i18n";
import type { DoctorReport, DoctorStatePath } from "./doctor.entities";

type FormatDoctorTextOptions = {
  color?: boolean;
  translator?: Translator;
};

const colors = {
  dim: "#9D98B8",
  error: "#E87A8E",
  indigo: "#8B7AE6",
  ok: "#5FD0C8",
  text: "#E8E6F2",
};
const defaultTranslator = new I18nCatalog().translator("en-US");

function colorize(value: string, hex: string, enabled: boolean): string {
  if (!enabled) {
    return value;
  }

  const [red, green, blue] = [hex.slice(1, 3), hex.slice(3, 5), hex.slice(5, 7)].map((part) =>
    Number.parseInt(part, 16),
  );

  return `\u001b[38;2;${red};${green};${blue}m${value}\u001b[0m`;
}

function stateStatus(state: DoctorStatePath): string {
  return state.exists ? "found" : "missing";
}

function statusColor(status: string): string {
  if (status === "ok" || status === "found") {
    return colors.ok;
  }

  if (status === "missing") {
    return colors.dim;
  }

  return colors.error;
}

function pill(label: string, enabled: boolean): string {
  const value = `[${label}]`;
  return colorize(value, statusColor(label), enabled);
}

function statusText(status: string, label: string, enabled: boolean): string {
  return colorize(label, statusColor(status), enabled);
}

function section(title: string, rows: Array<[string, string]>, enabled: boolean): string[] {
  return [
    colorize(`  ${title}`, colors.indigo, enabled),
    ...rows.map(([label, value]) => `    ${label.padEnd(7)} ${value}`),
  ];
}

export function formatDoctorText(
  report: DoctorReport,
  options: FormatDoctorTextOptions = {},
): string {
  const color = options.color === true;
  const translator = options.translator ?? defaultTranslator;
  const t = (key: string, values?: Record<string, string>) => translator.t(key, values);
  const globalStatus = stateStatus(report.runtime.globalState);
  const projectStatus = stateStatus(report.runtime.projectState);
  const globalStatusLabel = t(`doctor.status.${globalStatus}`);
  const projectStatusLabel = t(`doctor.status.${projectStatus}`);

  return [
    `${colorize(t("doctor.title"), colors.text, color)}  ${colorize(t("doctor.subtitle"), colors.dim, color)}`,
    colorize(t("doctor.command"), colors.indigo, color),
    "",
    `${pill(report.status, color)} ${t("doctor.health")}`,
    ...section(
      t("doctor.section.runtime"),
      [
        [t("doctor.field.version"), report.version],
        [t("doctor.field.node"), report.node.version],
      ],
      color,
    ),
    ...section(
      t("doctor.section.environment"),
      [
        [t("doctor.field.platform"), report.system.platform],
        [t("doctor.field.cwd"), report.system.cwd],
        [
          t("doctor.field.tty"),
          `stdin=${String(report.terminal.stdinIsTTY)} stdout=${String(report.terminal.stdoutIsTTY)}`,
        ],
      ],
      color,
    ),
    ...section(
      t("doctor.section.state"),
      [
        [
          t("doctor.field.global"),
          `${statusText(globalStatus, globalStatusLabel, color).padEnd(8)} ${report.runtime.globalState.path}`,
        ],
        [
          t("doctor.field.project"),
          `${statusText(projectStatus, projectStatusLabel, color).padEnd(8)} ${report.runtime.projectState.path}`,
        ],
      ],
      color,
    ),
    "",
    t("doctor.line.version", { version: report.version }),
    t("doctor.line.globalState", {
      path: report.runtime.globalState.path,
      status: globalStatusLabel,
    }),
    t("doctor.line.projectState", {
      path: report.runtime.projectState.path,
      status: projectStatusLabel,
    }),
  ].join("\n");
}
