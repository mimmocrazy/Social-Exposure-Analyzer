import os
import re
import requests
import time
from colorama import init, Fore, Style

init(autoreset=True)

def extract_keys_from_env(filepath=".env"):
    """Estrae tutte le chiavi GEMINI_API_KEY (anche quelle commentate) dal file .env"""
    keys = {}
    current_label = "unknown"
    
    if not os.path.exists(filepath):
        print(f"{Fore.RED}File {filepath} non trovato.")
        return keys

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Cerca il commento sopra la chiave (es. #domedg3)
            if line.startswith("#") and "GEMINI" not in line and "=" not in line and len(line) > 1:
                current_label = line[1:].strip()
                
            # Cerca la definizione della chiave (sia commentata che attiva)
            match = re.search(r'GEMINI_API_KEY\s*=\s*["\']([^"\']+)["\']', line)
            if match:
                key = match.group(1)
                is_active = not line.startswith("#")
                keys[current_label] = {"key": key, "active": is_active}
                current_label = "unknown"
                
    return keys

def test_model(api_key, model_name):
    """Testa un modello specifico facendo una richiesta minima."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": "Hello"}]}]
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return f"{Fore.GREEN}Disponibile"
        elif response.status_code == 429:
            return f"{Fore.RED}Esaurito (429)"
        elif response.status_code == 400 and "API key not valid" in response.text:
            return f"{Fore.RED}Chiave Non Valida"
        elif response.status_code == 403:
            return f"{Fore.RED}Permesso Negato (403)"
        elif response.status_code == 503:
            return f"{Fore.YELLOW}Sovraccarico (503)"
        else:
            return f"{Fore.YELLOW}Errore {response.status_code}"
    except Exception as e:
        return f"{Fore.RED}Errore Rete"

def main():
    print(f"{Style.BRIGHT}{Fore.CYAN}--- Controllo Disponibilità API Keys Gemini ---")
    keys = extract_keys_from_env()
    
    if not keys:
        print("Nessuna chiave GEMINI_API_KEY trovata.")
        return
        
    print(f"Trovate {len(keys)} chiavi nel file .env.\n")
    
    models = [
        "gemini-flash-latest",
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-2.0-flash"
    ]
    
    for label, info in keys.items():
        active_str = f"[{Fore.GREEN}ATTIVA{Style.RESET_ALL}]" if info["active"] else f"[{Fore.YELLOW}COMMENTATA{Style.RESET_ALL}]"
        print(f"{Style.BRIGHT}Account: {label} {active_str}")
        print(f"Key: {info['key'][:8]}...{info['key'][-4:]}")
        
        for model in models:
            status = test_model(info["key"], model)
            print(f"  - {model:<20}: {status}")
            time.sleep(0.5) # Evita rate limit spam
            
        print("-" * 40)

if __name__ == "__main__":
    main()
