from flask import Flask, render_template, request, jsonify
import requests as http

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

# ── Incremento de pavimentos por incentivo ADI (Decreto 25.644/2023)
# ADI concede +1 pavimento sobre o padrão F01.
# Uso misto (Dec. 25.647/2023) concede mais +1 pavimento se houver área comercial.
ADI_PAV_ADICIONAIS = {
    ("2-4",  "ADI-I"):  1,
    ("5-6",  "ADI-I"):  1,
    ("8",    "ADI-I"):  1,
    ("10",   "ADI-I"):  1,
    ("12",   "ADI-I"):  1,
    ("14",   "ADI-I"):  1,
    ("2-4",  "ADI-II"): 1,
    ("5-6",  "ADI-II"): 1,
    ("8",    "ADI-II"): 1,
    ("10",   "ADI-II"): 1,
    ("12",   "ADI-II"): 1,
    ("14",   "ADI-II"): 1,
}

def _base_pav_range(pav):
    pav = int(pav) if pav else 0
    if pav <= 4:   return "2-4"
    if pav <= 6:   return "5-6"
    if pav <= 8:   return "8"
    if pav <= 10:  return "10"
    if pav <= 12:  return "12"
    return "14"

def _wms_query(bbox, layer):
    return http.get(
        "https://geofloripa.pmf.sc.gov.br/geoserver/wms",
        params={
            "SERVICE": "WMS", "VERSION": "1.1.1", "REQUEST": "GetFeatureInfo",
            "LAYERS": layer, "QUERY_LAYERS": layer,
            "BBOX": bbox, "WIDTH": 100, "HEIGHT": 100,
            "SRS": "EPSG:4326", "X": 50, "Y": 50,
            "INFO_FORMAT": "application/json", "FEATURE_COUNT": 1,
        },
        timeout=30,
    ).json()

@app.route("/api/zona")
def get_zona():
    address = request.args.get("address", "").strip()
    if not address:
        return jsonify({"error": "Endereço não informado"}), 400

    # 1. Geocodificação via Nominatim
    try:
        geo = http.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": address + " Florianópolis SC", "format": "json", "limit": 1},
            headers={"User-Agent": "kosmos-viabilidade/1.0"},
            timeout=10,
        ).json()
    except Exception as e:
        return jsonify({"error": f"Erro no geocoding: {str(e)}"}), 502

    if not geo:
        return jsonify({"error": "Endereço não encontrado. Tente incluir bairro ou CEP."}), 404

    lat  = float(geo[0]["lat"])
    lon  = float(geo[0]["lon"])
    display = geo[0].get("display_name", address)
    delta = 0.0005
    bbox  = f"{lon-delta},{lat-delta},{lon+delta},{lat+delta}"

    # 2. Consulta zona base + ADI em paralelo
    try:
        wms_zona = _wms_query(bbox, "Geoportal:gvw_zonas")
    except Exception as e:
        return jsonify({"error": "Não foi possível conectar ao GeoFloripa (servidor da Prefeitura de Florianópolis). O serviço pode estar instável no momento — aguarde alguns instantes e tente novamente."}), 502

    features = wms_zona.get("features", [])
    if not features:
        return jsonify({"error": "Zona não identificada. Verifique se o endereço está em Florianópolis."}), 404

    p = features[0]["properties"]
    zona_nome = p.get("nome", "").replace("-", " ").strip()

    # 3. Consulta camada ADI-I
    adi_info = None
    try:
        wms_adi = _wms_query(bbox, "Geoportal:adi")
        adi_feats = wms_adi.get("features", [])
        if adi_feats:
            ap = adi_feats[0]["properties"]
            adi_info = {
                "tipo":       "ADI-I",
                "hierarquia": ap.get("hierarquia", ""),
                "label":      ap.get("label", ""),
                "trecho":     ap.get("trecho", ""),
            }
    except Exception:
        pass

    # 4. Consulta camada ADI-II se ADI-I não encontrado
    if not adi_info:
        try:
            wms_adi2 = _wms_query(bbox, "Geoportal:adi_II")
            adi2_feats = wms_adi2.get("features", [])
            if adi2_feats:
                ap2 = adi2_feats[0]["properties"]
                adi_info = {
                    "tipo":       "ADI-II",
                    "hierarquia": ap2.get("hierarquia", ap2.get("tipo", "Setor Urbano Ampliado")),
                    "label":      ap2.get("label", ap2.get("nome", "")),
                    "trecho":     ap2.get("trecho", ""),
                }
        except Exception:
            pass

    # 5. Calcula pavimentos máximos considerando ADI
    pav_base  = int(p.get("pavimentos_padrao") or 0)
    pav_tdc   = int(p.get("pavimentos_tdc")    or 0)
    pav_range = _base_pav_range(pav_base)
    tipo_adi  = adi_info["tipo"] if adi_info else None
    pav_adicional_adi = ADI_PAV_ADICIONAIS.get((pav_range, tipo_adi), 0)
    pav_max_adi = pav_base + pav_adicional_adi

    return jsonify({
        "zona":              zona_nome,
        "descricao":         p.get("descricao", ""),
        "macroarea":         p.get("macroarea", ""),
        "endereco_encontrado": display,
        "lat": lat, "lon": lon,
        "adi": adi_info,
        "pav_max_adi":       pav_max_adi,
        "pav_adicional_adi": pav_adicional_adi,
        "params": {
            "pavimentos_padrao":  p.get("pavimentos_padrao"),
            "pavimentos_tdc":     p.get("pavimentos_tdc"),
            "taxa_ocupacao":      p.get("taxa_ocupacao", "").replace("%", ""),
            "taxa_impermeab":     p.get("taxa_impermeabilizacao", "").replace("%", ""),
            "altura_fachada":     p.get("altura_fachada"),
            "altura_cumeeira":    p.get("altura_cumeeira"),
            "ca_minimo":          p.get("aproveitamento_minimo"),
            "ca_basico":          p.get("aproveitamento_basico"),
            "ca_oodc":            p.get("aproveitamento_outorga"),
            "ca_tdc":             p.get("aproveitamento_transferencia"),
            "ca_subsolos":        p.get("aproveitamento_subsolos"),
            "ca_maximo":          p.get("aproveitamento_total"),
            "lote_minimo":        p.get("area_minima_lote"),
            "testada_minima":     p.get("testada_minima"),
            "densidade_liquida":  p.get("densidade_liquida"),
            "lei":                p.get("lei"),
        },
    })


@app.route("/")
@app.route("/viabilidade")
def viabilidade():
    return render_template("viabilidade.html")

@app.route("/imc", methods=["GET", "POST"])
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
