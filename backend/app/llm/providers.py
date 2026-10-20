import json
from dataclasses import dataclass

import httpx


class ProviderError(Exception):
    """Raised with an actionable message when a model endpoint misbehaves."""


@dataclass
class ProviderConfig:
    kind: str  # ollama | openai_compat
    base_url: str
    model: str
    api_key: str | None = None


def _headers(cfg: ProviderConfig) -> dict:
    if cfg.kind == "openai_compat" and cfg.api_key:
        return {"Authorization": f"Bearer {cfg.api_key}"}
    return {}


def _ollama_url(cfg: ProviderConfig, path: str) -> str:
    return cfg.base_url.rstrip("/") + path


def _openai_url(cfg: ProviderConfig, path: str) -> str:
    base = cfg.base_url.rstrip("/")
    if not base.endswith("/v1"):
        base += "/v1"
    return base + path


async def test_connection(cfg: ProviderConfig) -> dict:
    url = _ollama_url(cfg, "/api/tags") if cfg.kind == "ollama" else _openai_url(cfg, "/models")
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, headers=_headers(cfg))
    except httpx.HTTPError as exc:
        raise ProviderError(f"Could not reach {url}: {exc.__class__.__name__}. Check the base URL and that the server is running.") from exc
    if resp.status_code != 200:
        raise ProviderError(f"{url} answered HTTP {resp.status_code}. Check the URL, key, and server config.")
    try:
        body = resp.json()
    except ValueError:
        raise ProviderError(f"{url} returned non-JSON: is this really a model server?")
    if cfg.kind == "ollama":
        models = [m.get("name", "") for m in body.get("models", [])]
        known = any(m == cfg.model or m.split(":")[0] == cfg.model for m in models)
        if not known:
            raise ProviderError(f"Connected, but model '{cfg.model}' is not pulled on that Ollama server. Run: ollama pull {cfg.model}")
        return {"ok": True, "models": models}
    model_ids = [m.get("id", "") for m in body.get("data", [])]
    if model_ids and cfg.model not in model_ids:
        raise ProviderError(f"Connected, but '{cfg.model}' is not in the server's model list: {model_ids[:10]}")
    return {"ok": True, "models": model_ids}


async def stream_chat(cfg: ProviderConfig, messages: list[dict]):
    """Yield assistant text chunks. Raises ProviderError with an actionable message."""
    if cfg.kind == "ollama":
        url = _ollama_url(cfg, "/api/chat")
        payload = {"model": cfg.model, "messages": messages, "stream": True}
    else:
        url = _openai_url(cfg, "/chat/completions")
        payload = {"model": cfg.model, "messages": messages, "stream": True}
    try:
        client = httpx.AsyncClient(timeout=httpx.Timeout(connect=10, read=600, write=30, pool=600))
        resp = await client.send(client.build_request("POST", url, json=payload, headers=_headers(cfg)), stream=True)
    except httpx.HTTPError as exc:
        raise ProviderError(f"Could not reach {url}: {exc.__class__.__name__}. Check the base URL and that the server is running.") from exc
    if resp.status_code != 200:
        detail = (await resp.aread()).decode(errors="replace")[:400]
        await resp.aclose()
        await client.aclose()
        raise ProviderError(f"{url} answered HTTP {resp.status_code}: {detail}")
    try:
        async for line in resp.aiter_lines():
            if not line.strip():
                continue
            if cfg.kind == "ollama":
                data = json.loads(line)
                if data.get("done"):
                    break
                chunk = (data.get("message") or {}).get("content", "")
                if chunk:
                    yield chunk
            else:
                if not line.startswith("data:"):
                    continue
                payload_str = line[5:].strip()
                if payload_str == "[DONE]":
                    break
                data = json.loads(payload_str)
                choices = data.get("choices") or [{}]
                chunk = (choices[0].get("delta") or {}).get("content") or ""
                if chunk:
                    yield chunk
    except httpx.HTTPError as exc:
        raise ProviderError(f"Stream interrupted: {exc.__class__.__name__}") from exc
    except json.JSONDecodeError:
        continue_flag = True
    finally:
        await resp.aclose()
        await client.aclose()
