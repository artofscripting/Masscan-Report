# Masscan Report Generator

A Python tool that generates interactive React-based HTML visualizations from masscan JSON output, featuring a D3.js force-directed network graph.

![Network Visualization](https://img.shields.io/badge/visualization-D3.js-orange)
![React](https://img.shields.io/badge/frontend-React%2018-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-green)

## Features

### Interactive Network Graph
- **Force-directed D3.js visualization** showing network topology
- **Hierarchical structure**: Internet → Class A (/8) → Class B (/16) → Class C (/24) → Hosts → Ports
- **Drag and zoom** to explore the network
- **Color-coded nodes** by type (hosts, ports, network segments)

### Search & Filter
- **Live search** - filter hosts and ports as you type
- **Port search prefix** - use `:` to search ports only (e.g., `:443`)
- **Wildcard support** - use `*` for pattern matching (e.g., `:*443`, `:80*`, `:*8*`)
- **Real-time highlighting** of matching nodes on the graph

### Host Details Modal
- Click any graph node to view detailed information
- **Host nodes** display all open ports with service descriptions
- **Port nodes** show service info, protocol, and security risk level
- **Security badges** color-coded: HIGH (red), MEDIUM (yellow), LOW (teal), SECURE (cyan)
- Links to documentation for each service

### PDF Export
- **Professional PDF reports** with dark theme styling
- **Title page** with summary statistics
- **Graph screenshot** captured from current view
- **Executive summary** in natural language
- **Host details** organized by network class

### Sidebar Navigation
- List of all discovered hosts with their open ports
- Click to highlight host and child nodes on graph
- Port badges for quick identification

## Installation

### From Source
```bash
# Clone or download the project
cd masscan_report

# Install dependencies (optional, only needed for PDF generation in development)
pip install pyinstaller  # Only if building exe
```

### Standalone Executable
Download `masscan_report.exe` from the `dist/` folder - no Python installation required.

## Usage

### Command Line

```bash
# Using Python
python masscan_report.py <input_json> [-o output.html]

# Using executable
masscan_report.exe <input_json> [-o output.html]
```

### Examples

```bash
# Generate report with default output (report.html)
python masscan_report.py scans/home.json

# Specify custom output file
python masscan_report.py scans/network_scan.json -o network_report.html

# Using the executable
.\dist\masscan_report.exe .\scans\home.192.168.10000.json
```

### Input Format

The tool expects masscan JSON output format:

```json
[
  {"ip": "192.168.1.1", "timestamp": "1234567890", "ports": [
    {"port": 80, "proto": "tcp", "status": "open", "reason": "syn-ack", "ttl": 64}
  ]},
  {"ip": "192.168.1.1", "timestamp": "1234567891", "ports": [
    {"port": 443, "proto": "tcp", "status": "open", "reason": "syn-ack", "ttl": 64}
  ]}
]
```

Generate this with masscan:
```bash
masscan 192.168.1.0/24 -p1-65535 --rate 1000 -oJ scan_results.json
```

## Keyboard & Mouse Controls

| Action | Effect |
|--------|--------|
| Click node (graph) | Open info modal |
| Click host (sidebar) | Highlight host and ports |
| Drag node | Reposition node |
| Scroll wheel | Zoom in/out |
| Click + drag (background) | Pan view |
| 🔄 Reset View | Reset zoom and position |
| ⚡ Reheat | Re-energize the force simulation |
| 📄 Export PDF | Generate PDF report |

## Search Syntax

| Pattern | Matches |
|---------|---------|
| `192.168` | IPs containing "192.168" |
| `:443` | Exactly port 443 |
| `:*443` | Ports ending with 443 (e.g., 8443) |
| `:443*` | Ports starting with 443 |
| `:*8*` | Ports containing 8 (e.g., 80, 8080, 443) |

## Project Structure

```
masscan_report/
├── masscan_report.py      # Main script
├── port_descriptions.py   # Port database (6700+ lines)
├── scans/                  # Sample scan files
│   ├── home.json
│   └── home.192.168.10000.json
├── dist/
│   └── masscan_report.exe # Standalone executable
├── report.html            # Generated output
└── README.md
```

## Port Descriptions Database

The `port_descriptions.py` contains detailed information for 130+ common ports including:
- Service name and description
- Technical details
- Security risk assessment
- Documentation links

## Building the Executable

```bash
pip install pyinstaller
pyinstaller --onefile --name masscan_report --add-data "port_descriptions.py;." masscan_report.py
```

The executable will be created in `dist/masscan_report.exe`.

## Requirements

- Python 3.8+ (for running from source)
- Modern web browser (for viewing reports)
- No additional Python packages required (uses only standard library)

## License

MIT License

## Contributing

Contributions welcome! Feel free to submit issues and pull requests.
