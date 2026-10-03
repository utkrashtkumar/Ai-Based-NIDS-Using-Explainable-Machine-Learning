# AI-NIDS User Guide & Operating Manual

Welcome to the **AI-Based Network Intrusion Detection System (AI-NIDS) with Explainable Machine Learning (TreeSHAP)**.

This system is designed to provide real-time endpoint protection on Windows machines, explaining detected network intrusions in plain English and visual Shapley attribution charts, with one-click Windows Firewall IP isolation.

---

## 🚀 1-Click Quick Start (For Public Users)

### First Time Setup:
1. Double-click [`install_prereqs.bat`](file:///s:/NIDS/install_prereqs.bat)
   * Automatically creates an isolated virtual environment (`.venv`).
   * Installs all Python dependencies.
   * Checks for the **Npcap driver** (required for raw packet capture). If missing, it provides a 1-click link to the official installer.

### Starting Protection:
2. Double-click [`Start_NIDS.bat`](file:///s:/NIDS/Start_NIDS.bat)
   * Prompts Windows Administrator permissions (required for raw network sniffing and firewall rules).
   * Launches the FastAPI AI backend.
   * Automatically opens your default web browser to: **`http://localhost:8000`**

---

## 🛡️ How to Use the System

### Mode 1: Live Sentinel (Real-Time Protection)
* **Status Ring:** When the indicator turns glowing green (**`PROTECTION ACTIVE`**), your network adapter is actively being monitored.
* **Network Adapter Selection:** Use the dropdown in the header to select your active Wi-Fi or Ethernet card.
* **Telemetry Dashboard:**
  * **Throughput Chart:** Real-time bandwidth streaming (KB/s and Packets/s).
  * **Host Risk Index:** Dynamic gauge showing current security posture (Low Risk, Elevated, Severe).
* **Live Intercepted Flows Table:** Displays all inbound and outbound 5-tuple sessions in real time.
* **What Happens When an Attack Occurs?**
  * An unobtrusive cyber-alert chime plays via the browser.
  * A slide-in **Intrusion Intercepted** alert card appears in the top-right corner.
  * Click **"Explain (XAI)"** to see the exact TreeSHAP waterfall chart and human-readable explanation of why the flow was flagged.
  * Click **"🛡️ Block IP in Firewall"** to immediately drop all future traffic from that remote host using Windows Defender Firewall.

---

### Mode 2: CSV Studio (Offline Benchmark Evaluation)
If you want to test how the AI model performs on standard datasets or pre-recorded attack logs:
1. Switch to the **CSV Studio** tab in the navigation bar.
2. Drag and drop any flow dataset CSV file into the upload zone.
   * *Tip:* Pre-packaged sample test files are located in `s:\NIDS\sample_data\`:
     * `sample_data/sample_attacks.csv` (500 mixed attacks: DoS/DDoS, PortScan, BruteForce, Botnet, Benign).
     * `sample_data/normal_traffic.csv` (100 legitimate web flows).
3. View the instant classification breakdown:
   * Total flows, Benign %, Threat %, and attack distribution tags.
   * Click **"Inspect"** on any flow to open the Explainable AI (XAI) modal.

---

### Mode 3: Threat History & Firewall Management
1. Switch to the **Threat History** tab.
2. **Active Windows Firewall Rules:** Displays all IP addresses currently isolated by AI-NIDS. Click the unlock icon to remove a rule anytime.
3. **Persistent Threat Audit Log (SQLite):** Permanently stores every flagged attack, confidence score, and plain-English narrative so past incidents are never lost upon rebooting.

---

## 🔧 Troubleshooting & FAQ

* **Q: Do I need Node.js or npm installed to run this project?**  
  **A:** No! The Next.js frontend has been pre-compiled into static distribution assets directly served by Python FastAPI. End users only need Python.
* **Q: Why does the app request Administrator rights on launch?**  
  **A:** Administrator privileges are required on Windows to:
  1. Access raw network packet sockets via Npcap.
  2. Insert inbound block rules into Windows Defender Firewall (`netsh advfirewall`).
* **Q: What if I don't have Npcap installed?**  
  **A:** The application will automatically fall back to **Simulation Mode**, generating realistic synthetic flows so all charts, alerts, and XAI explainers remain fully interactive for demonstrations.
