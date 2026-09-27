import re
import json
import requests
from bs4 import BeautifulSoup

JS_FILE = "convenciones.js"

def extraer_eventos():
    with open(JS_FILE, "r", encoding="utf-8") as f:
        contenido = f.read()
    
    # Extraer el array JSON desde convenciones.js
    coincidencia = re.search(r"const\s+CONVENCIONES\s*=\s*(\[[\s\S]*?\])\s*;", contenido)
    if not coincidencia:
        print("No se encontró el array CONVENCIONES en el archivo.")
        return None, contenido
    
    # Convertir sintaxis de JS relajada a JSON válido si es necesario
    json_str = coincidencia.group(1)
    # Reemplazar claves sin comillas o comillas simples
    try:
        eventos = json.loads(json_str)
    except Exception:
        # Si tiene comillas simples en strings
        import ast
        eventos = ast.literal_eval(json_str)
    
    return eventos, contenido

def auditar_y_actualizar():
    eventos, raw = extraer_eventos()
    if not eventos:
        return

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    modificado = False
    print(f"Iniciando auditoría de {len(eventos)} eventos...\n")

    for ev in eventos:
        url = ev.get("enlaceExterno", "")
        if not url or url == "#" or not url.startswith("http"):
            continue

        try:
            print(f"Revisando: {ev['nombre']} ({url})")
            resp = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
            
            if resp.status_code >= 400:
                print(f"  [AVISO] Web con error {resp.status_code}")
                continue

            # Buscar si la web publica un cartel o banner oficial (etiqueta OpenGraph og:image)
            soup = BeautifulSoup(resp.text, "html.parser")
            og_image = soup.find("meta", property="og:image")
            if og_image and og_image.get("content"):
                img_url = og_image["content"].strip()
                if img_url.startswith("http") and not ev.get("cartel"):
                    print(f"  [ACTUALIZADO] Cartel detectado: {img_url}")
                    ev["cartel"] = img_url
                    modificado = True

        except Exception as e:
            print(f"  [ERROR] No se pudo conectar: {e}")

    # Guardar de nuevo en convenciones.js si hubo cambios
    nuevo_contenido = f"const CONVENCIONES = {json.dumps(eventos, indent=2, ensure_ascii=False)};\n"
    with open(JS_FILE, "w", encoding="utf-8") as f:
        f.write(nuevo_contenido)
    
    print("\nProceso finalizado con éxito.")

if __name__ == "__main__":
    auditar_y_actualizar()
