"""ChatKit server integration for the boilerplate backend."""

from __future__ import annotations

import inspect
import logging
from datetime import datetime
import re
from typing import Annotated, Any, AsyncIterator
from uuid import uuid4

from agents import Agent, Runner
from chatkit.agents import (
    AgentContext,
    ThreadItemConverter,
    stream_agent_response,
)
from chatkit.server import ChatKitServer
from chatkit.types import (
    Attachment,
    ClientToolCallItem,
    HiddenContextItem,
    ThreadItem,
    ThreadMetadata,
    ThreadStreamEvent,
    UserMessageItem,
)
from openai.types.responses import ResponseInputContentParam
from pydantic import ConfigDict, Field

from .constants import INSTRUCTIONS, MODEL
from .memory_store import MemoryStore
from . import transcripts as transcripts_store

# If you want to check what's going on under the hood, set this to DEBUG
logging.basicConfig(level=logging.INFO)


def _gen_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:8]}"


def _is_tool_completion_item(item: Any) -> bool:
    return isinstance(item, ClientToolCallItem)


class AgentControllerContext(AgentContext):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    store: Annotated[MemoryStore, Field(exclude=True)]
    request_context: dict[str, Any]


 


 


def _user_message_text(item: UserMessageItem) -> str:
    parts: list[str] = []
    for part in item.content:
        text = getattr(part, "text", None)
        if text:
            parts.append(text)
    return " ".join(parts).strip()


_DOC_TAG_PATTERN = re.compile(r"@(?P<id>doc_[A-Za-z0-9_]+)")


def _extract_doc_ids(text: str, max_items: int = 5) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for match in _DOC_TAG_PATTERN.finditer(text or ""):
        doc_id = match.group("id")
        if doc_id not in seen:
            seen.add(doc_id)
            ordered.append(doc_id)
        if len(ordered) >= max_items:
            break
    return ordered


def _gather_doc_ids_from_mapping(data: Any, max_items: int, seen: set[str], ordered: list[str]) -> None:
    if len(ordered) >= max_items:
        return
    if isinstance(data, dict):
        for value in data.values():
            _gather_doc_ids_from_mapping(value, max_items, seen, ordered)
            if len(ordered) >= max_items:
                return
    elif isinstance(data, (list, tuple)):
        for value in data:
            _gather_doc_ids_from_mapping(value, max_items, seen, ordered)
            if len(ordered) >= max_items:
                return
    elif isinstance(data, str):
        for match in re.finditer(r"\b(doc_[A-Za-z0-9_]+)\b", data):
            doc_id = match.group(1)
            if doc_id not in seen:
                seen.add(doc_id)
                ordered.append(doc_id)
            if len(ordered) >= max_items:
                return


def _extract_doc_ids_from_item(item: UserMessageItem, max_items: int = 5) -> list[str]:
    """Extract doc ids from structured message parts (entity mentions), not just text."""
    seen: set[str] = set()
    ordered: list[str] = []
    try:
        for part in getattr(item, "content", []) or []:
            try:
                # Log part type and a tiny preview for debugging
                part_type = getattr(part, "type", None) or part.__class__.__name__
                logging.info("[chat] part type=%s", part_type)
            except Exception:
                pass

            # Prefer model_dump if available (pydantic models)
            mapping = None
            dump = getattr(part, "model_dump", None)
            if callable(dump):
                try:
                    mapping = dump()
                except Exception:
                    mapping = None
            if mapping is None:
                try:
                    mapping = vars(part)
                except Exception:
                    mapping = None

            if mapping is not None:
                _gather_doc_ids_from_mapping(mapping, max_items, seen, ordered)
            # Also scan any text field present on the part
            text = getattr(part, "text", None)
            if isinstance(text, str):
                for doc_id in _extract_doc_ids(text, max_items):
                    if doc_id not in seen:
                        seen.add(doc_id)
                        ordered.append(doc_id)
            if len(ordered) >= max_items:
                break
    except Exception:
        # Defensive: never break the request on extraction failure
        logging.exception("[chat] failed to extract doc ids from item parts")
    return ordered


