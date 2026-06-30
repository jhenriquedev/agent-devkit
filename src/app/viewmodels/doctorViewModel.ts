import type { DoctorReport, DoctorStatePath } from "../../domain/entities/DoctorReport";

type FormatDoctorTextOptions = {
  color?: boolean;
};

const colors = {
  dim: "#9D98B8",
  error: "#E87A8E",
  indigo: "#8B7AE6",
  ok: "#5FD0C8",
  text: "#E8E6F2",
};

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

function statusText(label: string, enabled: boolean): string {
  return colorize(label, statusColor(label), enabled);
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
  const globalStatus = stateStatus(report.runtime.globalState);
  const projectStatus = stateStatus(report.runtime.projectState);

  return [
    `${colorize("Agent DevKit Doctor", colors.text, color)}  ${colorize("local - no credentials required", colors.dim, color)}`,
    `${colorize(">", colors.indigo, color)} agent doctor`,
    "",
    `${pill(report.status, color)} local health`,
    ...section(
      "runtime",
      [
        ["version", report.version],
        ["node", report.node.version],
      ],
      color,
    ),
    ...section(
      "environment",
      [
        ["platform", report.system.platform],
        ["cwd", report.system.cwd],
        [
          "tty",
          `stdin=${String(report.terminal.stdinIsTTY)} stdout=${String(report.terminal.stdoutIsTTY)}`,
        ],
      ],
      color,
    ),
    ...section(
      "state",
      [
        [
          "global",
          `${statusText(globalStatus, color).padEnd(8)} ${report.runtime.globalState.path}`,
        ],
        [
          "project",
          `${statusText(projectStatus, color).padEnd(8)} ${report.runtime.projectState.path}`,
        ],
      ],
      color,
    ),
    "",
    `Version: ${report.version}`,
    `Global state: ${globalStatus} (${report.runtime.globalState.path})`,
    `Project state: ${projectStatus} (${report.runtime.projectState.path})`,
  ].join("\n");
}
