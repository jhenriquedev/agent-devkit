import type { CapabilityRepositoryPort } from "../../../../infra/bases/capability";
import type { AgentDataPath, AgentDataStore } from "../../../../infra/bases/data_store";
import { type AgentDevKitErrorCode, ErrorCodes } from "../../../../infra/bases/errors";
import { Result } from "../../../../infra/bases/result";
import { LocalAgentDataStore } from "../../../../infra/data";
import { ContextProjectSchema } from "../projects/projects.entities";
import {
  type ContextMessage,
  type ContextMessageKind,
  type ContextMessageRole,
  ContextMessageSchema,
  type ContextSession,
  type ContextSessionIndex,
  ContextSessionIndexSchema,
  ContextSessionSchema,
  type ContextSessionSearchResult,
  type ContextSessionStatus,
} from "./sessions.entities";

export type ContextSessionsRepositoryOptions = {
  clock?: () => Date;
  dataStore?: AgentDataStore;
  idFactory?: () => string;
  messageIdFactory?: () => string;
};

export type CreateContextSessionInput = {
  metadata?: Record<string, unknown>;
  origin: ContextSession["origin"];
  projectId?: string;
  tags?: string[];
  title?: string;
};

export type AppendContextMessageInput = {
  content: string;
  kind?: ContextMessageKind;
  metadata?: Record<string, unknown>;
  role: ContextMessageRole;
  sessionId: string;
};

export type ListContextSessionsInput = {
  limit?: number;
  projectId?: string;
  query?: string;
  status?: ContextSessionStatus | "all";
};

export type ShowContextSessionInput = {
  includeMessages?: boolean;
  limit?: number;
  sessionId: string;
};

export type SearchContextSessionsInput = {
  limit?: number;
  projectId?: string;
  query: string;
};

export type ContextSessionDetails = {
  index: ContextSessionIndex;
  messages?: ContextMessage[];
  session: ContextSession;
};

export interface ContextSessionsRepositoryPort extends CapabilityRepositoryPort {
  appendMessage(
    input: AppendContextMessageInput,
  ): Promise<
    Result<
      AgentDevKitErrorCode,
      { index: ContextSessionIndex; message: ContextMessage; session: ContextSession }
    >
  >;
  archive(sessionId: string): Promise<Result<AgentDevKitErrorCode, ContextSessionDetails>>;
  create(input: CreateContextSessionInput): Promise<Result<AgentDevKitErrorCode, ContextSession>>;
  delete(sessionId: string, hard?: boolean): Promise<Result<AgentDevKitErrorCode, boolean>>;
  list(
    input?: ListContextSessionsInput,
  ): Promise<Result<AgentDevKitErrorCode, ContextSessionIndex[]>>;
  resume(sessionId: string): Promise<Result<AgentDevKitErrorCode, ContextSessionDetails>>;
  search(
    input: SearchContextSessionsInput,
  ): Promise<Result<AgentDevKitErrorCode, ContextSessionSearchResult[]>>;
  show(
    input: ShowContextSessionInput,
  ): Promise<Result<AgentDevKitErrorCode, ContextSessionDetails>>;
}

const stopwords = new Set([
  "a",
  "as",
  "com",
  "da",
  "de",
  "do",
  "e",
  "for",
  "in",
  "of",
  "o",
  "os",
  "para",
  "the",
  "to",
  "um",
  "uma",
]);

function compactWhitespace(value: string): string {
  return value.replaceAll(/\s+/g, " ").trim();
}

function generateId(prefix: string): string {
  return `${prefix}_${crypto.randomUUID().replaceAll("-", "").slice(0, 26)}`;
}

function keywordsFor(values: string[], max = 12): string[] {
  const counts = new Map<string, number>();

  for (const token of values
    .join(" ")
    .toLowerCase()
    .normalize("NFD")
    .replaceAll(/[\u0300-\u036f]/g, "")
    .split(/[^a-z0-9]+/g)
    .filter((candidate) => candidate.length > 3 && !stopwords.has(candidate))) {
    counts.set(token, (counts.get(token) ?? 0) + 1);
  }

  return [...counts.entries()]
    .sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0]))
    .slice(0, max)
    .map(([token]) => token);
}

