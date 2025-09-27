"""Offline dynamic component generation stubs."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from .registry import RegistryService


@dataclass(slots=True)
class GeneratedComponent:
    name: str
    implementation_code: str
    metadata: dict[str, Any]


class DynamicBuilder:
    """Generates deterministic mock components to simulate GPT output."""

    def __init__(self, registry: RegistryService | None = None) -> None:
        self.registry = registry or RegistryService()

    async def generate_tool(self, description: str, context: dict[str, Any] | None = None) -> GeneratedComponent:
        context = context or {}
        name = _slugify(description, prefix="Tool")
        code = f"def handle(payload):\n    \"\"\"Auto-generated tool for {description}.\"\"\"\n    return {{'summary': '{description}', 'payload': payload}}\n"
        metadata = {"kind": "tool", "context": context}
        return GeneratedComponent(name=name, implementation_code=code, metadata=metadata)

    async def generate_agent(
        self,
        description: str,
        capabilities: list[str] | None = None,
        context: dict[str, Any] | None = None,
    ) -> GeneratedComponent:
        context = context or {}
        capabilities = capabilities or []
        name = _slugify(description, prefix="Agent")
        code = "\n".join(
            [
                "class AutoAgent:",
                "    \"\"\"Auto-generated agent class.\"\"\"",
                "    def __init__(self):",
                f"        self.capabilities = {capabilities}",
                "",
                "    def respond(self, message: str) -> str:",
                "        return f'[{name}] {message}'",
            ]
        )
        metadata = {"kind": "agent", "context": context, "capabilities": capabilities}
        return GeneratedComponent(name=name, implementation_code=code, metadata=metadata)

    async def generate_function(
        self,
        description: str,
        examples: list[str] | None = None,
    ) -> GeneratedComponent:
        examples = examples or []
        name = _slugify(description, prefix="Function")
        body_lines = ["def auto_function(input_value):", f"    \"\"\"{description}.\"\"\""]
        if examples:
            body_lines.append(f"    # Examples: {'; '.join(examples)}")
        body_lines.append("    return {'description': input_value}")
        code = "\n".join(body_lines)
        metadata = {"kind": "function", "examples": examples}
        return GeneratedComponent(name=name, implementation_code=code, metadata=metadata)

    async def validate_and_test(self, component: GeneratedComponent) -> dict[str, Any]:
        """Pretend to validate generated code by hashing its contents."""

        digest = hashlib.sha256(component.implementation_code.encode()).hexdigest()
        return {"status": "passed", "digest": digest}


def _slugify(text: str, prefix: str) -> str:
    normalized = "".join(ch if ch.isalnum() else " " for ch in text).strip()
    words = normalized.split()
    slug = "".join(word.capitalize() for word in words) or "Component"
    return f"{prefix}{slug}"
