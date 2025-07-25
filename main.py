from orchestrator.dag_executor import run_dag_from_yaml

if __name__ == "__main__":
    run_dag_from_yaml("config/agents.yaml")
