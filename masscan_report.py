#!/usr/bin/env python3
"""
Generate a React HTML page with D3 force-directed chart from masscan JSON data.
"""

import json
import os
from datetime import datetime

try:
    from port_descriptions import PORT_DESCRIPTIONS
except ImportError:
    PORT_DESCRIPTIONS = {}

def load_scan_data(json_file):
    """Load and parse masscan JSON data."""
    with open(json_file, 'r') as f:
        data = json.load(f)
    return data

def transform_to_graph_data(scan_data):
    """Transform masscan data to D3 force-directed graph format."""
    nodes = []
    links = []
    node_ids = set()
    ip_ports = {}  # Track ports per IP
    
    # Group ports by IP
    for entry in scan_data:
        ip = entry['ip']
        if ip not in ip_ports:
            ip_ports[ip] = []
        for port_info in entry.get('ports', []):
            ip_ports[ip].append(port_info)
    
    # Create network node (central hub)
    nodes.append({
        'id': 'network',
        'label': 'Internet',
        'type': 'network',
        'group': 0
    })
    node_ids.add('network')
    
    # Create nodes and links
    for ip, ports in ip_ports.items():
        octets = ip.split('.')
        
        # Class A network (first octet, e.g., 192.0.0.0/8)
        class_a_id = f"{octets[0]}.0.0.0/8"
        if class_a_id not in node_ids:
            nodes.append({
                'id': class_a_id,
                'label': class_a_id,
                'type': 'class_a',
                'group': 1
            })
            node_ids.add(class_a_id)
            # Link Class A to network hub
            links.append({
                'source': 'network',
                'target': class_a_id,
                'value': 1
            })
        
        # Class B network (first two octets, e.g., 192.168.0.0/16)
        class_b_id = f"{octets[0]}.{octets[1]}.0.0/16"
        if class_b_id not in node_ids:
            nodes.append({
                'id': class_b_id,
                'label': class_b_id,
                'type': 'class_b',
                'group': 2
            })
            node_ids.add(class_b_id)
            # Link Class B to Class A
            links.append({
                'source': class_a_id,
                'target': class_b_id,
                'value': 1
            })
        
        # Class C network (first three octets, e.g., 192.168.1.0/24)
        class_c_id = f"{octets[0]}.{octets[1]}.{octets[2]}.0/24"
        if class_c_id not in node_ids:
            nodes.append({
                'id': class_c_id,
                'label': class_c_id,
                'type': 'class_c',
                'group': 3
            })
            node_ids.add(class_c_id)
            # Link Class C to Class B
            links.append({
                'source': class_b_id,
                'target': class_c_id,
                'value': 1
            })
        
        # Add IP node (host)
        if ip not in node_ids:
            nodes.append({
                'id': ip,
                'label': ip,
                'type': 'host',
                'group': 4,
                'ports': [p['port'] for p in ports]
            })
            node_ids.add(ip)
            
            # Link host to Class C network
            links.append({
                'source': class_c_id,
                'target': ip,
                'value': 1
            })
        
        # Add port nodes (distinct per host)
        for port_info in ports:
            port = port_info['port']
            port_id = f"{ip}_port_{port}"  # Unique per host
            
            if port_id not in node_ids:
                nodes.append({
                    'id': port_id,
                    'label': f":{port}",
                    'type': 'port',
                    'group': 99,
                    'port': port,
                    'proto': port_info.get('proto', 'tcp'),
                    'host': ip
                })
                node_ids.add(port_id)
            
                # Link IP to port
                links.append({
                    'source': ip,
                    'target': port_id,
                    'value': 2
                })
    
    return {'nodes': nodes, 'links': links}

