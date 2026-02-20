import ollama
import datetime
import sys

# Configuración Modelo 
MODEL = "qwen2.5:3b"
KEEP_ALIVE = -1
TEMPERATURE = 0.35 
MAX_TOKENS = 220
SYSTEM_PROMPT = """

"""

#Herramientas
def consultar_estado_pedido(numero_pedido: str) -> str:
    """Consulta el estado actual de un pedido por su número"""
    estados = {
        "12345": "En tránsito - entrega estimada mañana 10-12 am",
        "67890": "Entregado el 15/02/2026",
        "54321": "Procesando pago - pendiente confirmación",
        "99999": "Cancelado por falta de stock"
    }
    return estados.get(numero_pedido.strip(), "No encontramos ese número de pedido. ¿Puedes confirmármelo?")


def obtener_hora_actual() -> str:
    """Devuelve la hora actual en San José, Costa Rica"""
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-6)))
    return now.strftime("%I:%M %p del %d de %B de %Y")


available_tools = {
    "consultar_estado_pedido": consultar_estado_pedido,
    "obtener_hora_actual": obtener_hora_actual,
}

#Carga del Modelo
print("Cargando LIA")
ollama.generate(model=MODEL, prompt="", keep_alive=KEEP_ALIVE)
print("Modelo Cargado en Memoria!\n")

#ChatBot
messages = [{"role": "system", "content": SYSTEM_PROMPT}]

print("Chatbot de servicio al cliente iniciado.")
print("Escribe 'adiós' o 'salir' para terminar.\n")

while True:
    user_input = input("Tú: ").strip()

    if user_input.lower() in ["salir", "adiós", "bye", "exit"]:
        print("\n¡Gracias por contactarnos! Estamos para ayudarte cuando quieras. 😊")
        sys.exit(0)

    if not user_input:
        continue

    messages.append({"role": "user", "content": user_input})

    try:
        # Primera llamada al modelo
        response = ollama.chat(
            model=MODEL,
            messages=messages,
            tools=list(available_tools.values()),
            keep_alive=KEEP_ALIVE,
            options={
                "temperature": TEMPERATURE,
                "num_predict": MAX_TOKENS
            }
        )

        messages.append(response["message"])

        #Proceso de Tools
        if response["message"].get("tool_calls"):
            print(" (usando herramientas internas...)")
            tool_results_added = False

            for tool_call in response["message"]["tool_calls"]:
                func_name = tool_call["function"]["name"]
                args = tool_call["function"].get("arguments") or {}

                if func_name == "consultar_estado_pedido":
                    numero = str(args.get("numero_pedido", "")).strip()
                    if not numero or not numero.isdigit() or len(numero) < 4:
                        result = "Por favor, dime el número exacto de tu pedido para poder consultarlo."
                        print(f" → {func_name} → Ignorado (número inválido)")
                    else:
                        result = available_tools[func_name](numero)
                        print(f" → {func_name} → {result}")
                        tool_results_added = True

                elif func_name == "obtener_hora_actual":
                    result = available_tools[func_name]()
                    print(f" → {func_name} → {result}")
                    tool_results_added = True
                else:
                    result = "Herramienta desconocida"
                    tool_results_added = True

                # Agregamos siempre el resultado de la tool al historial
                messages.append({
                    "role": "tool",
                    "tool_name": func_name,
                    "content": str(result)
                })

            # Solo hacemos segunda llamada si se ejecutó alguna tool válida
            if tool_results_added:
                final_response = ollama.chat(
                    model=MODEL,
                    messages=messages,
                    tools=list(available_tools.values()),
                    keep_alive=KEEP_ALIVE,
                    options={"temperature": TEMPERATURE, "num_predict": MAX_TOKENS}
                )
                reply = final_response["message"]["content"].strip()
                messages.append(final_response["message"])
            else:
                reply = response["message"]["content"].strip()

        else:
            # SSi no hay tools,responder directo
            reply = response["message"]["content"].strip()

        print("Asistente:", reply)

    except Exception as e:
        print(f"Error: {str(e)}")
        print("Asegúrate que Ollama  no esta corriendo,ejecute en consola ´ollama serve`.")