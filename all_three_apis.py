{\rtf1\ansi\ansicpg1252\cocoartf2865
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural\partightenfactor0

\f0\fs24 \cf0 #!/usr/bin/env python3\
"""\
Simple API Demo - REST, SOAP, and RPC\
All three APIs provide add() and multiply() operations\
Run this file and all three servers start simultaneously\
"""\
\
from flask import Flask, request, jsonify, Response\
import threading\
import json\
from http.server import BaseHTTPRequestHandler, HTTPServer\
\
# =============================================================================\
# 1. REST API (Flask) - Port 5000\
# =============================================================================\
rest_app = Flask(__name__)\
\
@rest_app.route('/')\
def rest_home():\
    return jsonify(\{\
        'message': 'REST API Server',\
        'endpoints': \{\
            'add': 'POST /add with JSON body: \{"a": 5, "b": 3\}',\
            'multiply': 'POST /multiply with JSON body: \{"a": 5, "b": 3\}'\
        \}\
    \})\
\
@rest_app.route('/add', methods=['POST'])\
def rest_add():\
    data = request.get_json()\
    result = data['a'] + data['b']\
    return jsonify(\{'result': result\})\
\
@rest_app.route('/multiply', methods=['POST'])\
def rest_multiply():\
    data = request.get_json()\
    result = data['a'] * data['b']\
    return jsonify(\{'result': result\})\
\
# =============================================================================\
# 2. SOAP API (Manual Implementation) - Port 5001\
# =============================================================================\
soap_app = Flask(__name__)\
\
WSDL_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>\
<definitions xmlns="http://schemas.xmlsoap.org/wsdl/"\
             xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"\
             xmlns:tns="http://calculator.example.com/"\
             xmlns:xsd="http://www.w3.org/2001/XMLSchema"\
             targetNamespace="http://calculator.example.com/">\
    \
    <types>\
        <xsd:schema targetNamespace="http://calculator.example.com/">\
            <xsd:element name="addRequest">\
                <xsd:complexType>\
                    <xsd:sequence>\
                        <xsd:element name="a" type="xsd:int"/>\
                        <xsd:element name="b" type="xsd:int"/>\
                    </xsd:sequence>\
                </xsd:complexType>\
            </xsd:element>\
            <xsd:element name="addResponse">\
                <xsd:complexType>\
                    <xsd:sequence>\
                        <xsd:element name="result" type="xsd:int"/>\
                    </xsd:sequence>\
                </xsd:complexType>\
            </xsd:element>\
            <xsd:element name="multiplyRequest">\
                <xsd:complexType>\
                    <xsd:sequence>\
                        <xsd:element name="a" type="xsd:int"/>\
                        <xsd:element name="b" type="xsd:int"/>\
                    </xsd:sequence>\
                </xsd:complexType>\
            </xsd:element>\
            <xsd:element name="multiplyResponse">\
                <xsd:complexType>\
                    <xsd:sequence>\
                        <xsd:element name="result" type="xsd:int"/>\
                    </xsd:sequence>\
                </xsd:complexType>\
            </xsd:element>\
        </xsd:schema>\
    </types>\
    \
    <message name="addInput">\
        <part name="parameters" element="tns:addRequest"/>\
    </message>\
    <message name="addOutput">\
        <part name="parameters" element="tns:addResponse"/>\
    </message>\
    <message name="multiplyInput">\
        <part name="parameters" element="tns:multiplyRequest"/>\
    </message>\
    <message name="multiplyOutput">\
        <part name="parameters" element="tns:multiplyResponse"/>\
    </message>\
    \
    <portType name="CalculatorPortType">\
        <operation name="add">\
            <input message="tns:addInput"/>\
            <output message="tns:addOutput"/>\
        </operation>\
        <operation name="multiply">\
            <input message="tns:multiplyInput"/>\
            <output message="tns:multiplyOutput"/>\
        </operation>\
    </portType>\
    \
    <binding name="CalculatorBinding" type="tns:CalculatorPortType">\
        <soap:binding transport="http://schemas.xmlsoap.org/soap/http"/>\
        <operation name="add">\
            <soap:operation soapAction="add"/>\
            <input><soap:body use="literal"/></input>\
            <output><soap:body use="literal"/></output>\
        </operation>\
        <operation name="multiply">\
            <soap:operation soapAction="multiply"/>\
            <input><soap:body use="literal"/></input>\
            <output><soap:body use="literal"/></output>\
        </operation>\
    </binding>\
    \
    <service name="CalculatorService">\
        <port name="CalculatorPort" binding="tns:CalculatorBinding">\
            <soap:address location="http://localhost:5001/"/>\
        </port>\
    </service>\
</definitions>"""\
\
def parse_soap_request(xml_data):\
    """Simple XML parser for SOAP requests"""\
    import re\
    \
    # Check for add operation\
    if '<calc:add>' in xml_data or '<add>' in xml_data:\
        a_match = re.search(r'<(?:calc:)?a>(\\d+)</(?:calc:)?a>', xml_data)\
        b_match = re.search(r'<(?:calc:)?b>(\\d+)</(?:calc:)?b>', xml_data)\
        if a_match and b_match:\
            return 'add', int(a_match.group(1)), int(b_match.group(1))\
    \
    # Check for multiply operation\
    if '<calc:multiply>' in xml_data or '<multiply>' in xml_data:\
        a_match = re.search(r'<(?:calc:)?a>(\\d+)</(?:calc:)?a>', xml_data)\
        b_match = re.search(r'<(?:calc:)?b>(\\d+)</(?:calc:)?b>', xml_data)\
        if a_match and b_match:\
            return 'multiply', int(a_match.group(1)), int(b_match.group(1))\
    \
    return None, None, None\
\
@soap_app.route('/', methods=['GET'])\
def soap_wsdl():\
    """Serve WSDL when ?wsdl is requested"""\
    if 'wsdl' in request.args:\
        return Response(WSDL_TEMPLATE, mimetype='text/xml')\
    return """\
    <html>\
    <body>\
        <h1>SOAP API Server</h1>\
        <p>View WSDL: <a href="?wsdl">?wsdl</a></p>\
        <p>Send SOAP requests to this endpoint</p>\
    </body>\
    </html>\
    """\
\
@soap_app.route('/', methods=['POST'])\
def soap_endpoint():\
    """Handle SOAP requests"""\
    xml_data = request.data.decode('utf-8')\
    operation, a, b = parse_soap_request(xml_data)\
    \
    if operation == 'add':\
        result = a + b\
    elif operation == 'multiply':\
        result = a * b\
    else:\
        return Response('Invalid operation', status=400)\
    \
    response = f"""<?xml version="1.0" encoding="UTF-8"?>\
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" \
               xmlns:calc="http://calculator.example.com/">\
    <soap:Body>\
        <calc:\{operation\}Response>\
            <calc:result>\{result\}</calc:result>\
        </calc:\{operation\}Response>\
    </soap:Body>\
</soap:Envelope>"""\
    \
    return Response(response, mimetype='text/xml')\
\
# =============================================================================\
# 3. JSON-RPC API - Port 5002\
# =============================================================================\
def start_jsonrpc_server():\
    """Start JSON-RPC server on port 5002"""\
    \
    class JSONRPCHandler(BaseHTTPRequestHandler):\
        def do_POST(self):\
            content_length = int(self.headers['Content-Length'])\
            post_data = self.rfile.read(content_length)\
            \
            try:\
                request_data = json.loads(post_data.decode('utf-8'))\
                method = request_data.get('method')\
                params = request_data.get('params', [])\
                request_id = request_data.get('id', 1)\
                \
                if method == 'add':\
                    result = params[0] + params[1]\
                elif method == 'multiply':\
                    result = params[0] * params[1]\
                else:\
                    raise Exception(f"Unknown method: \{method\}")\
                \
                response = \{\
                    'jsonrpc': '2.0',\
                    'result': result,\
                    'id': request_id\
                \}\
                \
                self.send_response(200)\
                self.send_header('Content-Type', 'application/json')\
                self.end_headers()\
                self.wfile.write(json.dumps(response).encode('utf-8'))\
                \
            except Exception as e:\
                error_response = \{\
                    'jsonrpc': '2.0',\
                    'error': \{'code': -32600, 'message': str(e)\},\
                    'id': None\
                \}\
                self.send_response(400)\
                self.send_header('Content-Type', 'application/json')\
                self.end_headers()\
                self.wfile.write(json.dumps(error_response).encode('utf-8'))\
        \
        def do_GET(self):\
            """Provide info page"""\
            self.send_response(200)\
            self.send_header('Content-Type', 'text/html')\
            self.end_headers()\
            html = """\
            <html>\
            <body>\
                <h1>JSON-RPC API Server</h1>\
                <p>Send POST requests with JSON-RPC 2.0 format:</p>\
                <pre>\
\{\
    "jsonrpc": "2.0",\
    "method": "add",\
    "params": [5, 3],\
    "id": 1\
\}\
                </pre>\
                <p>Available methods: add, multiply</p>\
            </body>\
            </html>\
            """\
            self.wfile.write(html.encode('utf-8'))\
        \
        def log_message(self, format, *args):\
            """Custom log format"""\
            print(f"[JSON-RPC] \{format % args\}")\
    \
    server = HTTPServer(('0.0.0.0', 5002), JSONRPCHandler)\
    print("JSON-RPC server started on http://0.0.0.0:5002")\
    server.serve_forever()\
\
# =============================================================================\
# Main - Start all three servers\
# =============================================================================\
if __name__ == '__main__':\
    print("="*60)\
    print("Starting All Three API Servers...")\
    print("="*60)\
    print("\\n1. REST API:     http://localhost:5000")\
    print("2. SOAP API:     http://localhost:5001")\
    print("3. JSON-RPC API: http://localhost:5002")\
    print("\\nPress Ctrl+C to stop all servers\\n")\
    print("="*60)\
    \
    # Start JSON-RPC in a separate thread\
    rpc_thread = threading.Thread(target=start_jsonrpc_server, daemon=True)\
    rpc_thread.start()\
    \
    # Start SOAP in a separate thread\
    soap_thread = threading.Thread(\
        target=lambda: soap_app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False),\
        daemon=True\
    )\
    soap_thread.start()\
    \
    # Start REST server (this blocks)\
    try:\
        rest_app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)\
    except KeyboardInterrupt:\
        print("\\n\\nShutting down all servers...")}