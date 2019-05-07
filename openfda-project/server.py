import http.server
import socketserver
import http.client
import json
import urllib.parse as urlparse

# -- IP and the port of the server
IP = "localhost"
PORT = 8000

#Definimos una función para conectarnos a la FDA

def FDA_connect(action, option=None, value=None, limit=1):
    HEADERS = {'User-Agent': 'http-client'}
    COMPANY_SEARCH = "/?search=openfda.manufacturer_name:"
    DRUG_SEARCH = "/?search=active_ingredient:"
    CLIENT = '/drug/label.json'
    URL = 'api.fda.gov'
    conn = http.client.HTTPSConnection(URL)
    if action == "search":
        if option == "drug":
            conn.request("GET", CLIENT + DRUG_SEARCH + value + '&limit={}'.format(limit), None, HEADERS)
        elif option == "company":
            conn.request("GET", CLIENT + COMPANY_SEARCH + value + '&limit={}'.format(limit), None, HEADERS)
        else:
            return False
    elif action == "list":
        conn.request('GET', CLIENT +'?limit={}'.format(limit))
    else:
        return False

    r1 = conn.getresponse()
    response = r1.read()
    json_info = response.decode("utf8")
    result = json.loads(json_info)
    conn.close()
    return result

#Esta función nos será útil para iterar sobre el diccionario "fda" dentro del JSON que recibiremos
#Evitaremos así repetir código en listar/buscar empresa/medicamento

def result_opfda(data, field):
    lista = []
    try:
        dicc = data["results"]
        for item in dicc:
            if field in item["openfda"]:
                lista.append(item["openfda"][field][0])
            else:
                lista.append("Desconocido")
    except KeyError:
        lista.append('Su búsqueda no obtuvo resultados.')
    return lista

# Definimos una función para tener una plantilla de la web de resultados

def results_web(lista):
    contents = ''
    for item in lista:
        contents += '<li>{}</li>'.format(item)
    page = '''<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
    <html><head>
    <body style='background-color: #d5f5e3'>
    <CENTER><IMG SRC="https://upload.wikimedia.org/wikipedia/commons/thumb/8/84/URJC_logo.svg/1200px-URJC_logo.svg.png" ALIGN="BOTTOM" width="150" height="50"/> </CENTER>
    <HR>
    <title>RESULTADOS</title>
    </head>
    <body>
    <CENTER><FONT FACE="arial"><H1>RESULTADOS DE LA BÚSQUEDA:</H1></FONT>
    <ul>
    {}
    </ul>
    <p align="center"><a href="http://localhost:8000/">VOLVER AL INICIO</a><p></body>  
    <HR> 
    <FONT FACE="arial"><CENTER><H4>Powered by</H4></FONT>
    <CENTER><IMG SRC="https://s3.amazonaws.com/poly-screenshots.angel.co/Project/a1/502691/ade7e3af4d1b15412a068de5075a601f-original.png" ALIGN="BOTTOM" width="150" height="50"/> </CENTER>
    
    </html>'''.format(contents)
    return page

# HTTPRequestHandler class

class testHTTPRequestHandler(http.server.BaseHTTPRequestHandler):


    # GET
    def do_GET(self):
        action = False
        path = self.path
        default_headers= True

        if path == "/":
            filename = "index.html"
            action = True
        elif path == "/buscar_farmaco.html":
            filename = "buscar_farmaco.html"
            action = True
        elif path == "/buscar_empresa.html":
            filename = "buscar_empresa.html"
            action = True
        elif path == "/listar_empresa.html":
            filename = "listar_empresa.html"
            action = True
        elif path == "/listar_farmaco.html":
            filename = "listar_farmaco.html"
            action = True
        elif path == "/listar_advertencias.html":
            filename = "listar_advertencias.html"
            action = True
        elif "?" in path:
            parsed = urlparse.urlparse(path)
            try:
                limit = urlparse.parse_qs(parsed.query)['limit'][0]
            except:
                limit = ""
            if "searchDrug" in path:
                value = urlparse.parse_qs(parsed.query)["active_ingredient"][0]
                output = FDA_connect("search","drug",value,limit)
                lista = result_opfda(output,"brand_name")
                content = results_web(lista)

            elif "searchCompany" in path:
                value = urlparse.parse_qs(parsed.query)["company"][0]
                output = FDA_connect("search","company",value,limit)
                lista = result_opfda(output,"manufacturer_name")
                content = results_web(lista)

            elif "listDrugs" in path:
                output = FDA_connect("list", limit=limit)
                lista = result_opfda(output, "brand_name")
                content = results_web(lista)

            elif "listCompanies" in path:
                output = FDA_connect("list", limit=limit)
                lista = result_opfda(output, "manufacturer_name")
                content = results_web(lista)

            elif "listWarnings" in path:
                output = FDA_connect("list", limit=limit)
                lista = []
                for item in output["results"]:
                    if 'warnings' in item:
                        lista.append(item['warnings'][0])
                    else:
                        lista.append('Desconocido')
                content = results_web(lista)
            else:
                default_headers = False
                self.send_response(404)
                self.send_header("HTTP/1.0", "404 Not Found")
                content = str(self.send_error(404))

        elif path =="/secret":
            default_headers = False
            self.send_response(401)
            self.send_header('WWW-Authenticate', 'Basic realm="Secure Area"')
            content = str(self.send_error(401))
        elif path == "/redirect":
            default_headers = False
            self.send_response(302)
            self.send_header('Location', 'http://localhost:8000/')
            content = str(self.send_error(302))
        else:
            default_headers = False
            self.send_response(404)
            self.send_header("HTTP/1.0", "404 Not Found")
            content = str(self.send_error(404))

        if default_headers:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')

        self.end_headers()

        if action:
            with open(filename, "r") as f:
                content = f.read()

        self.wfile.write(bytes(content, "utf8"))

        return

Handler = testHTTPRequestHandler
socketserver.TCPServer.allow_reuse_address = True

httpd = socketserver.TCPServer((IP, PORT), Handler)
print("serving at port", PORT)
print("Localhost:" , IP)
try:
    httpd.serve_forever()
except KeyboardInterrupt:
        pass

httpd.server_close()
print("")
