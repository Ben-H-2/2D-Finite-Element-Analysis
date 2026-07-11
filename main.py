import os
import uvicorn

def main():
    is_codespace = os.environ.get("CODESPACES") == "true"

    if is_codespace:
        codespace_name = os.environ.get("CODESPACE_NAME", "")
        domain = os.environ.get("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN", "app.github.dev")
        print(f"Running in GitHub Codespaces.")
        print(f"Once started, open: https://{codespace_name}-8000.{domain}")
    else:
        print("Running locally.")
        print("Once started, open: http://localhost:8000")

    uvicorn.run("api.app:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()