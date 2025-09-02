import yaml
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, Tuple, List, Set

def load_dag_config(yaml_path: str):
    with open(yaml_path, 'r') as f:
        return yaml.safe_load(f)

def build_dependency_graph(steps):
    graph = defaultdict(list)       # dep -> [dependents]
    indegree = defaultdict(int)     # node -> # unmet deps
    step_map = {}

    for step in steps:
        step_id = step['id']
        step_map[step_id] = step
        for dep in step.get('depends_on', []):
            graph[dep].append(step_id)
            indegree[step_id] += 1
        if step_id not in indegree:
            indegree[step_id] = 0
        if step_id not in graph:
            graph[step_id] = []     # ensure key exists

    return graph, indegree, step_map

def _resolve_input(raw_input, step_outputs: Dict[str, Any]):
    """
    Very light resolver:
    - "${step_id.output}" -> step_outputs[step_id]
    - list/dict will be walked recursively
    - plain strings/values returned as-is
    """
    if isinstance(raw_input, str) and raw_input.startswith("${") and raw_input.endswith("}"):
        ref = raw_input.strip("${}").split(".")
        dep_id = ref[0]
        return step_outputs.get(dep_id)
    if isinstance(raw_input, list):
        return [_resolve_input(x, step_outputs) for x in raw_input]
    if isinstance(raw_input, dict):
        return {k: _resolve_input(v, step_outputs) for k, v in raw_input.items()}
    return raw_input

def _run_single_step(step_id: str, step: dict, step_outputs: Dict[str, Any]):
    agent = step["agent"]
    resolved_input = _resolve_input(step.get("input"), step_outputs)
    params = step.get("params", {}) or {}
    print(f"🔧 Running {step_id} → {agent}")
    output = run_agent_by_name(agent, resolved_input, params)
    return step_id, output

def run_dag_from_yaml(yaml_path: str, max_workers: int = 8, timeout_per_step: float = None, retries: int = 0):
    """
    Executes DAG in level-parallel batches:
    - All current in-degree-0 nodes are launched together.
    - When a batch completes, their dependents are unlocked, forming the next batch.
    - If any step fails, the whole run stops (fail-fast strategy).
    """
    config = load_dag_config(yaml_path)
    steps = config["steps"]
    graph, indegree, step_map = build_dependency_graph(steps)

    # Ready queue (current batch = all in-degree 0 nodes not yet run)
    ready: Set[str] = {n for n, d in indegree.items() if d == 0}
    done: Set[str] = set()
    step_outputs: Dict[str, Any] = {}

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        while ready:
            batch = sorted(ready)  # deterministic order
            ready.clear()

            futures = {}
            for step_id in batch:
                def submit_with_retries(sid=step_id):
                    attempt = 0
                    last_exc = None
                    while attempt <= retries:
                        try:
                            return _run_single_step(sid, step_map[sid], step_outputs)
                        except Exception as e:
                            last_exc = e
                            attempt += 1
                            if attempt <= retries:
                                print(f"⚠️  Retry {attempt}/{retries} for {sid} due to: {e}")
                    # exhausted
                    raise last_exc
                futures[pool.submit(submit_with_retries)] = step_id

            # Collect results (fail-fast)
            try:
                for fut in as_completed(futures, timeout=timeout_per_step * len(futures) if timeout_per_step else None):
                    sid = futures[fut]
                    step_id, output = fut.result(timeout=timeout_per_step) if timeout_per_step else fut.result()
                    step_outputs[step_id] = output
                    done.add(step_id)
            except Exception as e:
                # Cancel others and abort
                for fut in futures:
                    fut.cancel()
                raise RuntimeError(f"DAG execution failed in batch {batch}: {e}") from e

            # Unlock next batch
            for finished in batch:
                for dep in graph[finished]:
                    indegree[dep] -= 1
                    if indegree[dep] == 0 and dep not in done:
                        ready.add(dep)

    # Sanity: ensure all nodes done
    if len(done) != len(step_map):
        missing = set(step_map.keys()) - done
        raise RuntimeError(f"DAG did not complete. Unfinished steps: {sorted(missing)}")

    return step_outputs

def run_agent_by_name(agent_name, input_text, params=None):
    from email_client.fetcher import fetch_recent_emails
    from email_client.task_extractor import extract_p0_tasks
    from orchestrator.agents.summarizer import summarize_p0_tasks
    from orchestrator.agents.helloWorld import HelloWorld
    from utils.discord_notifier import send_discord_message
    from orchestrator.agents.ollama_runner import run_ollama

    if agent_name == "gmail_reader":
        return fetch_recent_emails()
    elif agent_name == "gpt_task_extractor":
        return extract_p0_tasks(input_text)
    elif agent_name == "gpt_summarizer":
        return summarize_p0_tasks(input_text)
    elif agent_name == "ollama_agent":
        return run_ollama(input_text, params or {})
    elif agent_name == "file_writer":
        with open("data/p0_digest_summary.txt", "w") as f:
            f.write(input_text)
        return "✅ written to disk"
    elif agent_name == "discord_notifier":
        topic = (params or {}).get("topic", "🧠 Daily P0 Digest")
        send_discord_message(topic, input_text)
        return "✅ sent to Discord"
    elif agent_name == "helloWorld":
        return HelloWorld()
    else:
        raise ValueError(f"Unknown agent: {agent_name}")
