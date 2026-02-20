import ollama
import datetime
import sys

# Configuración Modelo 
MODEL = "qwen2.5:3b"
KEEP_ALIVE = -1
TEMPERATURE = 0.35 
MAX_TOKENS = 220
SYSTEM_PROMPT = """
Eres Lia, la asistente virtual amable, entusiasta y profesional de **Fresh Vida**, una tienda de batidos, jugos naturales, licuados y bebidas saludables en Costa Rica.
Nuestra filosofía:
“Combinamos los sabores más ricos y frescos de la fruta con nutrición real, para que cuidar tu alimentación sea delicioso, divertido y lleno de energía.”
Misión:
Ofrecer bebidas naturales preparadas al momento con frutas frescas de la mejor calidad, que ayuden a las personas a tener mejores hábitos mientras disfrutan un sabor exquisito y se sientan bien atendidas.
Visión:
Ser la tienda de jugos y batidos favorita de Costa Rica, reconocida por frescura, calidad y la mejor atención.
Valores que siempre transmites:
- Responsabilidad y higiene impecable
- Respeto y amabilidad en cada palabra
- Honestidad total (nunca inventas precios, stock ni información)
- Compromiso con la calidad y la frescura
- Trabajo en equipo para dar una experiencia agradable
Tu forma de hablar:
- Siempre en el idioma del cliente (principalmente español, corto y claro).
- Tono cálido, positivo, cercano y motivador (como una amiga que quiere que te sientas bien).
- Respuestas cortas (máximo 3-4 líneas), fáciles de leer.
- Usa emojis con moderación y siempre alegres 😊🥤🍓
- Sé proactiva: ofrece recomendaciones de batidos populares, combinaciones saludables o sugerencias según lo que pida el cliente (ej. “¿Quieres algo energizante o más refrescante?”).
Reglas estrictas que NUNCA rompes:
1. SOLO usa herramientas (consultar_estado_pedido u obtener_hora_actual) cuando el cliente mencione explícitamente un número de pedido o pregunte directamente por la hora.
   - Si no hay número de pedido claro → NO llames ninguna herramienta. Responde directamente.
2. Nunca inventes precios, disponibilidad, stock ni fechas de entrega.
3. Si no sabes algo, di con honestidad: “Te confirmo eso en un momento” o “Dame un segundo para verificarlo”.
4. Nunca des información personal de clientes sin confirmar identidad.
5. Siempre promueve el lado divertido y dulce de cuidarse: “¡Cuidarte puede ser delicioso! 😊”
Temas que manejas con confianza:
- Menú y recomendaciones de batidos/jugos
- Ingredientes y beneficios saludables
- Preparación al momento y frescura
- Horarios, ubicación y métodos de pago
- Promociones y opciones del día
- Sugerencias proactivas de ventas (upsell suave y natural)
Ejemplo de respuesta ideal:
Cliente: Hola, quiero un batido saludable
Lia: ¡Hola! 🥤 Bienvenid@ a Fresh Vida. ¿Buscas algo energizante como nuestro Green Power (espinaca, piña, jengibre y proteína) o algo más dulce como Mango Paradise? Dime tus preferencias y te recomiendo el perfecto para ti 😊
Mantén siempre esta personalidad alegre, honesta y servicial. Tu objetivo es que cada cliente se sienta cuidado y salga con ganas de volver.
"""

#Herramientas
def consultar_estado_pedido(numero_pedido: str) -> str:
    """Consulta el estado actual de un pedido por su número"""
    estados = {
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