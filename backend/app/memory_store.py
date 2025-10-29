from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

from chatkit.store import NotFoundError, Store
from chatkit.types import Attachment, Page, Thread, ThreadItem, ThreadMetadata
import logging
from uuid import uuid4


@dataclass
class _ThreadState:
    thread: ThreadMetadata
    items: List[ThreadItem]


class MemoryStore(Store[dict[str, Any]]):
    """Simple in-memory store compatible with the ChatKit server interface."""

    def __init__(self) -> None:
        self._logger = logging.getLogger("chatkit.memory_store")
        self._threads: Dict[str, _ThreadState] = {}
        # Attachments intentionally unsupported; use a real store that enforces auth.

    @staticmethod
    def _coerce_thread_metadata(thread: ThreadMetadata | Thread) -> ThreadMetadata:
        """Return thread metadata without any embedded items (openai-chatkit>=1.0)."""
        has_items = isinstance(thread, Thread) or "items" in getattr(
            thread, "model_fields_set", set()
        )
        if not has_items:
            return thread.model_copy(deep=True)

        data = thread.model_dump()
        data.pop("items", None)
        return ThreadMetadata(**data).model_copy(deep=True)

    # -- Thread metadata -------------------------------------------------
    async def load_thread(self, thread_id: str, context: dict[str, Any]) -> ThreadMetadata:
        state = self._threads.get(thread_id)
        if not state:
            self._logger.debug("load_thread: thread_id=%s not found", thread_id)
            raise NotFoundError(f"Thread {thread_id} not found")
        self._logger.debug(
            "load_thread: thread_id=%s title=%s items=%s",
            thread_id,
            getattr(state.thread, "title", None),
            len(state.items),
        )
        return self._coerce_thread_metadata(state.thread)

    async def save_thread(self, thread: ThreadMetadata, context: dict[str, Any]) -> None:
        metadata = self._coerce_thread_metadata(thread)
        state = self._threads.get(thread.id)
        if state:
            state.thread = metadata
            self._logger.debug(
                "save_thread: updated thread_id=%s title=%s items=%s",
                thread.id,
                getattr(metadata, "title", None),
                len(state.items),
            )
        else:
            self._threads[thread.id] = _ThreadState(
                thread=metadata,
                items=[],
            )
            self._logger.debug(
                "save_thread: created thread_id=%s title=%s",
                thread.id,
                getattr(metadata, "title", None),
            )

    async def load_threads(
        self,
        limit: int,
        after: str | None,
        order: str,
        context: dict[str, Any],
    ) -> Page[ThreadMetadata]:
        threads = sorted(
            (self._coerce_thread_metadata(state.thread) for state in self._threads.values()),
            key=lambda t: t.created_at or datetime.min,
            reverse=(order == "desc"),
        )

        if after:
            index_map = {thread.id: idx for idx, thread in enumerate(threads)}
            start = index_map.get(after, -1) + 1
        else:
            start = 0

        slice_threads = threads[start : start + limit + 1]
        has_more = len(slice_threads) > limit
        slice_threads = slice_threads[:limit]
        next_after = slice_threads[-1].id if has_more and slice_threads else None
        return Page(
            data=slice_threads,
            has_more=has_more,
            after=next_after,
        )

    async def delete_thread(self, thread_id: str, context: dict[str, Any]) -> None:
        removed = self._threads.pop(thread_id, None)
        self._logger.debug(
            "delete_thread: thread_id=%s existed=%s",
            thread_id,
            removed is not None,
        )

    # -- Thread items ----------------------------------------------------
    def _items(self, thread_id: str) -> List[ThreadItem]:
        state = self._threads.get(thread_id)
        if state is None:
            state = _ThreadState(
                thread=ThreadMetadata(id=thread_id, created_at=datetime.utcnow()),
                items=[],
            )
            self._threads[thread_id] = state
            self._logger.debug(
                "_items: auto-created thread state thread_id=%s", thread_id
            )
        return state.items

    async def load_thread_items(
        self,
        thread_id: str,
        after: str | None,
        limit: int,
        order: str,
        context: dict[str, Any],
    ) -> Page[ThreadItem]:
        items = [item.model_copy(deep=True) for item in self._items(thread_id)]
        items.sort(
            key=lambda item: getattr(item, "created_at", datetime.utcnow()),
            reverse=(order == "desc"),
        )

        if after:
            index_map = {item.id: idx for idx, item in enumerate(items)}
            start = index_map.get(after, -1) + 1
        else:
            start = 0

        slice_items = items[start : start + limit + 1]
        has_more = len(slice_items) > limit
        slice_items = slice_items[:limit]
        next_after = slice_items[-1].id if has_more and slice_items else None
        page = Page(data=slice_items, has_more=has_more, after=next_after)
        self._logger.debug(
            "load_thread_items: thread_id=%s total=%s returned=%s order=%s after=%s has_more=%s",
            thread_id,
            len(items),
            len(page.data),
            order,
            after,
            has_more,
        )
        return page

    async def add_thread_item(
        self, thread_id: str, item: ThreadItem, context: dict[str, Any]
    ) -> None:
        items = self._items(thread_id)
        before = len(items)
        # Guard: avoid silent overwrite if caller reuses item.id
        if any(getattr(existing, "id", None) == getattr(item, "id", None) for existing in items):
            try:
                # Recreate an id with the store's generator to avoid collision
                new_id = self.generate_item_id(
                    "message",
                    ThreadMetadata(id=thread_id, created_at=datetime.utcnow()),
                    context,
                )
                self._logger.warning(
                    "add_thread_item: duplicate id detected thread_id=%s item_id=%s -> new_id=%s",
                    thread_id,
                    getattr(item, "id", None),
                    new_id,
                )
                item = item.model_copy(update={"id": new_id})
            except Exception:
                # Fallback: suffix the id
                suffix_id = f"{getattr(item, 'id', 'item')}_{uuid4().hex[:6]}"
                self._logger.warning(
                    "add_thread_item: duplicate id fallback thread_id=%s item_id=%s -> new_id=%s",
                    thread_id,
                    getattr(item, "id", None),
                    suffix_id,
                )
                item = item.model_copy(update={"id": suffix_id})
        items.append(item.model_copy(deep=True))
        self._logger.debug(
            "add_thread_item: thread_id=%s item_id=%s type=%s count %s->%s",
            thread_id,
            getattr(item, "id", None),
            item.__class__.__name__,
            before,
            len(items),
        )

    async def save_item(self, thread_id: str, item: ThreadItem, context: dict[str, Any]) -> None:
        items = self._items(thread_id)
        for idx, existing in enumerate(items):
            if existing.id == item.id:
                try:
                    existing_dump = existing.model_dump(exclude_none=True)
                    new_dump = item.model_dump(exclude_none=True)
                    is_change = existing_dump != new_dump
                except Exception:
                    is_change = True
                items[idx] = item.model_copy(deep=True)
                self._logger.debug(
                    "save_item: updated thread_id=%s item_id=%s type=%s changed=%s",
                    thread_id,
                    getattr(item, "id", None),
                    item.__class__.__name__,
                    is_change,
                )
                return
        items.append(item.model_copy(deep=True))
        self._logger.debug(
            "save_item: appended thread_id=%s item_id=%s type=%s new_count=%s",
            thread_id,
            getattr(item, "id", None),
            item.__class__.__name__,
            len(items),
        )

    async def load_item(self, thread_id: str, item_id: str, context: dict[str, Any]) -> ThreadItem:
        for item in self._items(thread_id):
            if item.id == item_id:
                self._logger.debug(
                    "load_item: found thread_id=%s item_id=%s type=%s",
                    thread_id,
                    item_id,
                    item.__class__.__name__,
                )
                return item.model_copy(deep=True)
        raise NotFoundError(f"Item {item_id} not found")

    async def delete_thread_item(
        self, thread_id: str, item_id: str, context: dict[str, Any]
    ) -> None:
        items = self._items(thread_id)
        before = len(items)
        self._threads[thread_id].items = [item for item in items if item.id != item_id]
        self._logger.debug(
            "delete_thread_item: thread_id=%s item_id=%s count %s->%s",
            thread_id,
            item_id,
            before,
            len(self._threads[thread_id].items),
        )

    # -- ID generation ---------------------------------------------------
    def generate_thread_id(self, context: dict[str, Any]) -> str:
        thread_id = f"thread_{uuid4().hex[:12]}"
        self._logger.debug("generate_thread_id: %s", thread_id)
        return thread_id

    def generate_item_id(self, kind: str, thread: ThreadMetadata, context: dict[str, Any]) -> str:
        item_id = f"{kind}_{uuid4().hex[:12]}"
        self._logger.debug(
            "generate_item_id: kind=%s thread_id=%s item_id=%s",
            kind,
            thread.id,
            item_id,
        )
        return item_id

    # -- Files -----------------------------------------------------------
    # These methods are not currently used but required to be compatible with the Store interface.

    async def save_attachment(
        self,
        attachment: Attachment,
        context: dict[str, Any],
    ) -> None:
        raise NotImplementedError(
            "MemoryStore does not persist attachments. Provide a Store implementation "
            "that enforces authentication and authorization before enabling uploads."
        )

    async def load_attachment(
        self,
        attachment_id: str,
        context: dict[str, Any],
    ) -> Attachment:
        raise NotImplementedError(
            "MemoryStore does not load attachments. Provide a Store implementation "
            "that enforces authentication and authorization before enabling uploads."
        )

    async def delete_attachment(self, attachment_id: str, context: dict[str, Any]) -> None:
        raise NotImplementedError(
            "MemoryStore does not delete attachments because they are never stored."
        )
