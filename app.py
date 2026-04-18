from flask import Flask, render_template, request

app = Flask(__name__)

def classificar_imc(imc):
    if imc < 18.5:
        return "Abaixo do peso", "#3498db", "⬇️"
    elif imc < 25:
        return "Peso normal", "#2ecc71", "✅"
    elif imc < 30:
        return "Sobrepeso", "#f39c12", "⚠️"
    elif imc < 35:
        return "Obesidade grau I", "#e67e22", "🔶"
    elif imc < 40:
        return "Obesidade grau II", "#e74c3c", "🔴"
    else:
        return "Obesidade grau III", "#c0392b", "🚨"

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
                }
        except ValueError:
            resultado = {"erro": "Digite valores numéricos válidos."}
    return render_template("index.html", resultado=resultado)

if __name__ == "__main__":
    app.run(debug=True)