function scoreText(haystack: string, query: string): number {
  const normalizedHaystack = haystack.toLowerCase();
  const normalizedQuery = query.toLowerCase();
  let score = 0;
  let index = normalizedHaystack.indexOf(normalizedQuery);

  while (index >= 0) {
    score += 1;
    index = normalizedHaystack.indexOf(normalizedQuery, index + normalizedQuery.length);
  }

  return score;
}

export class ContextSessionsRepository implements ContextSessionsRepositoryPort {
  readonly repositoryId = "context.sessions.repository";
  readonly #clock: () => Date;
  readonly #dataStore: AgentDataStore;
  readonly #idFactory: () => string;
  readonly #messageIdFactory: () => string;

  constructor(options: ContextSessionsRepositoryOptions = {}) {
    this.#clock = options.clock ?? (() => new Date());
    this.#dataStore = options.dataStore ?? new LocalAgentDataStore();
    this.#idFactory = options.idFactory ?? (() => generateId("ses"));
    this.#messageIdFactory = options.messageIdFactory ?? (() => generateId("msg"));
  }

  async appendMessage(
    input: AppendContextMessageInput,
  ): Promise<
    Result<
      AgentDevKitErrorCode,
      { index: ContextSessionIndex; message: ContextMessage; session: ContextSession }
    >
  > {
    const current = await this.#readSessionById(input.sessionId);

    if (current.isErr()) {
      return Result.fail(current.unwrapError());
    }

    const { session } = current.unwrap();
    const now = this.#now();
    const message: ContextMessage = {
      schema: "agent-devkit.context-message/v1",
      content: input.content,
      createdAt: now,
      id: this.#messageIdFactory(),
      kind: input.kind ?? "message",
      metadata: input.metadata ?? {},
      role: input.role,
      sessionId: input.sessionId,
    };
    const parsedMessage = ContextMessageSchema.safeParse(message);

    if (!parsedMessage.success) {
      return Result.fail(ErrorCodes.InvalidInput);
    }

    const nextSession: ContextSession = {
      ...session,
      lastMessageAt: now,
      title:
        session.title === "Untitled session" && message.role === "user"
          ? compactWhitespace(message.content).slice(0, 80) || session.title
          : session.title,
      updatedAt: now,
    };
    const parsedSession = ContextSessionSchema.safeParse(nextSession);

    if (!parsedSession.success) {
      return Result.fail(ErrorCodes.InvalidInput);
    }

    const writeMessage = await this.#dataStore.appendJsonl(
      this.#sessionPath(parsedSession.data, "messages.jsonl"),
      parsedMessage.data,
    );

    if (writeMessage.isErr()) {
      return Result.fail(writeMessage.unwrapError());
    }

    const messages = await this.#readMessages(parsedSession.data);

    if (messages.isErr()) {
      return Result.fail(messages.unwrapError());
    }

    const save = await this.#saveSession(parsedSession.data, messages.unwrap());

    if (save.isErr()) {
      return Result.fail(save.unwrapError());
    }