def generate_html(graph_data, output_file='report.html'):
    """Generate the React HTML page with D3 visualization."""
    
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Network Scan Report</title>
    <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
    <script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: #1a1a2e;
            color: #eee;
            overflow: hidden;
        }
        
        .app-container {
            display: flex;
            flex-direction: column;
            height: 100vh;
        }
        
        /* Header Styles */
        .header {
            background: linear-gradient(135deg, #16213e 0%, #1a1a2e 100%);
            padding: 15px 25px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #0f3460;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }
        
        .header h1 {
            font-size: 1.5rem;
            background: linear-gradient(90deg, #e94560, #0f3460);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .header-info {
            display: flex;
            gap: 20px;
            font-size: 0.85rem;
            color: #888;
        }
        
        .header-info span {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        /* Main Layout */
        .main-layout {
            display: flex;
            flex: 1;
            overflow: hidden;
        }
        
        /* Sidebar Styles */
        .sidebar {
            width: 280px;
            background: #16213e;
            border-right: 1px solid #0f3460;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .sidebar-header {
            padding: 15px;
            border-bottom: 1px solid #0f3460;
            font-weight: 600;
            color: #e94560;
        }
        
        .sidebar-content {
            flex: 1;
            overflow-y: auto;
            padding: 10px;
        }
        
        .sidebar-section {
            margin-bottom: 20px;
        }
        
        .sidebar-section h3 {
            font-size: 0.75rem;
            text-transform: uppercase;
            color: #666;
            margin-bottom: 10px;
            letter-spacing: 1px;
        }
        
        .host-item {
            padding: 10px 12px;
            margin-bottom: 5px;
            background: rgba(15, 52, 96, 0.3);
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
            border-left: 3px solid transparent;
        }
        
        .host-item:hover {
            background: rgba(15, 52, 96, 0.6);
            border-left-color: #e94560;
        }
        
        .host-item.selected {
            background: rgba(233, 69, 96, 0.2);
            border-left-color: #e94560;
        }
        
        .host-ip {
            font-weight: 500;
            margin-bottom: 4px;
        }
        
        .host-ports {
            font-size: 0.75rem;
            color: #888;
        }
        
        .port-badge {
            display: inline-block;
            background: #0f3460;
            padding: 2px 6px;
            border-radius: 3px;
            margin: 2px;
            font-size: 0.7rem;
        }
        
        /* Legend */
        .legend {
            padding: 15px;
            border-top: 1px solid #0f3460;
        }
        
        /* Search Input */
        .search-container {
            padding: 15px;
            border-bottom: 1px solid #0f3460;
        }
        
        .search-input {
            width: 100%;
            padding: 10px 12px;
            background: rgba(15, 52, 96, 0.5);
            border: 1px solid #0f3460;
            border-radius: 6px;
            color: #eee;
            font-size: 0.9rem;
            outline: none;
            transition: all 0.2s;
        }
        
        .search-input:focus {
            border-color: #e94560;
            background: rgba(15, 52, 96, 0.8);
        }
        
        .search-input::placeholder {
            color: #666;
        }
        
        .search-results {
            font-size: 0.75rem;
            color: #888;
            margin-top: 8px;
        }
        
        .search-results .highlight {
            color: #e94560;
            font-weight: 600;
        }
        
        .host-item.search-match {
            background: rgba(233, 69, 96, 0.15);
            border-left-color: #f7c548;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;
            font-size: 0.8rem;
        }
        
        .legend-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }
        
        /* Main Content */
        .main-content {
            flex: 1;
            position: relative;
            overflow: hidden;
        }
        
        #chart-container {
            width: 100%;
            height: 100%;
        }
        
        #chart-container svg {
            width: 100%;
            height: 100%;
        }
        
        /* Node Tooltip */
        .tooltip {
            position: absolute;
            background: rgba(22, 33, 62, 0.95);
            border: 1px solid #0f3460;
            border-radius: 8px;
            padding: 12px;
            font-size: 0.85rem;
            pointer-events: none;
            z-index: 1000;
            box-shadow: 0 4px 20px rgba(0,0,0,0.4);
            min-width: 150px;
        }
        
        .tooltip-title {
            font-weight: 600;
            color: #e94560;
            margin-bottom: 8px;
        }
        
        .tooltip-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 4px;
            color: #aaa;
        }
        
        .tooltip-label {
            color: #666;
        }
        
        /* Controls */
        .controls {
            position: absolute;
            top: 15px;
            right: 15px;
            display: flex;
            gap: 10px;
            z-index: 100;
        }
        
        .control-btn {
            background: rgba(22, 33, 62, 0.9);
            border: 1px solid #0f3460;
            color: #eee;
            padding: 8px 15px;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 0.85rem;
        }
        
        .control-btn:hover {
            background: #0f3460;
            border-color: #e94560;
        }
        
        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 6px;
        }
        
        ::-webkit-scrollbar-track {
            background: #1a1a2e;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #0f3460;
            border-radius: 3px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #e94560;
        }
        
        /* Modal Styles */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.7);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            backdrop-filter: blur(4px);
        }
        
        .modal {
            background: linear-gradient(135deg, #16213e 0%, #1a1a2e 100%);
            border: 1px solid #0f3460;
            border-radius: 12px;
            max-width: 600px;
            width: 90%;
            max-height: 80vh;
            overflow: hidden;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
        }
        
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px;
            border-bottom: 1px solid #0f3460;
            background: rgba(15, 52, 96, 0.3);
        }
        
        .modal-title {
            font-size: 1.2rem;
            font-weight: 600;
            color: #e94560;
        }
        
        .modal-close {
            background: none;
            border: none;
            color: #888;
            font-size: 1.5rem;
            cursor: pointer;
            transition: color 0.2s;
            padding: 0;
            line-height: 1;
        }
        
        .modal-close:hover {
            color: #e94560;
        }
        
        .modal-body {
            padding: 20px;
            overflow-y: auto;
            max-height: calc(80vh - 80px);
        }
        
        .modal-section {
            margin-bottom: 20px;
        }
        
        .modal-section:last-child {
            margin-bottom: 0;
        }
        
        .modal-section-title {
            font-size: 0.75rem;
            text-transform: uppercase;
            color: #666;
            margin-bottom: 10px;
            letter-spacing: 1px;
        }
        
        .modal-info-row {
            display: flex;
            padding: 8px 0;
            border-bottom: 1px solid rgba(15, 52, 96, 0.5);
        }
        
        .modal-info-row:last-child {
            border-bottom: none;
        }
        
        .modal-info-label {
            color: #888;
            width: 100px;
            flex-shrink: 0;
        }
        
        .modal-info-value {
            color: #eee;
            flex: 1;
        }
        
        .port-card {
            background: rgba(15, 52, 96, 0.3);
            border: 1px solid #0f3460;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 10px;
        }
        
        .port-card:last-child {
            margin-bottom: 0;
        }
        
        .port-card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        
        .port-number {
            font-size: 1.1rem;
            font-weight: 600;
            color: #7209b7;
        }
        
        .port-service {
            color: #4cc9f0;
            font-size: 0.9rem;
        }
        
        .port-description {
            color: #aaa;
            font-size: 0.85rem;
            margin-bottom: 6px;
        }
        
        .port-security {
            font-size: 0.8rem;
            padding: 4px 8px;
            border-radius: 4px;
            display: inline-block;
        }
        
        .port-security.high {
            background: rgba(233, 69, 96, 0.2);
            color: #e94560;
        }
        
        .port-security.medium {
            background: rgba(247, 197, 72, 0.2);
            color: #f7c548;
        }
        
        .port-security.low {
            background: rgba(69, 183, 170, 0.2);
            color: #45b7aa;
        }
        
        .port-security.secure {
            background: rgba(76, 201, 240, 0.2);
            color: #4cc9f0;
        }
        
        .port-link {
            color: #4cc9f0;
            text-decoration: none;
            font-size: 0.8rem;
        }
        
        .port-link:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div id="root"></div>
    
    <script type="text/babel">
        // Graph data from Python
        const graphData = ''' + json.dumps(graph_data, indent=2) + ''';
        
        // Port descriptions from Python
        const portDescriptions = ''' + json.dumps({str(k): v for k, v in PORT_DESCRIPTIONS.items()}, indent=2) + ''';
        
        // Get security class for styling
        const getSecurityClass = (security) => {
            if (!security) return '';
            const s = security.toLowerCase();
            if (s.includes('high')) return 'high';
            if (s.includes('medium')) return 'medium';
            if (s.includes('secure')) return 'secure';
            return 'low';
        };
        
        // Modal Component
        const Modal = ({ node, onClose }) => {
            if (!node) return null;
            
            const getPortInfo = (port) => {
                return portDescriptions[port.toString()] || {
                    description: 'Unknown Service',
                    details: 'No information available for this port.',
                    security: 'UNKNOWN',
                    link: null
                };
            };
            
            const renderHostContent = () => (
                <div className="modal-section">
                    <div className="modal-section-title">Open Ports</div>
                    {node.ports && node.ports.length > 0 ? (
                        node.ports.map(port => {
                            const info = getPortInfo(port);
                            return (
                                <div key={port} className="port-card">
                                    <div className="port-card-header">
                                        <span className="port-number">:{port}</span>
                                        <span className="port-service">{info.description}</span>
                                    </div>
                                    <div className="port-description">{info.details}</div>
                                    <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                                        <span className={`port-security ${getSecurityClass(info.security)}`}>
                                            {info.security}
                                        </span>
                                        {info.link && (
                                            <a href={info.link} target="_blank" rel="noopener noreferrer" className="port-link">
                                                Learn more →
                                            </a>
                                        )}
                                    </div>
                                </div>
                            );
                        })
                    ) : (
                        <div style={{color: '#888'}}>No ports discovered</div>
                    )}
                </div>
            );
            
            const renderPortContent = () => {
                const info = getPortInfo(node.port);
                return (
                    <div className="modal-section">
                        <div className="modal-section-title">Port Information</div>
                        <div className="port-card">
                            <div className="port-card-header">
                                <span className="port-number">:{node.port}</span>
                                <span className="port-service">{info.description}</span>
                            </div>
                            <div className="port-description">{info.details}</div>
                            <div className="modal-info-row">
                                <span className="modal-info-label">Protocol:</span>
                                <span className="modal-info-value">{node.proto || 'tcp'}</span>
                            </div>
                            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '10px'}}>
                                <span className={`port-security ${getSecurityClass(info.security)}`}>
                                    {info.security}
                                </span>
                                {info.link && (
                                    <a href={info.link} target="_blank" rel="noopener noreferrer" className="port-link">
                                        Learn more →
                                    </a>
                                )}
                            </div>
                        </div>
                        {node.host && (
                            <div style={{marginTop: '15px', color: '#888', fontSize: '0.85rem'}}>
                                Host: <span style={{color: '#4cc9f0'}}>{node.host}</span>
                            </div>
                        )}
                    </div>
                );
            };
            
            const renderNetworkContent = () => (
                <div className="modal-section">
                    <div className="modal-section-title">Network Information</div>
                    <div className="modal-info-row">
                        <span className="modal-info-label">Type:</span>
                        <span className="modal-info-value">
                            {node.type === 'network' && 'Internet Gateway'}
                            {node.type === 'class_a' && 'Class A Network (/8)'}
                            {node.type === 'class_b' && 'Class B Network (/16)'}
                            {node.type === 'class_c' && 'Class C Network (/24)'}
                        </span>
                    </div>
                    <div className="modal-info-row">
                        <span className="modal-info-label">CIDR:</span>
                        <span className="modal-info-value">{node.label}</span>
                    </div>
                </div>
            );
            
            const getTitle = () => {
                switch(node.type) {
                    case 'host': return `Host: ${node.label}`;
                    case 'port': return `Port: ${node.label}`;
                    case 'network': return 'Internet';
                    case 'class_a':
                    case 'class_b':
                    case 'class_c': return `Network: ${node.label}`;
                    default: return node.label;
                }
            };
            
            return (
                <div className="modal-overlay" onClick={onClose}>
                    <div className="modal" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <div className="modal-title">{getTitle()}</div>
                            <button className="modal-close" onClick={onClose}>×</button>
                        </div>
                        <div className="modal-body">
                            {node.type === 'host' && renderHostContent()}
                            {node.type === 'port' && renderPortContent()}
                            {(node.type === 'network' || node.type === 'class_a' || node.type === 'class_b' || node.type === 'class_c') && renderNetworkContent()}
                        </div>
                    </div>
                </div>
            );
        };
        
        // Header Component
        const Header = ({ nodeCount, linkCount }) => (
            <header className="header">
                <h1>🔍 Network Scan Report</h1>
                <div className="header-info">
                    <span>📡 {nodeCount} Nodes</span>
                    <span>🔗 {linkCount} Connections</span>
                    <span>📅 ''' + datetime.now().strftime('%Y-%m-%d %H:%M') + '''</span>
                </div>
            </header>
        );
        
        // Sidebar Component
        const Sidebar = ({ hosts, selectedNode, onNodeSelect, searchQuery, onSearchChange }) => {
            const filteredHosts = hosts.filter(host => {
                if (!searchQuery) return true;
                const query = searchQuery.toLowerCase();
                const matchesIP = host.label.toLowerCase().includes(query);
                const matchesPort = host.ports && host.ports.some(p => p.toString().includes(query));
                return matchesIP || matchesPort;
            });
            
            const matchCount = searchQuery ? filteredHosts.length : 0;
            
            return (
            <aside className="sidebar">
                <div className="sidebar-header">
                    📊 Discovered Hosts
                </div>
                <div className="search-container">
                    <input 
                        type="text"
                        className="search-input"
                        placeholder="🔍 Search IP or port..."
                        value={searchQuery}
                        onChange={(e) => onSearchChange(e.target.value)}
                    />
                    {searchQuery && (
                        <div className="search-results">
                            Found <span className="highlight">{matchCount}</span> matching host{matchCount !== 1 ? 's' : ''}
                        </div>
                    )}
                </div>
                <div className="sidebar-content">
                    <div className="sidebar-section">
                        <h3>Hosts ({filteredHosts.length})</h3>
                        {filteredHosts.map(host => (
                            <div 
                                key={host.id}
                                className={`host-item ${selectedNode === host.id ? 'selected' : ''} ${searchQuery ? 'search-match' : ''}`}
                                onClick={() => onNodeSelect(host.id)}
                            >
                                <div className="host-ip">{host.label}</div>
                                <div className="host-ports">
                                    {host.ports && host.ports.map(port => (
                                        <span key={port} className="port-badge">{port}</span>
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
                <div className="legend">
                    <div className="legend-item">
                        <div className="legend-dot" style={{background: '#e94560'}}></div>
                        <span>Internet</span>
                    </div>
                    <div className="legend-item">
                        <div className="legend-dot" style={{background: '#ff6b35'}}></div>
                        <span>Class A (/8)</span>
                    </div>
                    <div className="legend-item">
                        <div className="legend-dot" style={{background: '#f7c548'}}></div>
                        <span>Class B (/16)</span>
                    </div>
                    <div className="legend-item">
                        <div className="legend-dot" style={{background: '#45b7aa'}}></div>
                        <span>Class C (/24)</span>
                    </div>
                    <div className="legend-item">
                        <div className="legend-dot" style={{background: '#4cc9f0'}}></div>
                        <span>Host</span>
                    </div>
                    <div className="legend-item">
                        <div className="legend-dot" style={{background: '#7209b7'}}></div>
                        <span>Open Port</span>
                    </div>
                </div>
            </aside>
        );
        };
        
        // Tooltip Component
        const Tooltip = ({ node, position }) => {
            if (!node) return null;
            
            return (
                <div className="tooltip" style={{ left: position.x + 15, top: position.y - 10 }}>
                    <div className="tooltip-title">{node.label}</div>
                    <div className="tooltip-row">
                        <span className="tooltip-label">Type:</span>
                        <span>{node.type}</span>
                    </div>
                    {node.type === 'host' && node.ports && (
                        <div className="tooltip-row">
                            <span className="tooltip-label">Ports:</span>
                            <span>{node.ports.join(', ')}</span>
                        </div>
                    )}
                    {node.type === 'port' && (
                        <div className="tooltip-row">
                            <span className="tooltip-label">Protocol:</span>
                            <span>{node.proto || 'tcp'}</span>
                        </div>
                    )}
                </div>
            );
        };
        
        // D3 Force Chart Component
        const ForceChart = ({ data, selectedNode, onNodeSelect, searchQuery }) => {
            const containerRef = React.useRef(null);
            const simulationRef = React.useRef(null);
            const [tooltip, setTooltip] = React.useState({ node: null, position: { x: 0, y: 0 } });
            
            React.useEffect(() => {
                if (!containerRef.current) return;
                
                // Clear previous chart
                d3.select(containerRef.current).selectAll('*').remove();
                
                const container = containerRef.current;
                const width = container.clientWidth;
                const height = container.clientHeight;
                
                // Create SVG
                const svg = d3.select(container)
                    .append('svg')
                    .attr('width', width)
                    .attr('height', height);
                
                // Add zoom behavior
                const g = svg.append('g');
                
                const zoom = d3.zoom()
                    .scaleExtent([0.1, 4])
                    .on('zoom', (event) => {
                        g.attr('transform', event.transform);
                    });
                
                svg.call(zoom);
                
                // Create arrow marker for links
                svg.append('defs').append('marker')
                    .attr('id', 'arrowhead')
                    .attr('viewBox', '-0 -5 10 10')
                    .attr('refX', 20)
                    .attr('refY', 0)
                    .attr('orient', 'auto')
                    .attr('markerWidth', 6)
                    .attr('markerHeight', 6)
                    .append('path')
                    .attr('d', 'M 0,-5 L 10,0 L 0,5')
                    .attr('fill', '#0f3460');
                
                // Color scale
                const getNodeColor = (node) => {
                    if (node.type === 'network') return '#e94560';
                    if (node.type === 'class_a') return '#ff6b35';
                    if (node.type === 'class_b') return '#f7c548';
                    if (node.type === 'class_c') return '#45b7aa';
                    if (node.type === 'port') return '#7209b7';
                    return '#4cc9f0';  // host
                };
                
                const getNodeRadius = (node) => {
                    if (node.type === 'network') return 30;
                    if (node.type === 'class_a') return 22;
                    if (node.type === 'class_b') return 18;
                    if (node.type === 'class_c') return 14;
                    if (node.type === 'port') return 8;
                    return 12;  // host
                };
                
                // Create simulation
                const simulation = d3.forceSimulation(data.nodes)
                    .force('link', d3.forceLink(data.links)
                        .id(d => d.id)
                        .distance(d => d.value === 1 ? 150 : 80))
                    .force('charge', d3.forceManyBody().strength(-300))
                    .force('center', d3.forceCenter(width / 2, height / 2))
                    .force('collision', d3.forceCollide().radius(30));
                
                simulationRef.current = simulation;
                
                // Create links
                const link = g.append('g')
                    .selectAll('line')
                    .data(data.links)
                    .join('line')
                    .attr('stroke', '#0f3460')
                    .attr('stroke-opacity', 0.6)
                    .attr('stroke-width', d => d.value);
                
                // Create nodes
                const node = g.append('g')
                    .selectAll('g')
                    .data(data.nodes)
                    .join('g')
                    .call(d3.drag()
                        .on('start', dragstarted)
                        .on('drag', dragged)
                        .on('end', dragended));
                
                // Add circles to nodes
                node.append('circle')
                    .attr('r', d => getNodeRadius(d))
                    .attr('fill', d => getNodeColor(d))
                    .attr('stroke', '#fff')
                    .attr('stroke-width', 1.5)
                    .style('cursor', 'pointer');
                
                // Add labels
                node.append('text')
                    .text(d => d.label)
                    .attr('x', d => getNodeRadius(d) + 5)
                    .attr('y', 4)
                    .attr('fill', '#aaa')
                    .attr('font-size', d => d.type === 'port' ? '10px' : '12px')
                    .style('pointer-events', 'none');
                
                // Add glow effect on hover
                node.on('mouseover', function(event, d) {
                    d3.select(this).select('circle')
                        .transition()
                        .duration(200)
                        .attr('r', getNodeRadius(d) * 1.3)
                        .attr('stroke-width', 3);
                    
                    setTooltip({ node: d, position: { x: event.pageX, y: event.pageY } });
                })
                .on('mousemove', function(event, d) {
                    setTooltip({ node: d, position: { x: event.pageX, y: event.pageY } });
                })
                .on('mouseout', function(event, d) {
                    d3.select(this).select('circle')
                        .transition()
                        .duration(200)
                        .attr('r', getNodeRadius(d))
                        .attr('stroke-width', 1.5);
                    
                    setTooltip({ node: null, position: { x: 0, y: 0 } });
                })
                .on('click', function(event, d) {
                    onNodeSelect(d.id);
                });
                
                // Simulation tick
                simulation.on('tick', () => {
                    link
                        .attr('x1', d => d.source.x)
                        .attr('y1', d => d.source.y)
                        .attr('x2', d => d.target.x)
                        .attr('y2', d => d.target.y);
                    
                    node.attr('transform', d => `translate(${d.x},${d.y})`);
                });
                
                // Drag functions
                function dragstarted(event, d) {
                    if (!event.active) simulation.alphaTarget(0.3).restart();
                    d.fx = d.x;
                    d.fy = d.y;
                }
                
                function dragged(event, d) {
                    d.fx = event.x;
                    d.fy = event.y;
                }
                
                function dragended(event, d) {
                    if (!event.active) simulation.alphaTarget(0);
                    d.fx = null;
                    d.fy = null;
                }
                
                // Center zoom initially
                svg.call(zoom.transform, d3.zoomIdentity.translate(0, 0).scale(0.9));
                
                // Cleanup
                return () => {
                    simulation.stop();
                };
            }, [data]);
            
            // Effect to highlight selected node and its children
            React.useEffect(() => {
                if (!containerRef.current) return;
                
                const svg = d3.select(containerRef.current).select('svg');
                const nodes = svg.selectAll('g g g');
                const links = svg.selectAll('g g line');
                
                if (!selectedNode) {
                    // Reset all nodes to normal state
                    nodes.select('circle')
                        .transition()
                        .duration(300)
                        .attr('opacity', 1)
                        .attr('stroke', '#fff')
                        .attr('stroke-width', 1.5);
                    nodes.select('text')
                        .transition()
                        .duration(300)
                        .attr('opacity', 1);
                    links.transition()
                        .duration(300)
                        .attr('opacity', 0.6);
                } else {
                    // Find child node IDs (ports connected to the selected host)
                    const childIds = new Set();
                    graphData.links.forEach(link => {
                        const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
                        const targetId = typeof link.target === 'object' ? link.target.id : link.target;
                        if (sourceId === selectedNode) {
                            childIds.add(targetId);
                        }
                    });
                    
                    // Highlight selected node and children, dim others
                    nodes.each(function(d) {
                        const isSelected = d.id === selectedNode;
                        const isChild = childIds.has(d.id);
                        const isHighlighted = isSelected || isChild;
                        
                        d3.select(this).select('circle')
                            .transition()
                            .duration(300)
                            .attr('opacity', isHighlighted ? 1 : 0.2)
                            .attr('stroke', isSelected ? '#ffff00' : (isChild ? '#ffcc00' : '#fff'))
                            .attr('stroke-width', isHighlighted ? 3 : 1.5);
                        
                        d3.select(this).select('text')
                            .transition()
                            .duration(300)
                            .attr('opacity', isHighlighted ? 1 : 0.2)
                            .attr('fill', isHighlighted ? '#fff' : '#aaa');
                    });
                    
                    // Highlight links connected to selected node
                    links.transition()
                        .duration(300)
                        .attr('opacity', d => {
                            const sourceId = typeof d.source === 'object' ? d.source.id : d.source;
                            const targetId = typeof d.target === 'object' ? d.target.id : d.target;
                            return (sourceId === selectedNode || targetId === selectedNode) ? 1 : 0.1;
                        })
                        .attr('stroke', d => {
                            const sourceId = typeof d.source === 'object' ? d.source.id : d.source;
                            const targetId = typeof d.target === 'object' ? d.target.id : d.target;
                            return (sourceId === selectedNode || targetId === selectedNode) ? '#ffcc00' : '#0f3460';
                        });
                }
            }, [selectedNode]);
            
            // Effect to highlight search matches
            React.useEffect(() => {
                if (!containerRef.current) return;
                if (selectedNode) return;  // Don't override selection highlighting
                
                const svg = d3.select(containerRef.current).select('svg');
                const nodes = svg.selectAll('g g g');
                const links = svg.selectAll('g g line');
                
                if (!searchQuery) {
                    // Reset all nodes to normal state
                    nodes.select('circle')
                        .transition()
                        .duration(300)
                        .attr('opacity', 1)
                        .attr('stroke', '#fff')
                        .attr('stroke-width', 1.5);
                    nodes.select('text')
                        .transition()
                        .duration(300)
                        .attr('opacity', 1)
                        .attr('fill', '#aaa');
                    links.transition()
                        .duration(300)
                        .attr('opacity', 0.6)
                        .attr('stroke', '#0f3460');
                } else {
                    const query = searchQuery.toLowerCase();
                    const isPortSearch = query.startsWith(':');
                    const portQuery = isPortSearch ? query.slice(1) : query;
                    
                    // Port matching helper - supports wildcards
                    const matchPort = (port, pattern) => {
                        const portStr = port.toString();
                        const hasLeadingWildcard = pattern.startsWith('*');
                        const hasTrailingWildcard = pattern.endsWith('*');
                        let cleanPattern = pattern.replace(/^\*|\*$/g, '');
                        
                        if (!cleanPattern) return false;
                        
                        if (hasLeadingWildcard && hasTrailingWildcard) {
                            // *443* - contains
                            return portStr.includes(cleanPattern);
                        } else if (hasLeadingWildcard) {
                            // *443 - ends with
                            return portStr.endsWith(cleanPattern);
                        } else if (hasTrailingWildcard) {
                            // 443* - starts with
                            return portStr.startsWith(cleanPattern);
                        } else {
                            // 443 - exact match
                            return portStr === cleanPattern;
                        }
                    };
                    
                    // Find matching node IDs
                    const matchingIds = new Set();
                    const matchingHostIds = new Set();
                    
                    data.nodes.forEach(node => {
                        if (isPortSearch) {
                            // Port-only search mode with exact/wildcard matching
                            if (node.type === 'port') {
                                if (node.port && matchPort(node.port, portQuery)) {
                                    matchingIds.add(node.id);
                                    // Also find the parent host
                                    if (node.host) {
                                        matchingIds.add(node.host);
                                    }
                                }
                            }
                        } else {
                            // Normal search - match all node types
                            // Match Class A, B, C network nodes
                            if (node.type === 'class_a' || node.type === 'class_b' || node.type === 'class_c') {
                                if (node.label.toLowerCase().includes(query)) {
                                    matchingIds.add(node.id);
                                }
                            } else if (node.type === 'host') {
                                const matchesIP = node.label.toLowerCase().includes(query);
                                const matchesPort = node.ports && node.ports.some(p => p.toString().includes(query));
                                if (matchesIP || matchesPort) {
                                    matchingIds.add(node.id);
                                    matchingHostIds.add(node.id);
                                }
                            } else if (node.type === 'port') {
                                if (node.port && node.port.toString().includes(query)) {
                                    matchingIds.add(node.id);
                                }
                            } else if (node.type === 'network') {
                                if (node.label.toLowerCase().includes(query)) {
                                    matchingIds.add(node.id);
                                }
                            }
                        }
                    });
                    
                    // Also highlight ports of matching hosts
                    data.links.forEach(link => {
                        const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
                        const targetId = typeof link.target === 'object' ? link.target.id : link.target;
                        if (matchingHostIds.has(sourceId)) {
                            matchingIds.add(targetId);
                        }
                    });
                    
                    // Highlight matching nodes, dim others
                    nodes.each(function(d) {
                        const isMatch = matchingIds.has(d.id);
                        
                        d3.select(this).select('circle')
                            .transition()
                            .duration(300)
                            .attr('opacity', isMatch ? 1 : 0.15)
                            .attr('stroke', isMatch ? '#f7c548' : '#fff')
                            .attr('stroke-width', isMatch ? 3 : 1.5);
                        
                        d3.select(this).select('text')
                            .transition()
                            .duration(300)
                            .attr('opacity', isMatch ? 1 : 0.15)
                            .attr('fill', isMatch ? '#fff' : '#aaa');
                    });
                    
                    // Highlight links connected to matching nodes
                    links.transition()
                        .duration(300)
                        .attr('opacity', d => {
                            const sourceId = typeof d.source === 'object' ? d.source.id : d.source;
                            const targetId = typeof d.target === 'object' ? d.target.id : d.target;
                            return (matchingIds.has(sourceId) && matchingIds.has(targetId)) ? 1 : 0.08;
                        })
                        .attr('stroke', d => {
                            const sourceId = typeof d.source === 'object' ? d.source.id : d.source;
                            const targetId = typeof d.target === 'object' ? d.target.id : d.target;
                            return (matchingIds.has(sourceId) && matchingIds.has(targetId)) ? '#f7c548' : '#0f3460';
                        });
                }
            }, [searchQuery, selectedNode]);
            
            const resetZoom = () => {
                const svg = d3.select(containerRef.current).select('svg');
                svg.transition().duration(500).call(
                    d3.zoom().transform,
                    d3.zoomIdentity.translate(0, 0).scale(0.9)
                );
            };
            
            const reheat = () => {
                if (simulationRef.current) {
                    simulationRef.current.alpha(1).restart();
                }
            };
            
            const generatePDF = async () => {
                const { jsPDF } = window.jspdf;
                const pdf = new jsPDF('p', 'mm', 'a4');
                const pageWidth = pdf.internal.pageSize.getWidth();
                const pageHeight = pdf.internal.pageSize.getHeight();
                const margin = 20;
                const contentWidth = pageWidth - (margin * 2);
                
                // Helper to add new page if needed - includes background color
                let yPos = margin;
                const checkNewPage = (neededSpace) => {
                    if (yPos + neededSpace > pageHeight - margin) {
                        pdf.addPage();
                        pdf.setFillColor(26, 26, 46);
                        pdf.rect(0, 0, pageWidth, pageHeight, 'F');
                        yPos = margin;
                        return true;
                    }
                    return false;
                };
                
                // ========== TITLE PAGE ==========
                pdf.setFillColor(26, 26, 46);
                pdf.rect(0, 0, pageWidth, pageHeight, 'F');
                
                // Title
                pdf.setTextColor(233, 69, 96);
                pdf.setFontSize(32);
                pdf.setFont('helvetica', 'bold');
                pdf.text('Network Scan Report', pageWidth / 2, 80, { align: 'center' });
                
                // Subtitle
                pdf.setTextColor(200, 200, 200);
                pdf.setFontSize(14);
                pdf.setFont('helvetica', 'normal');
                pdf.text('Force-Directed Network Visualization', pageWidth / 2, 95, { align: 'center' });
                
                // Date
                pdf.setFontSize(12);
                pdf.text('Generated: ''' + datetime.now().strftime('%Y-%m-%d %H:%M') + '''', pageWidth / 2, 110, { align: 'center' });
                
                // Stats box
                pdf.setDrawColor(15, 52, 96);
                pdf.setFillColor(22, 33, 62);
                pdf.roundedRect(margin + 20, 130, contentWidth - 40, 40, 3, 3, 'FD');
                
                const hosts = data.nodes.filter(n => n.type === 'host');
                const ports = data.nodes.filter(n => n.type === 'port');
                const networks = data.nodes.filter(n => n.type === 'class_c');
                
                pdf.setTextColor(76, 201, 240);
                pdf.setFontSize(11);
                pdf.text(`Hosts Discovered: ${hosts.length}`, pageWidth / 2 - 50, 145, { align: 'left' });
                pdf.text(`Open Ports: ${ports.length}`, pageWidth / 2 - 50, 155, { align: 'left' });
                pdf.text(`Networks: ${networks.length}`, pageWidth / 2 - 50, 165, { align: 'left' });
                
                // ========== GRAPH SCREENSHOT PAGE ==========
                pdf.addPage();
                pdf.setFillColor(26, 26, 46);
                pdf.rect(0, 0, pageWidth, pageHeight, 'F');
                
                yPos = margin;
                pdf.setTextColor(233, 69, 96);
                pdf.setFontSize(18);
                pdf.setFont('helvetica', 'bold');
                pdf.text('Network Topology', margin, yPos);
                yPos += 10;
                
                // Capture the chart
                try {
                    const chartContainer = document.getElementById('chart-container');
                    const canvas = await html2canvas(chartContainer, {
                        backgroundColor: '#1a1a2e',
                        scale: 2
                    });
                    const imgData = canvas.toDataURL('image/png');
                    const imgWidth = contentWidth;
                    const imgHeight = (canvas.height * imgWidth) / canvas.width;
                    pdf.addImage(imgData, 'PNG', margin, yPos, imgWidth, Math.min(imgHeight, pageHeight - yPos - margin));
                } catch (e) {
                    pdf.setTextColor(150, 150, 150);
                    pdf.setFontSize(10);
                    pdf.text('Graph screenshot could not be captured', margin, yPos + 20);
                }
                
                // ========== SUMMARY PAGE ==========
                pdf.addPage();
                pdf.setFillColor(26, 26, 46);
                pdf.rect(0, 0, pageWidth, pageHeight, 'F');
                
                yPos = margin;
                pdf.setTextColor(233, 69, 96);
                pdf.setFontSize(18);
                pdf.setFont('helvetica', 'bold');
                pdf.text('Executive Summary', margin, yPos);
                yPos += 15;
                
                // Summary content - Natural language
                pdf.setTextColor(200, 200, 200);
                pdf.setFontSize(10);
                pdf.setFont('helvetica', 'normal');
                
                const uniquePorts = [...new Set(ports.map(p => p.port))].sort((a, b) => a - b);
                const classANetworks = data.nodes.filter(n => n.type === 'class_a');
                const classBNetworks = data.nodes.filter(n => n.type === 'class_b');
                const classCNetworks = data.nodes.filter(n => n.type === 'class_c');
                
                // Count high-risk ports
                const highRiskPorts = uniquePorts.filter(p => {
                    const info = portDescriptions[p.toString()];
                    return info && info.security && info.security.toLowerCase().includes('high');
                });
                
                // Count common service ports
                const webPorts = uniquePorts.filter(p => [80, 443, 8080, 8443].includes(p));
                const sshPorts = uniquePorts.filter(p => p === 22);
                const dbPorts = uniquePorts.filter(p => [3306, 5432, 1433, 27017, 6379].includes(p));
                
                // Build natural language paragraphs
                const para1 = `This network scan identified ${hosts.length} active host${hosts.length !== 1 ? 's' : ''} across ${classCNetworks.length} Class C network${classCNetworks.length !== 1 ? 's' : ''}. The scan discovered a total of ${ports.length} open port instance${ports.length !== 1 ? 's' : ''}, representing ${uniquePorts.length} unique service${uniquePorts.length !== 1 ? 's' : ''} running across the infrastructure.`;
                
                const splitPara1 = pdf.splitTextToSize(para1, contentWidth);
                pdf.text(splitPara1, margin, yPos);
                yPos += splitPara1.length * 5 + 8;
                
                // Network topology paragraph
                const para2 = `The network topology spans ${classANetworks.length} Class A (/8) network${classANetworks.length !== 1 ? 's' : ''}, subdivided into ${classBNetworks.length} Class B (/16) segment${classBNetworks.length !== 1 ? 's' : ''} and ${classCNetworks.length} Class C (/24) subnet${classCNetworks.length !== 1 ? 's' : ''}. This hierarchical structure indicates ${classCNetworks.length > 5 ? 'a distributed network environment with multiple segments' : classCNetworks.length > 1 ? 'a moderately segmented network' : 'a consolidated network segment'}.`;
                
                const splitPara2 = pdf.splitTextToSize(para2, contentWidth);
                pdf.text(splitPara2, margin, yPos);
                yPos += splitPara2.length * 5 + 8;
                
                // Services paragraph
                let para3 = 'The discovered services include ';
                const serviceTypes = [];
                if (webPorts.length > 0) serviceTypes.push(`${webPorts.length} web server${webPorts.length !== 1 ? 's' : ''} (HTTP/HTTPS)`);
                if (sshPorts.length > 0) serviceTypes.push('SSH remote access');
                if (dbPorts.length > 0) serviceTypes.push(`${dbPorts.length} database service${dbPorts.length !== 1 ? 's' : ''}`);
                if (serviceTypes.length > 0) {
                    para3 += serviceTypes.join(', ') + '. ';
                } else {
                    para3 = 'Various network services were detected. ';
                }
                
                if (highRiskPorts.length > 0) {
                    para3 += `Security analysis identified ${highRiskPorts.length} potentially high-risk service${highRiskPorts.length !== 1 ? 's' : ''} that may require additional review or hardening.`;
                } else {
                    para3 += 'No services were flagged as high-risk based on the port analysis.';
                }
                
                const splitPara3 = pdf.splitTextToSize(para3, contentWidth);
                pdf.text(splitPara3, margin, yPos);
                yPos += splitPara3.length * 5 + 15;
                
                // Key findings section
                pdf.setTextColor(114, 9, 183);
                pdf.setFontSize(12);
                pdf.setFont('helvetica', 'bold');
                pdf.text('Key Findings', margin, yPos); yPos += 8;
                
                pdf.setTextColor(200, 200, 200);
                pdf.setFontSize(10);
                pdf.setFont('helvetica', 'normal');
                
                // Calculate average ports per host
                const avgPortsPerHost = (ports.length / hosts.length).toFixed(1);
                
                const findings = [
                    `• Average of ${avgPortsPerHost} open ports per host`,
                    `• Most common ports: ${uniquePorts.slice(0, 5).map(p => ':' + p).join(', ')}${uniquePorts.length > 5 ? ' and ' + (uniquePorts.length - 5) + ' others' : ''}`,
                    `• ${highRiskPorts.length > 0 ? highRiskPorts.length + ' high-risk service(s) detected requiring attention' : 'No high-risk services detected'}`,
                    `• Network spans ${classCNetworks.length} subnet${classCNetworks.length !== 1 ? 's' : ''} indicating ${classCNetworks.length > 3 ? 'distributed' : 'centralized'} infrastructure`
                ];
                
                findings.forEach(finding => {
                    const splitFinding = pdf.splitTextToSize(finding, contentWidth - 5);
                    pdf.text(splitFinding, margin, yPos);
                    yPos += splitFinding.length * 5 + 2;
                });
                yPos += 10;
                
                // Ports discovered section
                pdf.setTextColor(114, 9, 183);
                pdf.setFontSize(12);
                pdf.setFont('helvetica', 'bold');
                pdf.text('Ports Discovered', margin, yPos); yPos += 8;
                
                pdf.setTextColor(200, 200, 200);
                pdf.setFontSize(9);
                pdf.setFont('helvetica', 'normal');
                const portsText = uniquePorts.join(', ');
                const splitPorts = pdf.splitTextToSize(portsText, contentWidth);
                pdf.text(splitPorts, margin, yPos);
                yPos += splitPorts.length * 5 + 10;
                
                // ========== HOST DETAILS BY NETWORK ==========
                pdf.addPage();
                pdf.setFillColor(26, 26, 46);
                pdf.rect(0, 0, pageWidth, pageHeight, 'F');
                
                yPos = margin;
                pdf.setTextColor(233, 69, 96);
                pdf.setFontSize(18);
                pdf.setFont('helvetica', 'bold');
                pdf.text('Host Details by Network', margin, yPos);
                yPos += 15;
                
                // Group hosts by Class C network
                const hostsByNetwork = {};
                hosts.forEach(host => {
                    const octets = host.id.split('.');
                    const classC = `${octets[0]}.${octets[1]}.${octets[2]}.0/24`;
                    if (!hostsByNetwork[classC]) {
                        hostsByNetwork[classC] = [];
                    }
                    hostsByNetwork[classC].push(host);
                });
                
                // Sort networks
                const sortedNetworks = Object.keys(hostsByNetwork).sort();
                
                for (const network of sortedNetworks) {
                    checkNewPage(25);
                    
                    // Network header
                    pdf.setFillColor(22, 33, 62);
                    pdf.roundedRect(margin, yPos - 4, contentWidth, 10, 2, 2, 'F');
                    pdf.setTextColor(69, 183, 170);
                    pdf.setFontSize(11);
                    pdf.setFont('helvetica', 'bold');
                    pdf.text(`Network: ${network}`, margin + 3, yPos + 3);
                    yPos += 12;
                    
                    const networkHosts = hostsByNetwork[network].sort((a, b) => {
                        const aNum = parseInt(a.id.split('.')[3]);
                        const bNum = parseInt(b.id.split('.')[3]);
                        return aNum - bNum;
                    });
                    
                    for (const host of networkHosts) {
                        const hostPorts = host.ports || [];
                        const neededSpace = 12 + (hostPorts.length * 5);
                        checkNewPage(neededSpace);
                        
                        // Host IP
                        pdf.setTextColor(76, 201, 240);
                        pdf.setFontSize(10);
                        pdf.setFont('helvetica', 'bold');
                        pdf.text(host.id, margin + 5, yPos);
                        yPos += 6;
                        
                        // Ports
                        if (hostPorts.length > 0) {
                            for (const port of hostPorts) {
                                checkNewPage(6);
                                const portInfo = portDescriptions[port.toString()] || { description: 'Unknown' };
                                
                                pdf.setTextColor(114, 9, 183);
                                pdf.setFontSize(9);
                                pdf.setFont('helvetica', 'bold');
                                pdf.text(`:${port}`, margin + 10, yPos);
                                
                                pdf.setTextColor(170, 170, 170);
                                pdf.setFont('helvetica', 'normal');
                                pdf.text(`- ${portInfo.description}`, margin + 25, yPos);
                                
                                // Security indicator
                                if (portInfo.security) {
                                    const secText = portInfo.security.split(' ')[0];
                                    if (secText.includes('HIGH')) {
                                        pdf.setTextColor(233, 69, 96);
                                    } else if (secText.includes('MEDIUM')) {
                                        pdf.setTextColor(247, 197, 72);
                                    } else if (secText.includes('SECURE')) {
                                        pdf.setTextColor(76, 201, 240);
                                    } else {
                                        pdf.setTextColor(69, 183, 170);
                                    }
                                    pdf.setFontSize(7);
                                    pdf.text(`[${secText}]`, margin + 120, yPos);
                                }
                                yPos += 5;
                            }
                        } else {
                            pdf.setTextColor(100, 100, 100);
                            pdf.setFontSize(8);
                            pdf.text('No ports discovered', margin + 10, yPos);
                            yPos += 5;
                        }
                        yPos += 3;
                    }
                    yPos += 5;
                }
                
                // Save the PDF
                pdf.save('network-scan-report.pdf');
            };
            
            return (
                <div className="main-content">
                    <div className="controls">
                        <button className="control-btn" onClick={resetZoom}>🔄 Reset View</button>
                        <button className="control-btn" onClick={reheat}>⚡ Reheat</button>
                        <button className="control-btn" onClick={generatePDF}>📄 Export PDF</button>
                    </div>
                    <div id="chart-container" ref={containerRef}></div>
                    <Tooltip node={tooltip.node} position={tooltip.position} />
                </div>
            );
        };
        
        // Main App Component
        const App = () => {
            const [selectedNode, setSelectedNode] = React.useState(null);
            const [modalNode, setModalNode] = React.useState(null);
            const [searchQuery, setSearchQuery] = React.useState('');
            
            // Handle sidebar selection - just highlight, no modal
            const handleSidebarSelect = (nodeId) => {
                setSelectedNode(nodeId);
                setModalNode(null);  // Close any open modal
            };
            
            // Handle graph node click - show modal
            const handleGraphNodeClick = (nodeId) => {
                setSelectedNode(nodeId);
                const node = graphData.nodes.find(n => n.id === nodeId);
                if (node) {
                    setModalNode(node);
                }
            };
            
            // Close modal
            const handleCloseModal = () => {
                setModalNode(null);
            };
            
            // Clear selection when searching
            const handleSearchChange = (query) => {
                setSearchQuery(query);
                if (query) {
                    setSelectedNode(null);
                    setModalNode(null);
                }
            };
            
            const hosts = graphData.nodes.filter(n => n.type === 'host');
            
            return (
                <div className="app-container">
                    <Header 
                        nodeCount={graphData.nodes.length} 
                        linkCount={graphData.links.length} 
                    />
                    <div className="main-layout">
                        <Sidebar 
                            hosts={hosts}
                            selectedNode={selectedNode}
                            onNodeSelect={handleSidebarSelect}
                            searchQuery={searchQuery}
                            onSearchChange={handleSearchChange}
                        />
                        <ForceChart 
                            data={graphData}
                            selectedNode={selectedNode}
                            onNodeSelect={handleGraphNodeClick}
                            searchQuery={searchQuery}
                        />
                    </div>
                    <Modal node={modalNode} onClose={handleCloseModal} />
                </div>
            );
        };
        
        // Render the app
        const root = ReactDOM.createRoot(document.getElementById('root'));
        root.render(<App />);
    </script>
</body>
</html>
'''
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return output_file

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate network scan visualization')
    parser.add_argument('input', nargs='?', default='scans/home.json', 
                        help='Input JSON file from masscan (default: scans/home.json)')
    parser.add_argument('-o', '--output', default='report.html',
                        help='Output HTML file (default: report.html)')
    
    args = parser.parse_args()
    
    # Get script directory for relative paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Handle relative paths
    input_file = args.input
    if not os.path.isabs(input_file):
        input_file = os.path.join(script_dir, input_file)
    
    output_file = args.output
    if not os.path.isabs(output_file):
        output_file = os.path.join(script_dir, output_file)
    
    print(f"📁 Loading scan data from: {input_file}")
    scan_data = load_scan_data(input_file)
    
    print(f"🔄 Transforming data to graph format...")
    graph_data = transform_to_graph_data(scan_data)
    
    print(f"📊 Nodes: {len(graph_data['nodes'])}, Links: {len(graph_data['links'])}")
    
    print(f"📝 Generating HTML report: {output_file}")
    generate_html(graph_data, output_file)
    
    print(f"✅ Report generated successfully!")
    print(f"🌐 Open {output_file} in your browser to view the visualization.")

if __name__ == '__main__':
    main()
