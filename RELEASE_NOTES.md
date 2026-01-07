# Release Notes

## v1.0.0 - January 7, 2026

### 🎉 Initial Release

Masscan Report Generator is a tool that transforms masscan JSON output into interactive, visually rich HTML reports featuring D3.js force-directed network visualizations.

---

### ✨ Features

#### Interactive Network Visualization
- **Force-directed D3.js graph** displaying network topology in real-time
- **Hierarchical network structure** showing Internet → Class A (/8) → Class B (/16) → Class C (/24) → Hosts → Ports
- **Drag-and-drop nodes** to manually arrange the visualization
- **Zoom and pan** controls for exploring large networks
- **Color-coded nodes** for easy identification:
  - 🔴 Red: Internet gateway
  - 🟠 Orange: Class A networks
  - 🟡 Yellow: Class B networks
  - 🩵 Teal: Class C networks
  - 🔵 Cyan: Hosts
  - 🟣 Purple: Open ports

#### Smart Search & Filtering
- **Live search** with real-time graph highlighting as you type
- **Port-specific search** using `:` prefix (e.g., `:443` for HTTPS)
- **Wildcard pattern matching**:
  - `:443` - exact match
  - `:*443` - ends with (matches 8443)
  - `:443*` - starts with
  - `:*8*` - contains
- **Sidebar filtering** showing only matching hosts

#### Detailed Information Modal
- Click any graph node to view comprehensive details
- **Host information** displays all open ports with:
  - Service name and description
  - Technical details
  - Security risk assessment (HIGH/MEDIUM/LOW/SECURE)
  - Documentation links
- **Port information** shows service details and parent host
- **Network information** for subnet nodes

#### PDF Report Generation
- **Professional multi-page PDF reports** with dark theme styling
- **Title page** with scan statistics
- **Graph screenshot** captured from current visualization state
- **Executive summary** written in natural language prose
- **Key findings** with actionable insights
- **Host details** organized by network class (/24 subnets)
- **Security indicators** for each discovered service

#### Sidebar Navigation
- Complete list of discovered hosts
- Port badges showing open services at a glance
- Click to highlight host and its ports on the graph
- Search results counter

#### Port Intelligence Database
- **130+ port descriptions** with detailed information
- Service names and technical details
- Security risk assessments
- Links to official documentation

---

### 📦 Distribution

- **Python script** (`masscan_report.py`) - runs with Python 3.8+
- **Standalone executable** (`masscan_report.exe`) - no Python required
- **Zero dependencies** - uses only Python standard library

---

### 🚀 Usage

```bash
# Python
python masscan_report.py scan_results.json -o report.html

# Executable
masscan_report.exe scan_results.json -o report.html
```

---

### 🔧 Technical Details

- **Frontend**: React 18 with Babel (inline compilation)
- **Visualization**: D3.js v7 force simulation
- **PDF Generation**: jsPDF + html2canvas
- **Styling**: Custom dark theme CSS
- **Build Tool**: PyInstaller for executable packaging

---

### 📋 Input Format

Accepts standard masscan JSON output (`-oJ` flag):

```bash
masscan 192.168.0.0/16 -p1-65535 --rate 10000 -oJ results.json
```

---

### 🙏 Acknowledgments

- D3.js for the force-directed graph library
- React team for the UI framework
- jsPDF for PDF generation capabilities
- The masscan project for the excellent network scanner
