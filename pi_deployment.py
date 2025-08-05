#!/usr/bin/env python3
"""
Raspberry Pi Deployment Automation
Automatisiert die Vorbereitung und das Deployment auf Raspberry Pi
"""

import os
import shutil
import subprocess
import zipfile
from pathlib import Path

def create_deployment_package():
    """Erstelle ein Deployment-Paket für Raspberry Pi"""
    print("📦 Erstelle Deployment-Paket...")
    
    # Deployment-Verzeichnis erstellen
    deploy_dir = Path("deploy_package")
    if deploy_dir.exists():
        shutil.rmtree(deploy_dir)
    deploy_dir.mkdir()
    
    # Kritische Dateien kopieren
    critical_files = [
        "main.py",
        "enhanced_telegram_bot.py", 
        "cex_price_provider.py",
        "cex_trading_api.py",
        "unified_arbitrage_scanner.py",
        "optimization_config.py",
        "requirements.txt",
        "Dockerfile",
        "docker-compose.yml",
        ".env.example"
    ]
    
    print("📋 Kopiere kritische Dateien:")
    for file in critical_files:
        if os.path.exists(file):
            shutil.copy2(file, deploy_dir)
            print(f"   ✅ {file}")
        else:
            print(f"   ⚠️  {file} nicht gefunden")
    
    # Contracts Verzeichnis kopieren
    if os.path.exists("contracts"):
        shutil.copytree("contracts", deploy_dir / "contracts")
        print("   ✅ contracts/")
    
    # Python Scanner kopieren
    if os.path.exists("python_scanner"):
        shutil.copytree("python_scanner", deploy_dir / "python_scanner") 
        print("   ✅ python_scanner/")
    
    # README für Deployment erstellen
    readme_content = """# BSC Arbitrage System - Raspberry Pi Deployment

## Schnellstart

1. **System vorbereiten:**
   ```bash
   sudo apt update && sudo apt upgrade -y
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   ```

2. **Environment konfigurieren:**
   ```bash
   cp .env.example .env
   nano .env  # Ihre API-Keys eintragen
   ```

3. **System starten:**
   ```bash
   docker-compose up -d
   ```

4. **Logs prüfen:**
   ```bash
   docker-compose logs -f
   ```

## Wichtige Einstellungen in .env

```bash
# BSC Blockchain
BSC_RPC_URL=https://bsc-dataseed1.binance.org/
PRIVATE_KEY=your_private_key_here

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Trading Parameter  
MIN_PROFIT_THRESHOLD=0.5
MAX_GAS_PRICE=5
SCAN_INTERVAL=10
ENABLE_EXECUTION=false  # Für Live-Trading auf true setzen

# CEX API Keys (optional)
BINANCE_API_KEY=your_binance_key
BINANCE_SECRET=your_binance_secret
GATE_API_KEY=your_gate_key
GATE_SECRET=your_gate_secret
```

## System-Monitoring

- **Telegram Bot**: /stats, /help, /status
- **Docker Logs**: `docker-compose logs -f`
- **System Status**: `docker-compose ps`

## Troubleshooting

- **Container startet nicht**: `docker-compose logs`
- **API Fehler**: Environment-Variablen prüfen
- **Out of Memory**: Resource-Limits in docker-compose.yml anpassen
"""
    
    with open(deploy_dir / "README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print("   ✅ README.md erstellt")
    
    # ZIP-Archiv erstellen
    print("\n📦 Erstelle ZIP-Archiv...")
    with zipfile.ZipFile("bsc_arbitrage_pi_deployment.zip", 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(deploy_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arc_name = os.path.relpath(file_path, deploy_dir)
                zipf.write(file_path, arc_name)
    
    print("✅ bsc_arbitrage_pi_deployment.zip erstellt")
    
    # Cleanup
    shutil.rmtree(deploy_dir)
    
    return "bsc_arbitrage_pi_deployment.zip"

def generate_pi_setup_commands():
    """Generiere Setup-Befehle für Raspberry Pi"""
    
    commands = """
# RASPBERRY PI SETUP BEFEHLE
# Diese Befehle auf dem Raspberry Pi ausführen

# 1. System Update
sudo apt update && sudo apt upgrade -y

# 2. Docker Installation  
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 3. Docker Compose Installation
sudo apt install -y docker-compose

# 4. System Neustart (wichtig für Docker-Gruppen)
sudo reboot

# Nach Neustart:

# 5. Projektverzeichnis erstellen
mkdir -p /home/pi/arbitrage
cd /home/pi/arbitrage

# 6. Deployment-Paket entpacken (ZIP-Datei hierher übertragen)
unzip bsc_arbitrage_pi_deployment.zip

# 7. Environment konfigurieren
cp .env.example .env
nano .env  # Ihre API-Keys eintragen

# 8. System starten
docker-compose up -d

# 9. Status prüfen
docker-compose ps
docker-compose logs -f

# 10. Auto-Start nach Reboot aktivieren
echo '@reboot cd /home/pi/arbitrage && docker-compose up -d' | crontab -
"""
    
    with open("pi_setup_commands.txt", "w", encoding="utf-8") as f:
        f.write(commands)
    
    print("✅ pi_setup_commands.txt erstellt")

def print_deployment_guide():
    """Drucke komplette Deployment-Anleitung"""
    
    print("\n🥧 RASPBERRY PI DEPLOYMENT GUIDE")
    print("=" * 50)
    
    print("\n📋 SCHRITT 1: LOKALE VORBEREITUNG")
    print("-" * 35)
    print("✅ Deployment-Paket erstellt: bsc_arbitrage_pi_deployment.zip")
    print("✅ Setup-Befehle generiert: pi_setup_commands.txt")
    print("✅ Alle kritischen Dateien gepackt")
    
    print("\n📤 SCHRITT 2: DATEI-ÜBERTRAGUNG")
    print("-" * 35)
    print("Wählen Sie eine der folgenden Methoden:")
    print("")
    print("Option A - USB-Stick (einfachste):")
    print("   1. Kopieren Sie bsc_arbitrage_pi_deployment.zip auf USB-Stick")
    print("   2. Stecken Sie USB-Stick in Raspberry Pi")
    print("   3. Kopieren Sie die Datei: cp /media/usb/bsc_arbitrage_pi_deployment.zip ~/")
    print("")
    print("Option B - SCP (über Netzwerk):")
    print("   scp bsc_arbitrage_pi_deployment.zip pi@raspberry-pi-ip:~/")
    print("")
    print("Option C - WinSCP/FileZilla (GUI):")
    print("   • Verwenden Sie WinSCP oder FileZilla")
    print("   • Verbinden Sie sich mit Raspberry Pi")
    print("   • Übertragen Sie die ZIP-Datei")
    
    print("\n🔧 SCHRITT 3: RASPBERRY PI SETUP")
    print("-" * 35)
    print("Führen Sie diese Befehle auf dem Raspberry Pi aus:")
    print("(Alle Befehle auch in pi_setup_commands.txt)")
    print("")
    print("1. SSH-Verbindung:")
    print("   ssh pi@raspberry-pi-ip")
    print("")
    print("2. System Update:")
    print("   sudo apt update && sudo apt upgrade -y")
    print("")
    print("3. Docker Installation:")
    print("   curl -fsSL https://get.docker.com -o get-docker.sh")
    print("   sudo sh get-docker.sh")
    print("   sudo usermod -aG docker $USER")
    print("")
    print("4. Neustart (wichtig!):")
    print("   sudo reboot")
    
    print("\n🚀 SCHRITT 4: DEPLOYMENT")
    print("-" * 25)
    print("Nach dem Neustart:")
    print("")
    print("1. Projektverzeichnis:")
    print("   mkdir -p ~/arbitrage && cd ~/arbitrage")
    print("")
    print("2. ZIP entpacken:")
    print("   unzip ~/bsc_arbitrage_pi_deployment.zip")
    print("")
    print("3. Environment konfigurieren:")
    print("   cp .env.example .env")
    print("   nano .env  # Ihre API-Keys eintragen!")
    print("")
    print("4. System starten:")
    print("   docker-compose up -d")
    print("")
    print("5. Status prüfen:")
    print("   docker-compose logs -f")
    
    print("\n⚙️ SCHRITT 5: KONFIGURATION")
    print("-" * 30)
    print("Wichtige Einstellungen in .env:")
    print("")
    print("# Pflicht-Einstellungen:")
    print("BSC_RPC_URL=https://bsc-dataseed1.binance.org/")
    print("TELEGRAM_BOT_TOKEN=your_bot_token")
    print("TELEGRAM_CHAT_ID=your_chat_id")
    print("")
    print("# Trading (optional):")
    print("PRIVATE_KEY=your_private_key")
    print("ENABLE_EXECUTION=false  # Für Live-Trading: true")
    print("")
    print("# CEX APIs (optional):")
    print("BINANCE_API_KEY=your_key")
    print("GATE_API_KEY=your_key")
    
    print("\n📊 SCHRITT 6: MONITORING")
    print("-" * 25)
    print("• Telegram Bot: /stats, /help, /status")
    print("• Docker Logs: docker-compose logs -f")
    print("• System Status: docker-compose ps")
    print("• Neustart: docker-compose restart")
    print("• Stop: docker-compose down")
    
    print("\n🔄 SCHRITT 7: AUTO-START")
    print("-" * 25)
    print("Für automatischen Start nach Reboot:")
    print("echo '@reboot cd /home/pi/arbitrage && docker-compose up -d' | crontab -")
    
    print("\n✅ DEPLOYMENT COMPLETE!")
    print("Ihr BSC Arbitrage System läuft jetzt auf dem Raspberry Pi!")

if __name__ == "__main__":
    print("🚀 BSC Arbitrage System - Raspberry Pi Deployment")
    print("=" * 55)
    
    # Deployment-Paket erstellen
    zip_file = create_deployment_package()
    
    # Setup-Befehle generieren  
    generate_pi_setup_commands()
    
    # Deployment-Guide anzeigen
    print_deployment_guide()
