from flask import Flask, render_template, request

app = Flask(__name__)

DICAS = {
    "Abaixo do peso": [
        "Aumente a ingestão calórica com alimentos nutritivos como abacate, oleaginosas e proteínas.",
        "Faça de 5 a 6 refeições por dia para ganhar peso de forma saudável.",
        "Pratique musculação para ganhar massa muscular.",
        "Consulte um nutricionista para um plano alimentar personalizado.",
    ],
    "Peso normal": [
        "Parabéns! Mantenha uma alimentação equilibrada com frutas, legumes e proteínas.",
        "Pratique pelo menos 150 minutos de atividade física moderada por semana.",
        "Beba de 2 a 3 litros de água por dia.",
        "Faça check-ups médicos anuais para monitorar sua saúde.",
    ],
    "Sobrepeso": [
        "Reduza o consumo de alimentos ultraprocessados, açúcar e gorduras saturadas.",
        "Inclua 30 minutos de caminhada no seu dia a dia.",
        "Prefira alimentos integrais, ricos em fibras que prolongam a saciedade.",
        "Evite bebidas açucaradas — substitua por água ou chás sem açúcar.",
    ],
    "Obesidade grau I": [
        "Busque acompanhamento médico e nutricional para um plano seguro de emagrecimento.",
        "Comece com exercícios de baixo impacto como caminhada ou natação.",
        "Reduza o tamanho das porções e coma devagar, mastigando bem.",
        "Durma de 7 a 9 horas por noite — o sono regula os hormônios da fome.",
    ],
    "Obesidade grau II": [
        "Consulte um médico para avaliação completa e acompanhamento especializado.",
        "Exercícios supervisionados por um profissional de educação física são essenciais.",
        "Evite dietas restritivas sem orientação — podem ser perigosas.",
        "Considere apoio psicológico, pois o emocional influencia muito os hábitos alimentares.",
    ],
    "Obesidade grau III": [
        "Procure atendimento médico imediatamente para uma avaliação completa.",
        "Há risco elevado de diabetes, hipertensão e problemas cardíacos — monitoramento é essencial.",
        "O tratamento multidisciplinar (médico, nutricionista e psicólogo) é o mais eficaz.",
        "Evite qualquer mudança brusca na dieta sem orientação profissional.",
    ],
}

def classificar_imc(imc):
    if imc < 18.5:
        return "Abaixo do peso", "#3b82f6", "⬇️"
    elif imc < 25:
        return "Peso normal", "#22c55e", "✅"
    elif imc < 30:
        return "Sobrepeso", "#eab308", "⚠️"
    elif imc < 35:
        return "Obesidade grau I", "#f97316", "🔶"
    elif imc < 40:
        return "Obesidade grau II", "#ef4444", "🔴"
    else:
        return "Obesidade grau III", "#991b1b", "🚨"

@app.route("/viabilidade")
def viabilidade():
    return render_template("viabilidade.html")

@app.route("/", methods=["GET", "POST"])
def index():
    resultado = None
    if request.method == "POST":
        try:
            peso = float(request.form["peso"])
            altura = float(request.form["altura"])
            if peso <= 0 or altura <= 0:
                resultado = {"erro": "Peso e altura devem ser maiores que zero."}
            else:
                imc = peso / (altura ** 2)
                classificacao, cor, icone = classificar_imc(imc)
                resultado = {
                    "imc": f"{imc:.2f}",
                    "classificacao": classificacao,
                    "cor": cor,
                    "icone": icone,
                    "peso": peso,
                    "altura": altura,
                    "dicas": DICAS[classificacao],
                }
        except ValueError:
            resultado = {"erro": "Digite valores numéricos válidos."}
    return render_template("index.html", resultado=resultado)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
