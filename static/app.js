
const formulario = document.getElementById("formulario");
const resultado = document.getElementById("resultado");
const contenido = document.getElementById("contenido");
const error = document.getElementById("error");

formulario.addEventListener("submit", async (event) => {
    event.preventDefault();

    resultado.hidden = true;
    error.textContent = "";

    const datos = {
        codigo_pedido: document.getElementById("codigo_pedido").value,
        distancia_km: Number(document.getElementById("distancia_km").value),
        tipo_envio: document.getElementById("tipo_envio").value,
        horas_desde_pedido: Number(
            document.getElementById("horas_desde_pedido").value
        ),
        es_festivo: document.getElementById("es_festivo").checked,
        clima_adverso: document.getElementById("clima_adverso").checked,
        zona_remota: document.getElementById("zona_remota").checked
    };

    try {
        const respuesta = await fetch("/api/predecir-retraso", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(datos)
        });

        const informacion = await respuesta.json();

        if (!respuesta.ok) {
            const detalle = Array.isArray(informacion.detail)
                ? informacion.detail.map(item => item.msg).join("; ")
                : informacion.detail || "No se pudo evaluar el pedido.";

            throw new Error(detalle);
        }

        contenido.replaceChildren();

        const campos = [
            ["Código del pedido", informacion.codigo_pedido],
            ["Nivel de riesgo", informacion.riesgo_retraso],
            ["Puntuación de riesgo", `${informacion.score_riesgo}/100`],
            [
                "Probabilidad simulada",
                `${informacion.probabilidad_retraso * 100}%`
            ],
            [
                "Retraso estimado",
                `${informacion.retraso_estimado_horas} horas`
            ],
            ["Explicación", informacion.motivo]
        ];

        for (const [etiqueta, valor] of campos) {
            const parrafo = document.createElement("p");
            const negrita = document.createElement("strong");

            negrita.textContent = `${etiqueta}: `;
            parrafo.append(negrita, document.createTextNode(String(valor)));
            contenido.appendChild(parrafo);
        }

        resultado.hidden = false;

    } catch (err) {
        error.textContent = `Error: ${err.message}`;
    }
});
