#!/usr/bin/env python3
"""
All Three API Servers - REST, SOAP, and JSON-RPC
Demonstrates three different API architectural styles
"""

from flask import Flask, request, jsonify
import threading
import json
from werkzeug.serving import make_server

# ============================================================
# REST API SERVER (Port 5000)
# ============================================================
rest_app = Flask('REST_API')

@rest_app.route('/')
def rest_home():
    return jsonify({
        "message": "REST API Server",
        "endpoints": [
            {"method": "POST", "path": "/add", "description": "Add two numbers"},
            {"method": "POST", "path": "/multiply", "description": "Multiply two numbers"}
        ]
    })

@rest_app.route('/add', methods=['POST'])
def rest_add():
    data = request.get_json()
    if 'a' not in data or 'b' not in data:
        return jsonify({"error": "Missing parameters 'a' or 'b'"}), 400
    result = data['a'] + data['b']
    return jsonify({"result": result})

@rest_app.route('/multiply', methods=['POST'])
def rest_multiply():
    data = request.get_json()
    if 'a' not in data or 'b' not in data:
        return jsonify({"error": "Missing parameters 'a' or 'b'"}), 400
    result = data['a'] * data['b']
    return jsonify({"result": result})

# ============================================================
# SOAP API SERVER (Port 5001)
# ============================================================
soap_app = Flask('SOAP_API')

WSDL_TEMPLATE = '''<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://schemas.xmlsoap.org/wsdl/"
             xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
             xmlns:tns="http://calculator.example.com/"
             xmlns:xsd="http://www.w3.org/2001/XMLSchema"
             targetNamespace="http://calculator.example.com/"
             name="CalculatorService">
    
    <types>
        <xsd:schema targetNamespace="http://calculator.example.com/">
            <xsd:element name="add">
                <xsd:complexType>
                    <xsd:sequence>
                        <xsd:element name="a" type="xsd:int"/>
                        <xsd:element name="b" type="xsd:int"/>
                    </xsd:sequence>
                </xsd:complexType>
            </xsd:element>
            <xsd:element name="addResponse">
                <xsd:complexType>
                    <xsd:sequence>
                        <xsd:element name="result" type="xsd:int"/>
                    </xsd:sequence>
                </xsd:complexType>
            </xsd:element>
            <xsd:element name="multiply">
                <xsd:complexType>
                    <xsd:sequence>
                        <xsd:element name="a" type="xsd:int"/>
                        <xsd:element name="b" type="xsd:int"/>
                    </xsd:sequence>
                </xsd:complexType>
            </xsd:element>
            <xsd:element name="multiplyResponse">
                <xsd:complexType>
                    <xsd:sequence>
                        <xsd:element name="result" type="xsd:int"/>
                    </xsd:sequence>
                </xsd:complexType>
            </xsd:element>
        </xsd:schema>
    </types>
    
    <message name="addRequest">
        <part name="parameters" element="tns:add"/>
    </message>
    <message name="addResponse">
        <part name="parameters" element="tns:addResponse"/>
    </message>
    <message name="multiplyRequest">
        <part name="parameters" element="tns:multiply"/>
    </message>
    <message name="multiplyResponse">
        <part name="parameters" element="tns:multiplyResponse"/>
    </message>
    
    <portType name="CalculatorPortType">
        <operation name="add">
            <input message="tns:addRequest"/>
            <output message="tns:addResponse"/>
        </operation>
        <operation name="multiply">
            <input message="tns:multiplyRequest"/>
            <output message="tns:multiplyResponse"/>
        </operation>
    </portType>
    
    <binding name="CalculatorBinding" type="tns:CalculatorPortType">
        <soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>
        <operation name="add">
            <soap:operation soapAction="add"/>
            <input><soap:body use="literal"/></input>
            <output><soap:body use="literal"/></output>
        </operation>
        <operation name="multiply">
            <soap:operation soapAction="multiply"/>
            <input><soap:body use="literal"/></input>
            <output><soap:body use="literal"/></output>
        </operation>
    </binding>
    
    <service name="CalculatorService">
        <port name="CalculatorPort" binding="tns:CalculatorBinding">
            <soap:address location="http://localhost:5001/"/>
        </port>
    </service>
</definitions>'''

