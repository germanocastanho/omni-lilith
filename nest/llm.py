from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import anthropic


@dataclass
class LLMResponse:
    content: str
    tool_uses: list[dict[str, Any]] = field(default_factory=list)
    stop_reason: str = "end_turn"
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""


class AnthropicLLM:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model

    async def acomplete(
        self,
        messages: list[dict],
        system: str = "",
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
        echo: bool = False,
    ) -> LLMResponse:
        """Call the API. When echo=True, stream text to stdout as it arrives."""
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
        }
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = tools

        if echo:
            return await self._acomplete_streaming(kwargs)
        return await self._acomplete_blocking(kwargs)

    async def _acomplete_streaming(self, kwargs: dict[str, Any]) -> LLMResponse:
        text_parts: list[str] = []
        tool_uses: list[dict[str, Any]] = []

        async with self._client.messages.stream(**kwargs) as stream:
            async for chunk in stream.text_stream:
                print(chunk, end="", flush=True)
                text_parts.append(chunk)

            message = await stream.get_final_message()

        if text_parts:
            print()

        for block in message.content:
            if block.type == "tool_use":
                tool_uses.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })

        return LLMResponse(
            content="".join(text_parts),
            tool_uses=tool_uses,
            stop_reason=message.stop_reason or "end_turn",
            input_tokens=message.usage.input_tokens,
            output_tokens=message.usage.output_tokens,
            model=message.model,
        )

    async def _acomplete_blocking(self, kwargs: dict[str, Any]) -> LLMResponse:
        resp = await self._client.messages.create(**kwargs)

        text_parts: list[str] = []
        tool_uses: list[dict[str, Any]] = []

        for block in resp.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_uses.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })

        return LLMResponse(
            content="\n".join(text_parts),
            tool_uses=tool_uses,
            stop_reason=resp.stop_reason or "end_turn",
            input_tokens=resp.usage.input_tokens,
            output_tokens=resp.usage.output_tokens,
            model=resp.model,
        )
