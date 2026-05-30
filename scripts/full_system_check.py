import sys
import subprocess
import os
from pathlib import Path

# FIX: Assicura che l'orchestratore operi sempre dalla root del progetto,
# indipendentemente da quale cartella l'utente lanci lo script.
REPO_ROOT = Path(__file__).resolve().parent.parent
os.chdir(REPO_ROOT)

# Codici colore ANSI per la Dashboard
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

def run_step(name, cmd, cwd=None):
    print(f"\n{YELLOW}▶ Esecuzione Gate: {name}{RESET}")
    
    # Adattamento automatico di pytest per garantire l'uso del virtual environment
    if cmd[0] == "pytest":
        cmd = [sys.executable, "-m", "pytest"] + cmd[1:]
    
    # Risoluzione compatibilità cross-platform per npm su Windows/WSL
    is_shell = True if os.name == 'nt' and cmd[0] in ['npm', 'npx'] else False
    
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, shell=is_shell)
    
    if result.returncode == 0:
        return True
    else:
        print(f"{RED}Dettaglio Errore in {name}:{RESET}\n{result.stdout}\n{result.stderr}")
        return False

def check_and_install_dependencies():
    print(f"\n{CYAN}🔍 Controllo dipendenze di sistema in corso...{RESET}")
    try:
        import fastapi
        import pytest
        import sqlmodel
    except ImportError:
        print(f"{YELLOW}⚠️ L'ambiente WSL risulta vuoto (mancano FastAPI e altre librerie).{RESET}")
        print(f"{YELLOW}⏳ Ricostruzione totale dell'ambiente da requirements.txt in corso... (Potrebbe volerci 1-2 minuti){RESET}")
        
        # Installa tutto il necessario
        cmd = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
        subprocess.run(cmd, check=True)
        
        # Esegue il download del modello linguistico per il modulo NLP (spaCy)
        print(f"{YELLOW}🧠 Download modello NLP (spaCy) in corso...{RESET}")
        cmd_spacy = [sys.executable, "-m", "spacy", "download", "it_core_news_sm"]
        subprocess.run(cmd_spacy, check=False)
        
        print(f"{GREEN}✅ Ambiente completamente ricostruito!{RESET}\n")

def main():
    print(f"\n{CYAN}======================================================{RESET}")
    print(f"{CYAN}🛡️  MASTER TEST ORCHESTRATOR & VALIDATION GATE 🛡️{RESET}")
    print(f"{CYAN}======================================================{RESET}\n")
    
    # Autonomus Optimization: auto-installazione dei pacchetti mancanti
    check_and_install_dependencies()
    
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    # 1. Backend Status (Unit tests & Coverage)
    backend_cmd = ["pytest", "tests/", "-v", "--cov=backend", "--html=reports/backend_coverage.html", "--self-contained-html", "--ignore=tests/locustfile.py", "--ignore=tests/test_integration.py", "--ignore=tests/test_dos.py"]
    backend_ok = run_step("Backend Unit & Coverage", backend_cmd)
    
    # 2. API Contract (Integration testing Ingestion+Polling)
    api_cmd = ["pytest", "tests/test_integration.py", "-v"]
    api_ok = run_step("API Contract Flow", api_cmd)
    
    # 3. Performance & Security Gate (DoS Prevention)
    dos_cmd = ["pytest", "tests/test_dos.py", "-v"]
    dos_ok = run_step("Performance Gate (Anti-DoS)", dos_cmd)
    
    # 4. Frontend Build Check (React Build Pipeline)
    frontend_dir = Path("frontend")
    if frontend_dir.exists():
        frontend_cmd = ["npm", "run", "build"]
        frontend_ok = run_step("Frontend Compilation Check", frontend_cmd, cwd=str(frontend_dir))
    else:
        frontend_ok = False
        print(f"{RED}Directory /frontend non trovata.{RESET}")

    # STAMPA DASHBOARD REPORT
    print("\n" + "="*50)
    print(f"📊 {GREEN}MASTER DASHBOARD REPORT{RESET}")
    print("="*50)
    
    def format_status(success):
        return f"[{GREEN}SUCCESS{RESET}]" if success else f"[{RED}FAIL{RESET}]   "
        
    print(f"{format_status(backend_ok)} Backend Status")
    print(f"{format_status(api_ok)} API Contract")
    print(f"{format_status(dos_ok)} Performance Gate")
    print(f"{format_status(frontend_ok)} Frontend Build")
    print("="*50)
    
    if not (backend_ok and api_ok and dos_ok and frontend_ok):
        print(f"\n{RED}❌ ERRORE CRITICO: Il Validation Gate ha bloccato la pipeline. Deploy abortito.{RESET}")
        sys.exit(1)
        
    print(f"\n{GREEN}✅ TUTTI I GATE SUPERATI. Il sistema è pronto per il deploy su Azure App Service.{RESET}\n")
    sys.exit(0)

if __name__ == "__main__":
    main()
