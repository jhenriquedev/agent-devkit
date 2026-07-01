# conversation.chat

Sends a chat message through Agent DevKit's canonical prompt and brain request contracts.

The first implementation uses the deterministic mock brain provider. It persists user and assistant messages through `context.sessions`, reads the active character from `user.personalization`, and optionally attaches `context.projects` metadata.
