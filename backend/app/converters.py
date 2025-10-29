from __future__ import annotations

from inspect import cleandoc
from typing import Any, Sequence

from chatkit.agents import ThreadItemConverter
from chatkit.types import (
    Attachment,
    UserMessageItem,
    UserMessageTagContent,
    UserMessageTextContent,
)
from openai.types.responses import (
    ResponseInputContentParam,
    ResponseInputTextParam,
)
from openai.types.responses.response_input_item_param import Message

from . import transcripts as transcripts_store


class TranscriptAwareConverter(ThreadItemConverter):
    async def attachment_to_message_content(
        self, attachment: Attachment
    ) -> ResponseInputContentParam:
        # Attachments are not supported in this demo backend.
        raise RuntimeError("File attachments are not supported in this build.")

    def tag_to_message_content(self, tag: UserMessageTagContent) -> ResponseInputContentParam:
        # Only transcripts (doc_*) are supported for now.
        transcript = (
            transcripts_store.get_transcript(tag.id) if tag.id and tag.id.startswith("doc_") else None
        )
        if transcript is None:
            text = f"Transcript not found for id: {tag.id}"
            return ResponseInputTextParam(type="input_text", text=text)

        # Full transcript context (title, id, date, summary, content)
        text = (
            f"---\n"
            f"Title: {transcript.title}\n"
            f"ID: {transcript.id}\n"
            f"Date: {transcript.date}\n"
            f"Summary: {transcript.summary}\n"
            f"Transcript:\n{transcript.content}\n"
        )
        return ResponseInputTextParam(type="input_text", text=text)

    async def user_message_to_input(
        self, item: UserMessageItem, is_last_message: bool = True
    ) -> Message | list[Message] | None:
        # Build the user text exactly as typed, rendering tags as @key
        message_text_parts: list[str] = []
        # Track tags separately to add context
        raw_tags: list[UserMessageTagContent] = []

        for part in item.content:
            if isinstance(part, UserMessageTextContent):
                message_text_parts.append(part.text)
            elif isinstance(part, UserMessageTagContent):
                message_text_parts.append(f"@{part.text}")
                raw_tags.append(part)
            else:
                # Ignore unknown parts
                continue

        user_text_item = Message(
            role="user",
            type="message",
            content=[
                ResponseInputTextParam(type="input_text", text="".join(message_text_parts)),
                *[
                    await self.attachment_to_message_content(a)
                    for a in item.attachments
                ],
            ],
        )

        # Prepare context message with instructions and per-tag transcript content
        context_items: list[Message] = []

        if raw_tags:
            # Dedupe by tag.text, preserve order, cap at 5
            seen: set[str] = set()
            uniq: list[UserMessageTagContent] = []
            for t in raw_tags:
                if t.text not in seen:
                    seen.add(t.text)
                    uniq.append(t)
                if len(uniq) >= 5:
                    break

            tag_contents: list[ResponseInputContentParam] = [
                self.tag_to_message_content(tag) for tag in uniq
            ]

            if tag_contents:
                context_items.append(
                    Message(
                        role="user",
                        type="message",
                        content=[
                            ResponseInputTextParam(
                                type="input_text",
                                text=cleandoc(
                                    """
                                    # User-provided context for @-mentions
                                    - When referencing resolved entities, use their canonical names without '@'.
                                    - The '@' form appears only in user text and should not be echoed.
                                    - Each block below contains transcript context referenced by the user.
                                    """
                                ).strip(),
                            ),
                            *tag_contents,
                        ],
                    )
                )

        return [user_text_item, *context_items]


