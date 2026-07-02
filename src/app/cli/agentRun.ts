import { homedir } from "node:os";
import { AgentRuntime, type AgentStreamEvent } from "../../infra/agent/agent_runtime";
import { createBrainDockProvider } from "../../infra/brain/brain_dock";
import { createCliToolRuntime } from "./toolRuntime";

export type RunAgentTaskOptions = {
  approved?: boolean;
  currentVersion: string;
  json?: boolean;
  packageName: string;
};

function printEvent(event: AgentStreamEvent): void {
  if (event.type === "tool") {
    process.stdout.write(`\n· ${event.tool} …\n`);
    return;
  }

  if (event.type === "observation") {
    process.stdout.write(`  ${event.ok ? "✓" : "✕"} ${event.summary}\n`);
    return;
  }

  process.stdout.write(`\n${event.reply}\n`);
}

export async function runAgentTask(task: string, options: RunAgentTaskOptions): Promise<void> {
  const toolRuntime = createCliToolRuntime({
    currentVersion: options.currentVersion,
    packageName: options.packageName,
  });
  const agent = new AgentRuntime({
    brainProvider: createBrainDockProvider({ stateDirectory: `${homedir()}/.agent-devkit` }),
    toolRuntime,
  });
  const streaming = options.json !== true && process.stdout.isTTY === true;

  const result = await agent.run({
    approved: options.approved,
    onEvent: streaming ? printEvent : undefined,
    task,
  });

  if (result.isErr()) {
    throw new Error(result.unwrapError());
  }

  const payload = result.unwrap();

  if (options.json === true) {
    console.log(JSON.stringify(payload, null, 2));
    return;
  }

  if (!streaming) {
    for (const step of payload.steps) {
      console.log(`· ${step.tool}: ${step.summary}`);
    }

    console.log(payload.reply);
  }
}
