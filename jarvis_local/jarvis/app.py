"""Zusammenbau der Jarvis-Komponenten zu einer lauffähigen App."""
from __future__ import annotations

from dataclasses import dataclass

from .config import Config
from .core.agent_loop import AgentLoop
from .core.llm import LLMBackend
from .memory.obsidian import ObsidianVault
from .memory.vector_index import VectorIndex
from .security.audit_log import AuditLog
from .security.permission_gateway import PermissionGateway
from .tools.base import ToolRegistry
from .tools.demo_tool import build_demo_tools
from .tools.gmail_tool import GmailClient, build_gmail_tools
from .tools.memory_tool import build_memory_tools
from .tools.web_agent_tool import build_web_tools


@dataclass
class JarvisApp:
    config: Config
    agent: AgentLoop
    gateway: PermissionGateway
    registry: ToolRegistry
    vault: ObsidianVault
    index: VectorIndex
    audit: AuditLog


def build_registry(
    vault: ObsidianVault,
    index: VectorIndex,
    *,
    gmail_client: GmailClient | None = None,
    include_web: bool = True,
    include_demo: bool = True,
) -> ToolRegistry:
    registry = ToolRegistry()
    for tool in build_memory_tools(vault, index):
        registry.register(tool)
    for tool in build_gmail_tools(gmail_client or GmailClient()):
        registry.register(tool)
    if include_web:
        for tool in build_web_tools():
            registry.register(tool)
    if include_demo:
        for tool in build_demo_tools():
            registry.register(tool)
    return registry


def build_app(config: Config, backend: LLMBackend, *, persist: bool = True) -> JarvisApp:
    config.ensure_dirs()
    audit = AuditLog(config.audit_db if persist else ":memory:")
    gateway = PermissionGateway(config.approvals_db if persist else ":memory:", audit=audit)
    vault = ObsidianVault(config.vault_dir)
    index = VectorIndex(config.vector_db if persist else ":memory:")
    registry = build_registry(vault, index)
    agent = AgentLoop(backend, registry, gateway)
    return JarvisApp(config, agent, gateway, registry, vault, index, audit)
