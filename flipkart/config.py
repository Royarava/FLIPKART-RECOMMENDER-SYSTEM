import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from data/ directory (handles both root and nested execution)
env_path = Path(__file__).parent.parent / "data" / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"[CONFIG] Loaded environment from: {env_path}")
else:
    print(f"[CONFIG] Warning: .env not found at {env_path}")
    # Try loading from current directory as fallback
    load_dotenv()


def _get_windows_proxy():
    """Try to extract proxy from Windows registry for corporate networks."""
    try:
        import winreg
        try:
            # Try HKEY_CURRENT_USER first
            reg_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path) as key:
                proxy_enable, _ = winreg.QueryValueEx(key, "ProxyEnable")
                if proxy_enable:
                    proxy_server, _ = winreg.QueryValueEx(key, "ProxyServer")
                    if proxy_server and not proxy_server.startswith("http"):
                        return f"http://{proxy_server}"
                    return proxy_server
        except WindowsError:
            pass
    except ImportError:
        pass
    return None


def _configure_proxy():
    """Configure proxy for HTTP requests and environment."""
    # Check for explicit proxy environment variable
    proxy = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
    
    if not proxy:
        proxy = _get_windows_proxy()
    
    if proxy:
        os.environ["HTTP_PROXY"] = proxy
        os.environ["HTTPS_PROXY"] = proxy
        os.environ["http_proxy"] = proxy
        os.environ["https_proxy"] = proxy
        print(f"[CONFIG] Using proxy: {proxy.split(':')[0]}:****")
    
    return proxy


# Configure proxy on import
_configure_proxy()


class Config:
    ASTRA_DB_API_ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT")
    ASTRA_DB_APPLICATION_TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN") or os.getenv("ASTARA_DB_APPLICATION_TOKEN")
    ASTRA_DB_KEYSPACE = os.getenv("ASTRA_DB_KEYSPACE")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
    RAG_MODEL = "openai/gpt-oss-20b"
    DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"