class AgentControllerServer(ChatKitServer[dict[str, Any]]):
    """ChatKit server without tools, streaming text-only responses."""

    def __init__(self) -> None:
        self.store: MemoryStore = MemoryStore()
        super().__init__(self.store)
        self.assistant = Agent[AgentControllerContext](
            model=MODEL,
            name="Agent Controller",
            instructions=INSTRUCTIONS,
            tools=[],  # no tools enabled
        )
        self._thread_item_converter = self._init_thread_item_converter()

    async def respond(
        self,
        thread: ThreadMetadata,
        item: UserMessageItem | None,
        context: dict[str, Any],
    ) -> AsyncIterator[ThreadStreamEvent]:
        agent_context = AgentControllerContext(
            thread=thread,
            store=self.store,
            request_context=context,
        )

        target_item: ThreadItem | None = item
        if target_item is None:
            target_item = await self._latest_thread_item(thread, context)

        if target_item is None or _is_tool_completion_item(target_item):
            return

        agent_input = await self._to_agent_input(thread, target_item)
        if agent_input is None:
            return

        result = Runner.run_streamed(
            self.assistant,
            agent_input,
            context=agent_context,
        )

        async for event in stream_agent_response(agent_context, result):
            yield event
        return

    async def to_message_content(self, _input: Attachment) -> ResponseInputContentParam:
        raise RuntimeError("File attachments are not supported in this demo.")

    def _init_thread_item_converter(self) -> Any | None:
        converter_cls = ThreadItemConverter
        if converter_cls is None or not callable(converter_cls):
            return None

        attempts: tuple[dict[str, Any], ...] = (
            {"to_message_content": self.to_message_content},
            {"message_content_converter": self.to_message_content},
            {},
        )

        for kwargs in attempts:
            try:
                return converter_cls(**kwargs)
            except TypeError:
                continue
        return None

    async def _latest_thread_item(
        self, thread: ThreadMetadata, context: dict[str, Any]
    ) -> ThreadItem | None:
        try:
            items = await self.store.load_thread_items(thread.id, None, 1, "desc", context)
        except Exception:  # pragma: no cover - defensive
            return None

        return items.data[0] if getattr(items, "data", None) else None

    async def _to_agent_input(
        self,
        thread: ThreadMetadata,
        item: ThreadItem,
    ) -> Any | None:
        if _is_tool_completion_item(item):
            return None

        # First try to use ChatKit's converter to obtain best-effort text (may include entity markup)
        base_text: str | None = None
        converter = getattr(self, "_thread_item_converter", None)
        if converter is not None:
            for attr in (
                "to_input_item",
                "convert",
                "convert_item",
                "convert_thread_item",
            ):
                method = getattr(converter, attr, None)
                if method is None:
                    continue
                call_args: list[Any] = [item]
                call_kwargs: dict[str, Any] = {}
                try:
                    signature = inspect.signature(method)
                except (TypeError, ValueError):
                    signature = None

                if signature is not None:
                    params = [
                        parameter
                        for parameter in signature.parameters.values()
                        if parameter.kind
                        not in (
                            inspect.Parameter.VAR_POSITIONAL,
                            inspect.Parameter.VAR_KEYWORD,
                        )
                    ]
                    if len(params) >= 2:
                        next_param = params[1]
                        if next_param.kind in (
                            inspect.Parameter.POSITIONAL_ONLY,
                            inspect.Parameter.POSITIONAL_OR_KEYWORD,
                        ):
                            call_args.append(thread)
                        else:
                            call_kwargs[next_param.name] = thread

                result = method(*call_args, **call_kwargs)
                if inspect.isawaitable(result):
                    result = await result
                if isinstance(result, str):
                    base_text = result
                else:
                    # Fallback if converter returns a structured item — we'll handle simple user text below
                    base_text = None
                break

        # Fallback to raw user message content if needed
        if base_text is None and isinstance(item, UserMessageItem):
            base_text = _user_message_text(item)

        # If we have user text, attempt transcript augmentation
        if isinstance(item, UserMessageItem) and base_text is not None:
            logging.info("[chat] user_text: %s", base_text)
            # First try to find raw @doc_* in text
            doc_ids = _extract_doc_ids(base_text)
            # If none, try to read from structured parts (entity mention payloads)
            if not doc_ids:
                doc_ids = _extract_doc_ids_from_item(item)
            logging.info("[chat] detected_doc_ids: %s", doc_ids)
            if not doc_ids:
                return base_text

            found = [transcripts_store.get_transcript(doc_id) for doc_id in doc_ids]
            transcripts = [t for t in found if t is not None]
            logging.info("[chat] transcripts_found: %d", len(transcripts))
            if not transcripts:
                return base_text

            def _remove_doc_tags(text: str) -> str:
                cleaned = _DOC_TAG_PATTERN.sub("", text or "").strip()
                return re.sub(r"\s+", " ", cleaned)

            cleaned_question = _remove_doc_tags(base_text)

            sections: list[str] = []
            for t in transcripts:
                sections.append(
                    (
                        f"---\n"
                        f"Title: {t.title}\n"
                        f"ID: {t.id}\n"
                        f"Date: {t.date}\n"
                        f"Summary: {t.summary}\n"
                        f"Transcript:\n{t.content}\n"
                    )
                )

            augmented = (
                "You are given meeting transcript context referenced by the user via @doc_* tags.\n\n"
                "Use the transcripts to answer questions, summarize key points, extract action items, "
                "and connect information across meetings.\n\n"
                + "\n".join(sections)
                + "\n\nUser question: "
                + cleaned_question
            )
            logging.info("[chat] augmented_len=%d preview=%.120s", len(augmented), augmented)
            return augmented

        if isinstance(item, UserMessageItem):
            return _user_message_text(item)

        return None

    async def _add_hidden_item(
        self,
        thread: ThreadMetadata,
        context: dict[str, Any],
        content: str,
    ) -> None:
        await self.store.add_thread_item(
            thread.id,
            HiddenContextItem(
                id=_gen_id("msg"),
                thread_id=thread.id,
                created_at=datetime.now(),
                content=content,
            ),
            context,
        )


def create_chatkit_server() -> AgentControllerServer | None:
    """Return a configured ChatKit server instance if dependencies are available."""
    return AgentControllerServer()
