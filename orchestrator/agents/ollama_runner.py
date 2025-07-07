import requests

def run_ollama(prompt: str, params: dict) -> str:
    model = params.get("model", "llama3")
    host = params.get("host", "http://localhost:11434")
    response = requests.post(f"{host}/api/generate", json={
        "model": model,
        "prompt": prompt,
        "stream": False
    })
    if response.status_code != 200:
        raise Exception(
          f"Ollama call failed: {response.status_code} {response.text}. Hint:\n"
          "1. Check if the Ollama server is running and the model is available.\n"
          "2. Ensure the model name is correct.\n"
          "3. Verify the host URL is correct (default is http://localhost:11434).\n"
          "4. If using Docker to run the project, ensure the URL is http://host.docker.internal:{Port}."
        )
    return response.json()["response"].strip()
