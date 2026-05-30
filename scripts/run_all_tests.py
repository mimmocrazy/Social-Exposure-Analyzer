import os
import sys
import subprocess
from pathlib import Path

# ANSI color codes for CI/CD like output
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

def main():
    print("🔄 Inizializzazione Orchestratore di Test (CI/CD Mockup)...")
    
    # Autonomous Optimization: Generiamo dinamicamente il folder report
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    # Autonomous Optimization: Escludiamo i test asincroni per Locust 
    # dall'esecutore pytest per evitare failure fittizi.
    # Il DB SQLite resta quello in-memory definito nel conftest.py
    cmd = [
        sys.executable,
        "-m", "pytest",
        "tests/",
        "-v",
        "--cov=backend",
        "--html=reports/test_report.html",
        "--self-contained-html",
        "--ignore=tests/locustfile.py"
    ]
    
    print(f"🚀 Esecuzione suite in corso...")
    
    result = subprocess.run(cmd)
    
    print("\n" + "="*60)
    if result.returncode == 0:
        print(f"{GREEN}✅ SUCCESSO: Tutti i test sono passati con successo!{RESET}")
        print(f"{GREEN}📊 Il report di coverage è disponibile in: reports/test_report.html{RESET}")
        sys.exit(0)
    else:
        print(f"{RED}❌ FALLITO: Regressioni o test falliti. Pipeline CI bloccata.{RESET}")
        sys.exit(result.returncode)

if __name__ == "__main__":
    main()