@soap_app.route('/', methods=['GET', 'POST'])
def soap_endpoint():
    if request.method == 'GET' and 'wsdl' in request.args:
        return WSDL_TEMPLATE, 200, {'Content-Type': 'text/xml'}
    
    if request.method == 'POST':
        xml_data = request.data.decode('utf-8')
        
        try:
            # Simple XML parsing for add operation
            if '<calc:add>' in xml_data or '<add>' in xml_data:
                # Extract numbers
                a_start = xml_data.find('<calc:a>') if '<calc:a>' in xml_data else xml_data.find('<a>')
                b_start = xml_data.find('<calc:b>') if '<calc:b>' in xml_data else xml_data.find('<b>')
                
                if a_start != -1 and b_start != -1:
                    a_end = xml_data.find('</calc:a>') if '</calc:a>' in xml_data else xml_data.find('</a>')
                    b_end = xml_data.find('</calc:b>') if '</calc:b>' in xml_data else xml_data.find('</b>')
                    
                    a_val = int(xml_data[a_start:a_end].split('>')[-1])
                    b_val = int(xml_data[b_start:b_end].split('>')[-1])
                    result = a_val + b_val
                    
                    response = f'''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:calc="http://calculator.example.com/">
    <soap:Body>
        <calc:addResponse>
            <calc:result>{result}</calc:result>
        </calc:addResponse>
    </soap:Body>
</soap:Envelope>'''
                    return response, 200, {'Content-Type': 'text/xml'}
            
            # Simple XML parsing for multiply operation
            elif '<calc:multiply>' in xml_data or '<multiply>' in xml_data:
                a_start = xml_data.find('<calc:a>') if '<calc:a>' in xml_data else xml_data.find('<a>')
                b_start = xml_data.find('<calc:b>') if '<calc:b>' in xml_data else xml_data.find('<b>')
                
                if a_start != -1 and b_start != -1:
                    a_end = xml_data.find('</calc:a>') if '</calc:a>' in xml_data else xml_data.find('</a>')
                    b_end = xml_data.find('</calc:b>') if '</calc:b>' in xml_data else xml_data.find('</b>')
                    
                    a_val = int(xml_data[a_start:a_end].split('>')[-1])
                    b_val = int(xml_data[b_start:b_end].split('>')[-1])
                    result = a_val * b_val
                    
                    response = f'''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:calc="http://calculator.example.com/">
    <soap:Body>
        <calc:multiplyResponse>
            <calc:result>{result}</calc:result>
        </calc:multiplyResponse>
    </soap:Body>
</soap:Envelope>'''
                    return response, 200, {'Content-Type': 'text/xml'}
            
            # Error response
            error_response = '''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <soap:Fault>
            <faultcode>soap:Server</faultcode>
            <faultstring>Invalid SOAP request or operation not found</faultstring>
        </soap:Fault>
    </soap:Body>
</soap:Envelope>'''
            return error_response, 400, {'Content-Type': 'text/xml'}
            
        except Exception as e:
            error_response = f'''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <soap:Fault>
            <faultcode>soap:Server</faultcode>
            <faultstring>Error processing request: {str(e)}</faultstring>
        </soap:Fault>
    </soap:Body>
</soap:Envelope>'''
            return error_response, 500, {'Content-Type': 'text/xml'}
    
    return "SOAP API - Add ?wsdl to see the service description", 200

# ============================================================
# JSON-RPC API SERVER (Port 5002)
# ============================================================
jsonrpc_app = Flask('JSONRPC_API')

@jsonrpc_app.route('/', methods=['GET', 'POST'])
def jsonrpc_endpoint():
    if request.method == 'GET':
        return '''
        <html>
        <head><title>JSON-RPC API</title></head>
        <body>
            <h1>JSON-RPC 2.0 API</h1>
            <p>This API uses JSON-RPC 2.0 protocol.</p>
            <h2>Available Methods:</h2>
            <ul>
                <li><strong>add</strong> - Add two numbers</li>
                <li><strong>multiply</strong> - Multiply two numbers</li>
            </ul>
            <h2>Request Format:</h2>
            <pre>
{
    "jsonrpc": "2.0",
    "method": "add",
    "params": [10, 5],
    "id": 1
}
            </pre>
            <h2>Response Format:</h2>
            <pre>
{
    "jsonrpc": "2.0",
    "result": 15,
    "id": 1
}
            </pre>
        </body>
        </html>
        ''', 200, {'Content-Type': 'text/html'}
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            if 'jsonrpc' not in data or data['jsonrpc'] != '2.0':
                return jsonify({
                    "jsonrpc": "2.0",
                    "error": {"code": -32600, "message": "Invalid Request - jsonrpc version must be 2.0"},
                    "id": data.get('id', None)
                }), 400
            
            method = data.get('method')
            params = data.get('params', [])
            request_id = data.get('id', None)
            
            if method == 'add':
                if len(params) < 2:
                    return jsonify({
                        "jsonrpc": "2.0",
                        "error": {"code": -32602, "message": "Invalid params - need two numbers"},
                        "id": request_id
                    }), 400
                result = params[0] + params[1]
                return jsonify({"jsonrpc": "2.0", "result": result, "id": request_id})
            
            elif method == 'multiply':
                if len(params) < 2:
                    return jsonify({
                        "jsonrpc": "2.0",
                        "error": {"code": -32602, "message": "Invalid params - need two numbers"},
                        "id": request_id
                    }), 400
                result = params[0] * params[1]
                return jsonify({"jsonrpc": "2.0", "result": result, "id": request_id})
            
            else:
                return jsonify({
                    "jsonrpc": "2.0",
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                    "id": request_id
                }), 404
                
        except Exception as e:
            return jsonify({
                "jsonrpc": "2.0",
                "error": {"code": -32700, "message": f"Parse error: {str(e)}"},
                "id": None
            }), 400

# ============================================================
# SERVER MANAGEMENT
# ============================================================
class ServerThread(threading.Thread):
    def __init__(self, app, port):
        threading.Thread.__init__(self)
        self.server = make_server('localhost', port, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()

def main():
    print("=" * 60)
    print("Starting All Three API Servers...")
    print("=" * 60)
    print()
    print("1. REST API:     http://localhost:5000")
    print("2. SOAP API:     http://localhost:5001")
    print("3. JSON-RPC API: http://localhost:5002")
    print()
    print("Press Ctrl+C to stop all servers")
    print()
    print("=" * 60)
    
    # Start all servers
    rest_server = ServerThread(rest_app, 5000)
    soap_server = ServerThread(soap_app, 5001)
    jsonrpc_server = ServerThread(jsonrpc_app, 5002)
    
    rest_server.daemon = True
    soap_server.daemon = True
    jsonrpc_server.daemon = True
    
    rest_server.start()
    soap_server.start()
    jsonrpc_server.start()
    
    try:
        # Keep main thread alive
        while True:
            pass
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        rest_server.shutdown()
        soap_server.shutdown()
        jsonrpc_server.shutdown()
        print("All servers stopped.")

if __name__ == '__main__':
    main()
