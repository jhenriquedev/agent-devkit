import type { CapabilityRepositoryPort } from "../../../../infra/bases/capability";
import type { AgentDataPath, AgentDataStore } from "../../../../infra/bases/data_store";
import { type AgentDevKitErrorCode, ErrorCodes } from "../../../../infra/bases/errors";
import { Result } from "../../../../infra/bases/result";
import { LocalAgentDataStore } from "../../../../infra/data";
import {
  type ContextProject,
  ContextProjectIndexSchema,
  ContextProjectSchema,
  type ContextProjectStatus,
} from "./projects.entities";

export type ContextProjectsRepositoryOptions = {
  clock?: () => Date;
  dataStore?: AgentDataStore;
};

export type CreateContextProjectInput = {
  description?: string;
  metadata?: Record<string, unknown>;
  name: string;
  path?: string;
  tags?: string[];
};

export type ListContextProjectsInput = {
  query?: string;
  status?: ContextProjectStatus | "all";
};

export type UpdateContextProjectInput = {
  description?: string;
  metadata?: Record<string, unknown>;
  name?: string;
  path?: string;
  projectId: string;
  tags?: string[];
};

export interface ContextProjectsRepositoryPort extends CapabilityRepositoryPort {
  archive(projectId: string): Promise<Result<AgentDevKitErrorCode, ContextProject>>;
  create(input: CreateContextProjectInput): Promise<Result<AgentDevKitErrorCode, ContextProject>>;
  delete(projectId: string, hard?: boolean): Promise<Result<AgentDevKitErrorCode, boolean>>;
  list(input?: ListContextProjectsInput): Promise<Result<AgentDevKitErrorCode, ContextProject[]>>;
  show(projectId: string): Promise<Result<AgentDevKitErrorCode, ContextProject>>;
  update(input: UpdateContextProjectInput): Promise<Result<AgentDevKitErrorCode, ContextProject>>;
}

const knowledgeBase = `# Project Knowledge Base

This file stores durable project knowledge promoted from sessions or written manually.
`;

function slugify(value: string): string {
  const slug = value
    .trim()
    .toLowerCase()
    .normalize("NFD")
    .replaceAll(/[\u0300-\u036f]/g, "")
    .replaceAll(/[^a-z0-9]+/g, "_")
    .replaceAll(/^_+|_+$/g, "");

  return slug.length > 0 ? slug : "project";
}