    return Result.ok({
      index: this.#index(nextSession, messages.unwrap()),
      message: parsedMessage.data,
      session: parsedSession.data,
    });
  }

  async archive(sessionId: string): Promise<Result<AgentDevKitErrorCode, ContextSessionDetails>> {
    const updated = await this.#setStatus(sessionId, "archived");

    if (updated.isErr()) {
      return Result.fail(updated.unwrapError());
    }

    return this.show({ includeMessages: false, sessionId });
  }

  async create(
    input: CreateContextSessionInput,
  ): Promise<Result<AgentDevKitErrorCode, ContextSession>> {
    if (input.projectId !== undefined) {
      const project = await this.#validateProjectExists(input.projectId);

      if (project.isErr()) {
        return Result.fail(project.unwrapError());
      }
    }

    const now = this.#now();
    const session: ContextSession = {
      schema: "agent-devkit.context-session/v1",
      createdAt: now,
      id: this.#idFactory(),
      metadata: input.metadata ?? {},
      origin: input.origin,
      projectId: input.projectId,
      status: "active",
      tags: input.tags ?? [],
      title: input.title ?? "Untitled session",
      updatedAt: now,
    };
    const parsedSession = ContextSessionSchema.safeParse(session);

    if (!parsedSession.success) {
      return Result.fail(ErrorCodes.InvalidInput);
    }

    const save = await this.#saveSession(parsedSession.data, []);

    return save.isOk() ? Result.ok(parsedSession.data) : Result.fail(save.unwrapError());
  }

  async delete(sessionId: string, hard = false): Promise<Result<AgentDevKitErrorCode, boolean>> {
    const current = await this.#readSessionById(sessionId);

    if (current.isErr()) {
      return Result.fail(current.unwrapError());
    }

    if (hard) {
      const remove = await this.#dataStore.remove(this.#sessionDirectory(current.unwrap().session));
      return remove.isOk() ? Result.ok(true) : Result.fail(remove.unwrapError());
    }

    const updated = await this.#setStatus(sessionId, "deleted");
    return updated.isOk() ? Result.ok(true) : Result.fail(updated.unwrapError());
  }

  async list(
    input: ListContextSessionsInput = {},
  ): Promise<Result<AgentDevKitErrorCode, ContextSessionIndex[]>> {
    const entries = await this.#allSessionReferences(input.projectId);

    if (entries.isErr()) {
      return Result.fail(entries.unwrapError());
    }

    const status = input.status ?? "active";
    const query = input.query?.trim();
    const indexes: ContextSessionIndex[] = [];

    for (const session of entries.unwrap()) {
      const index = await this.#readIndex(session);

      if (index.isErr()) {
        return Result.fail(index.unwrapError());
      }

      indexes.push(index.unwrap());
    }

    return Result.ok(
      indexes
        .filter((index) => status === "all" || index.status === status)
        .filter((index) => query === undefined || this.#indexMatches(index, query))
        .sort((left, right) => right.updatedAt.localeCompare(left.updatedAt))
        .slice(0, input.limit ?? 20),
    );
  }

  async resume(sessionId: string): Promise<Result<AgentDevKitErrorCode, ContextSessionDetails>> {
    const current = await this.#readSessionById(sessionId);

    if (current.isErr()) {
      return Result.fail(current.unwrapError());
    }

    if (current.unwrap().session.status !== "active") {
      const updated = await this.#setStatus(sessionId, "active");

      if (updated.isErr()) {
        return Result.fail(updated.unwrapError());
      }
    }

    return this.show({ includeMessages: true, limit: 20, sessionId });
  }

  async search(
    input: SearchContextSessionsInput,
  ): Promise<Result<AgentDevKitErrorCode, ContextSessionSearchResult[]>> {
    const entries = await this.#allSessionReferences(input.projectId);

    if (entries.isErr()) {
      return Result.fail(entries.unwrapError());
    }

    const results: ContextSessionSearchResult[] = [];

    for (const reference of entries.unwrap()) {
      const index = await this.#readIndex(reference);
      const messages = await this.#readMessages(reference.session);

      if (index.isErr()) {
        return Result.fail(index.unwrapError());
      }

      if (messages.isErr()) {
        return Result.fail(messages.unwrapError());
      }

      const haystack = [
        index.unwrap().title,
        index.unwrap().preview,
        index.unwrap().keywords.join(" "),
        ...messages.unwrap().map((message) => message.content),
      ].join(" ");
      const score = scoreText(haystack, input.query);

      if (score > 0 && index.unwrap().status !== "deleted") {
        results.push({ ...index.unwrap(), score });
      }
    }

    return Result.ok(
      results
        .sort(
          (left, right) =>
            right.score - left.score || right.updatedAt.localeCompare(left.updatedAt),
        )
        .slice(0, input.limit ?? 20),
    );
  }

  async show(
    input: ShowContextSessionInput,
  ): Promise<Result<AgentDevKitErrorCode, ContextSessionDetails>> {
    const current = await this.#readSessionById(input.sessionId);

    if (current.isErr()) {
      return Result.fail(current.unwrapError());
    }

    const index = await this.#readIndex(current.unwrap());

    if (index.isErr()) {
      return Result.fail(index.unwrapError());
    }

    if (input.includeMessages !== true) {
      return Result.ok({ index: index.unwrap(), session: current.unwrap().session });
    }

    const messages = await this.#readMessages(current.unwrap().session);

    if (messages.isErr()) {
      return Result.fail(messages.unwrapError());
    }

    return Result.ok({
      index: index.unwrap(),
      messages: messages.unwrap().slice(-(input.limit ?? messages.unwrap().length)),
      session: current.unwrap().session,
    });
  }

  async #allSessionReferences(
    projectId?: string,
  ): Promise<Result<AgentDevKitErrorCode, Array<{ session: ContextSession }>>> {
    const references: Array<{ session: ContextSession }> = [];
    const roots =
      projectId === undefined ? await this.#sessionRoots() : [this.#projectSessionsRoot(projectId)];

    for (const root of roots) {
      const exists = await this.#dataStore.exists(root);

      if (exists.isErr()) {
        return Result.fail(exists.unwrapError());
      }

      if (!exists.unwrap()) {
        continue;
      }

      const entries = await this.#dataStore.list(root);

      if (entries.isErr()) {
        return Result.fail(entries.unwrapError());
      }

      for (const entry of entries.unwrap().filter((candidate) => candidate.kind === "directory")) {
        const session = await this.#readSessionAt({
          namespace: "context",
          segments: [...entry.path.segments, "session.json"],
        });

        if (session.isOk()) {
          references.push({ session: session.unwrap() });
        }
      }
    }

    return Result.ok(references);
  }

  async #readSessionById(
    sessionId: string,
  ): Promise<Result<AgentDevKitErrorCode, { session: ContextSession }>> {
    const references = await this.#allSessionReferences();

    if (references.isErr()) {
      return Result.fail(references.unwrapError());
    }

    const found = references.unwrap().find((reference) => reference.session.id === sessionId);

    return found === undefined ? Result.fail(ErrorCodes.InvalidInput) : Result.ok(found);
  }

  async #readSessionAt(path: AgentDataPath): Promise<Result<AgentDevKitErrorCode, ContextSession>> {
    const payload = await this.#dataStore.readJson<unknown>(path);

    if (payload.isErr()) {
      return Result.fail(payload.unwrapError());
    }

    const parsed = ContextSessionSchema.safeParse(payload.unwrap());
    return parsed.success ? Result.ok(parsed.data) : Result.fail(ErrorCodes.InvalidInput);
  }

  async #saveSession(
    session: ContextSession,
    messages: ContextMessage[],
  ): Promise<Result<AgentDevKitErrorCode, void>> {
    const sessionWrite = await this.#dataStore.writeJson(
      this.#sessionPath(session, "session.json"),
      session,
    );

    if (sessionWrite.isErr()) {
      return Result.fail(sessionWrite.unwrapError());
    }

    const indexWrite = await this.#dataStore.writeJson(
      this.#sessionPath(session, "index.json"),
      this.#index(session, messages),
    );

    if (indexWrite.isErr()) {
      return Result.fail(indexWrite.unwrapError());
    }

    return this.#dataStore.writeText(
      this.#sessionPath(session, "summary.md"),
      this.#summary(session, messages),
    );
  }

  async #setStatus(
    sessionId: string,
    status: ContextSessionStatus,
  ): Promise<Result<AgentDevKitErrorCode, ContextSession>> {
    const current = await this.#readSessionById(sessionId);

    if (current.isErr()) {
      return Result.fail(current.unwrapError());
    }

    const messages = await this.#readMessages(current.unwrap().session);

    if (messages.isErr()) {
      return Result.fail(messages.unwrapError());
    }

    const session: ContextSession = {
      ...current.unwrap().session,
      status,
      updatedAt: this.#now(),
    };
    const save = await this.#saveSession(session, messages.unwrap());

    return save.isOk() ? Result.ok(session) : Result.fail(save.unwrapError());
  }

  async #validateProjectExists(projectId: string): Promise<Result<AgentDevKitErrorCode, void>> {
    const path: AgentDataPath = {
      namespace: "context",
      segments: ["projects", projectId, "project.json"],
    };
    const exists = await this.#dataStore.exists(path);

    if (exists.isErr()) {
      return Result.fail(exists.unwrapError());
    }

    if (!exists.unwrap()) {
      return Result.fail(ErrorCodes.InvalidInput);
    }

    const project = await this.#dataStore.readJson<unknown>(path);

    if (project.isErr()) {
      return Result.fail(project.unwrapError());
    }

    return ContextProjectSchema.safeParse(project.unwrap()).success
      ? Result.ok(undefined)
      : Result.fail(ErrorCodes.InvalidInput);
  }

  async #sessionRoots(): Promise<AgentDataPath[]> {
    const roots: AgentDataPath[] = [{ namespace: "context", segments: ["sessions"] }];
    const projectsRoot: AgentDataPath = { namespace: "context", segments: ["projects"] };
    const exists = await this.#dataStore.exists(projectsRoot);

    if (exists.isErr() || !exists.unwrap()) {
      return roots;
    }

    const projects = await this.#dataStore.list(projectsRoot);

    if (projects.isErr()) {
      return roots;
    }

    return [
      ...roots,
      ...projects
        .unwrap()
        .filter((entry) => entry.kind === "directory")
        .map((entry) => this.#projectSessionsRoot(entry.name)),
    ];
  }

  async #readIndex(reference: {
    session: ContextSession;
  }): Promise<Result<AgentDevKitErrorCode, ContextSessionIndex>> {
    const payload = await this.#dataStore.readJson<unknown>(
      this.#sessionPath(reference.session, "index.json"),
    );

    if (payload.isErr()) {
      return Result.fail(payload.unwrapError());
    }

    const parsed = ContextSessionIndexSchema.safeParse(payload.unwrap());
    return parsed.success ? Result.ok(parsed.data) : Result.fail(ErrorCodes.InvalidInput);
  }

  async #readMessages(
    session: ContextSession,
  ): Promise<Result<AgentDevKitErrorCode, ContextMessage[]>> {
    const path = this.#sessionPath(session, "messages.jsonl");
    const exists = await this.#dataStore.exists(path);

    if (exists.isErr()) {
      return Result.fail(exists.unwrapError());
    }

    if (!exists.unwrap()) {
      return Result.ok([]);
    }

    const messages = await this.#dataStore.readJsonl<unknown>(path);

    if (messages.isErr()) {
      return Result.fail(messages.unwrapError());
    }

    const parsed: ContextMessage[] = [];

    for (const message of messages.unwrap()) {
      const result = ContextMessageSchema.safeParse(message);

      if (!result.success) {
        return Result.fail(ErrorCodes.InvalidInput);
      }

      parsed.push(result.data);
    }

    return Result.ok(parsed);
  }

  #index(session: ContextSession, messages: ContextMessage[]): ContextSessionIndex {
    const preview = compactWhitespace(
      [...messages].reverse().find((message) => message.content.trim().length > 0)?.content ?? "",
    ).slice(0, 240);

    return ContextSessionIndexSchema.parse({
      schema: "agent-devkit.context-session-index/v1",
      createdAt: session.createdAt,
      keywords: keywordsFor([session.title, preview, session.tags.join(" ")]),
      lastMessageAt: session.lastMessageAt,
      messageCount: messages.length,
      preview,
      projectId: session.projectId,
      sessionId: session.id,
      status: session.status,
      title: session.title,
      updatedAt: session.updatedAt,
    });
  }

  #indexMatches(index: ContextSessionIndex, query: string): boolean {
    return [index.title, index.preview, index.keywords.join(" ")]
      .join(" ")
      .toLowerCase()
      .includes(query.toLowerCase());
  }

  #summary(session: ContextSession, messages: ContextMessage[]): string {
    return [`# ${session.title}`, "", `Messages: ${messages.length}`, ""].join("\n");
  }

  #sessionDirectory(session: ContextSession): AgentDataPath {
    return session.projectId === undefined
      ? { namespace: "context", segments: ["sessions", session.id] }
      : {
          namespace: "context",
          segments: ["projects", session.projectId, "sessions", session.id],
        };
  }

  #sessionPath(session: ContextSession, fileName: string): AgentDataPath {
    return {
      ...this.#sessionDirectory(session),
      segments: [...this.#sessionDirectory(session).segments, fileName],
    };
  }

  #projectSessionsRoot(projectId: string): AgentDataPath {
    return { namespace: "context", segments: ["projects", projectId, "sessions"] };
  }

  #now(): string {
    return this.#clock().toISOString();
  }
}