function includesQuery(project: ContextProject, query: string): boolean {
  const normalized = query.trim().toLowerCase();
  const haystack = [
    project.name,
    project.path,
    project.description,
    project.status,
    ...project.tags,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();

  return haystack.includes(normalized);
}

export class ContextProjectsRepository implements ContextProjectsRepositoryPort {
  readonly repositoryId = "context.projects.repository";
  readonly #clock: () => Date;
  readonly #dataStore: AgentDataStore;

  constructor(options: ContextProjectsRepositoryOptions = {}) {
    this.#clock = options.clock ?? (() => new Date());
    this.#dataStore = options.dataStore ?? new LocalAgentDataStore();
  }

  async archive(projectId: string): Promise<Result<AgentDevKitErrorCode, ContextProject>> {
    return this.#setStatus(projectId, "archived");
  }

  async create(
    input: CreateContextProjectInput,
  ): Promise<Result<AgentDevKitErrorCode, ContextProject>> {
    const id = await this.#uniqueProjectId(input.name);
    const now = this.#now();
    const project: ContextProject = {
      schema: "agent-devkit.context-project/v1",
      createdAt: now,
      description: input.description,
      id,
      metadata: input.metadata ?? {},
      name: input.name,
      path: input.path,
      status: "active",
      tags: input.tags ?? [],
      updatedAt: now,
    };

    const save = await this.#saveProject(project);

    if (save.isErr()) {
      return Result.fail(save.unwrapError());
    }

    const bootstrap = await this.#bootstrapProject(project.id);

    if (bootstrap.isErr()) {
      return Result.fail(bootstrap.unwrapError());
    }

    return Result.ok(project);
  }

  async delete(projectId: string, hard = false): Promise<Result<AgentDevKitErrorCode, boolean>> {
    if (hard) {
      const remove = await this.#dataStore.remove(this.#projectDirectory(projectId));
      return remove.isOk() ? Result.ok(true) : Result.fail(remove.unwrapError());
    }

    const project = await this.#setStatus(projectId, "deleted");
    return project.isOk() ? Result.ok(true) : Result.fail(project.unwrapError());
  }

  async list(
    input: ListContextProjectsInput = {},
  ): Promise<Result<AgentDevKitErrorCode, ContextProject[]>> {
    const projectsDirectory = { namespace: "context" as const, segments: ["projects"] };
    const exists = await this.#dataStore.exists(projectsDirectory);

    if (exists.isErr()) {
      return Result.fail(exists.unwrapError());
    }

    if (!exists.unwrap()) {
      return Result.ok([]);
    }

    const entries = await this.#dataStore.list(projectsDirectory);

    if (entries.isErr()) {
      return Result.fail(entries.unwrapError());
    }

    const projects: ContextProject[] = [];

    for (const entry of entries.unwrap().filter((candidate) => candidate.kind === "directory")) {
      const project = await this.#readProject(entry.name);

      if (project.isErr()) {
        return Result.fail(project.unwrapError());
      }

      projects.push(project.unwrap());
    }

    const status = input.status ?? "active";
    const query = input.query?.trim();

    return Result.ok(
      projects
        .filter((project) => status === "all" || project.status === status)
        .filter(
          (project) => query === undefined || query.length === 0 || includesQuery(project, query),
        )
        .sort((left, right) => right.updatedAt.localeCompare(left.updatedAt)),
    );
  }

  async show(projectId: string): Promise<Result<AgentDevKitErrorCode, ContextProject>> {
    return this.#readProject(projectId);
  }

  async update(
    input: UpdateContextProjectInput,
  ): Promise<Result<AgentDevKitErrorCode, ContextProject>> {
    const current = await this.#readProject(input.projectId);

    if (current.isErr()) {
      return Result.fail(current.unwrapError());
    }

    const updated: ContextProject = {
      ...current.unwrap(),
      description: input.description ?? current.unwrap().description,
      metadata: input.metadata ?? current.unwrap().metadata,
      name: input.name ?? current.unwrap().name,
      path: input.path ?? current.unwrap().path,
      tags: input.tags ?? current.unwrap().tags,
      updatedAt: this.#now(),
    };
    const save = await this.#saveProject(updated);

    return save.isOk() ? Result.ok(updated) : Result.fail(save.unwrapError());
  }

  async #bootstrapProject(projectId: string): Promise<Result<AgentDevKitErrorCode, void>> {
    const writes = [
      this.#dataStore.writeText(
        { namespace: "context", segments: ["projects", projectId, "knowledge", "base.md"] },
        knowledgeBase,
      ),
      this.#dataStore.writeJson(
        { namespace: "context", segments: ["projects", projectId, "knowledge", "index.json"] },
        { schema: "agent-devkit.context-knowledge-index/v1", projectId, entries: [] },
      ),
      this.#dataStore.writeText(
        { namespace: "context", segments: ["projects", projectId, "knowledge", "facts.jsonl"] },
        "",
      ),
      this.#dataStore.writeText(
        {
          namespace: "context",
          segments: ["projects", projectId, "knowledge", "decisions.jsonl"],
        },
        "",
      ),
      this.#dataStore.writeText(
        {
          namespace: "context",
          segments: ["projects", projectId, "knowledge", "preferences.jsonl"],
        },
        "",
      ),
      this.#dataStore.writeText(
        {
          namespace: "context",
          segments: ["projects", projectId, "knowledge", "references.jsonl"],
        },
        "",
      ),
      this.#dataStore.writeText(
        { namespace: "context", segments: ["projects", projectId, "sessions", ".keep"] },
        "",
      ),
    ];

    for (const write of await Promise.all(writes)) {
      if (write.isErr()) {
        return Result.fail(write.unwrapError());
      }
    }

    return Result.ok(undefined);
  }

  #index(project: ContextProject) {
    return ContextProjectIndexSchema.parse({
      schema: "agent-devkit.context-project-index/v1",
      description: project.description,
      id: project.id,
      name: project.name,
      path: project.path,
      status: project.status,
      tags: project.tags,
      updatedAt: project.updatedAt,
    });
  }

  async #readProject(projectId: string): Promise<Result<AgentDevKitErrorCode, ContextProject>> {
    const payload = await this.#dataStore.readJson<unknown>({
      namespace: "context",
      segments: ["projects", projectId, "project.json"],
    });

    if (payload.isErr()) {
      return Result.fail(payload.unwrapError());
    }

    const parsed = ContextProjectSchema.safeParse(payload.unwrap());
    return parsed.success ? Result.ok(parsed.data) : Result.fail(ErrorCodes.InvalidInput);
  }

  async #saveProject(project: ContextProject): Promise<Result<AgentDevKitErrorCode, void>> {
    const projectWrite = await this.#dataStore.writeJson(
      { namespace: "context", segments: ["projects", project.id, "project.json"] },
      project,
    );

    if (projectWrite.isErr()) {
      return Result.fail(projectWrite.unwrapError());
    }

    return this.#dataStore.writeJson(
      { namespace: "context", segments: ["projects", project.id, "index.json"] },
      this.#index(project),
    );
  }

  async #setStatus(
    projectId: string,
    status: ContextProjectStatus,
  ): Promise<Result<AgentDevKitErrorCode, ContextProject>> {
    const current = await this.#readProject(projectId);

    if (current.isErr()) {
      return Result.fail(current.unwrapError());
    }

    const updated: ContextProject = { ...current.unwrap(), status, updatedAt: this.#now() };
    const save = await this.#saveProject(updated);

    return save.isOk() ? Result.ok(updated) : Result.fail(save.unwrapError());
  }

  async #uniqueProjectId(name: string): Promise<string> {
    const base = `proj_${slugify(name)}`;
    let candidate = base;
    let index = 2;

    while ((await this.#dataStore.exists(this.#projectDirectory(candidate))).unwrap()) {
      candidate = `${base}_${index}`;
      index += 1;
    }

    return candidate;
  }

  #now(): string {
    return this.#clock().toISOString();
  }

  #projectDirectory(projectId: string): AgentDataPath {
    return { namespace: "context", segments: ["projects", projectId] };
  }
}
