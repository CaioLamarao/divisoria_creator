"""Divisorias do fichario: frente, verso e folhas A4 com sangria, em dois conjuntos.

uso: python divisoria.py <pasta-de-saida> <pasta-das-capas>
Gera <saida>/sagas (so as grandes sagas) e <saida>/arcos (todos os arcos).
As capas sao vol-NNN.jpg: a escolhida para o arco ou, sem escolha, o volume onde
ele comeca. Capa que falta sai sem fundo.
"""
import sys, os
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter

DPI = 300
MM = DPI / 25.4
def mm(v): return round(v * MM)

W, H = mm(63), mm(88)          # 744 x 1039, a carta cortada
SANGRIA = mm(2)                 # preto que passa da linha de corte

# moldura no desenho da DON!!: lados finos, bloco grosso embaixo com uma aba no meio
LADO = mm(2.3)
BLOCO = mm(10.5)
ABA_ALT = mm(2.2)
ABA_LARG = 0.36
RAIO_FORA = mm(3.2)
RAIO_DENTRO = mm(1.0)

OPACIDADE = 0.22
AQUI = os.path.dirname(os.path.abspath(__file__))
FONTES = os.path.join(AQUI, "fontes")


def primeira(*caminhos):
    for c in caminhos:
        if os.path.exists(c):
            return c
    raise SystemExit("nenhuma destas fontes existe: " + ", ".join(caminhos))


# no Windows usa as fontes do sistema; fora dele, as livres da pasta fontes/
SERIFA = primeira("C:/Windows/Fonts/BOD_B.TTF",                 # Bodoni MT Bold: o didone do ONE PIECE DAY
                  os.path.join(FONTES, "BodoniModa-Black.ttf"))
RETA = "C:/Windows/Fonts/bahnschrift.ttf"                       # sans reta, Bold Condensed
RETA_LIVRE = {"Bold Condensed": os.path.join(FONTES, "BarlowCondensed-Bold.ttf"),
              "SemiBold Condensed": os.path.join(FONTES, "BarlowCondensed-SemiBold.ttf")}

# nome, volume de inicio, capitulos, novo mundo, capa do fundo (None: a do volume de inicio)
# a numeracao sai da ordem na lista
SAGAS = [
    ("East Blue", 1, (1, 100), False, 1),
    ("Alabasta", 12, (101, 217), False, 20),
    ("Skypiea", 24, (218, 302), False, 30),
    ("Enies Lobby", 32, (303, 441), False, 44),
    ("Thriller Bark", 46, (442, 489), False, 48),
    ("Marineford", 50, (490, 597), False, 57),
    ("Fish-Man Island", 61, (598, 653), True, 61),
    ("Dressrosa", 66, (654, 801), True, 72),
    ("Whole Cake Island", 80, (802, 908), True, 83),
    ("Wano", 90, (909, 1057), True, 103),
    ("Egghead", 105, (1058, 1125), True, 106),
    ("Elbaph", 111, (1126, None), True, 112),     # em andamento: sem capitulo final
]

# todo arco que ocupa ao menos um volume inteiro, mais Amazon Lily;
# os trechos curtos entram no arco vizinho e os capitulos ficam continuos
ARCOS = [
    ("Romance Dawn", 1, (1, 7), False, 1),
    ("Orange Town", 1, (8, 21), False, 2),
    ("Syrup Village", 3, (22, 41), False, None),
    ("Baratie", 5, (42, 68), False, None),
    ("Arlong Park", 8, (69, 100), False, None),          # com Loguetown
    ("Little Garden", 12, (101, 129), False, None),      # com Reverse Mountain e Whisky Peak
    ("Drum Island", 15, (130, 154), False, 16),
    ("Alabasta", 17, (155, 217), False, 20),
    ("Jaya", 24, (218, 236), False, 24),
    ("Skypiea", 26, (237, 302), False, 30),
    ("Long Ring Long Land", 32, (303, 321), False, 33),
    ("Water 7", 34, (322, 374), False, 37),
    ("Enies Lobby", 39, (375, 441), False, 44),          # com o pos-Enies Lobby
    ("Thriller Bark", 46, (442, 489), False, 48),
    ("Sabaody", 50, (490, 513), False, 51),
    ("Amazon Lily", 53, (514, 524), False, 53),
    ("Impel Down", 54, (525, 548), False, 54),
    ("Marineford", 56, (549, 580), False, 57),
    ("Post-War", 59, (581, 597), False, None),
    ("Fish-Man Island", 61, (598, 653), True, 61),       # com o retorno a Sabaody
    ("Punk Hazard", 66, (654, 699), True, 67),
    ("Dressrosa", 70, (700, 801), True, 72),
    ("Zou", 80, (802, 824), True, 81),
    ("Whole Cake Island", 82, (825, 908), True, 83),     # com a Reverie
    ("Wano", 90, (909, 1057), True, 103),
    ("Egghead", 105, (1058, 1125), True, 106),
    ("Elbaph", 111, (1126, None), True, 112),
]

CONJUNTOS = [("sagas", SAGAS, "SAGA"), ("arcos", ARCOS, None)]

# o recorte de cada capa que fica no fundo: sem o logo e sem os creditos
# (esquerda, topo, direita, base), em fracao da capa
RECORTES = {
    1: (0.12, 0.27, 0.875, 0.695),   # so o quadro da ilustracao
    16: (0.0, 0.31, 1.0, 0.90),
    20: (0.0, 0.31, 1.0, 0.89),
    24: (0.0, 0.33, 1.0, 0.90),
    30: (0.0, 0.315, 1.0, 0.90),
    33: (0.0, 0.33, 1.0, 0.89),
    37: (0.0, 0.295, 1.0, 0.89),
    44: (0.0, 0.27, 1.0, 0.89),
    48: (0.0, 0.26, 1.0, 0.91),
    51: (0.0, 0.25, 1.0, 0.76),      # o titulo desta fica embaixo
    57: (0.0, 0.29, 1.0, 0.89),
    61: (0.0, 0.31, 1.0, 0.90),
    67: (0.0, 0.27, 1.0, 0.90),
    72: (0.0, 0.26, 1.0, 0.89),
    81: (0.0, 0.27, 1.0, 0.905),
    83: (0.0, 0.25, 1.0, 0.895),
    103: (0.0, 0.24, 1.0, 0.81),     # edicao americana: sem o "volume 103" de baixo
    106: (0.0, 0.24, 1.0, 0.915),
    112: (0.0, 0.235, 1.0, 0.78),    # sem o "volume 112" de baixo
    53: (0.0, 0.25, 1.0, 0.80),      # o titulo desta fica embaixo
    54: (0.0, 0.18, 1.0, 0.90),
}
RECORTE_PADRAO = (0.0, 0.17, 1.0, 0.90)

CINZA_TEXTO = (238, 238, 238)
CINZA_APOIO = (150, 150, 150)


def fonte_reta(tam, estilo="Bold Condensed"):
    if not os.path.exists(RETA):
        return ImageFont.truetype(primeira(RETA_LIVRE[estilo]), tam)
    f = ImageFont.truetype(RETA, tam)
    f.set_variation_by_name(estilo)
    return f


def capa_de(pasta, volume):
    p = os.path.join(pasta, "vol-%03d.jpg" % volume)
    return p if os.path.exists(p) else None


def arte(capa, volume, w, h):
    """A ilustracao da capa, recortada, em cinza e no tamanho pedido."""
    img = ImageOps.grayscale(Image.open(capa))
    l, t, r, b = RECORTES.get(volume, RECORTE_PADRAO)
    img = img.crop((round(l * img.width), round(t * img.height),
                    round(r * img.width), round(b * img.height)))
    return ImageOps.fit(img, (w, h), Image.LANCZOS)


def losangos(w, h, passo=14):
    """A textura de losangos das tiras do cartaz: 255 onde ha losango."""
    t = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(t)
    for y in range(0, h + passo, passo):
        for x in range(0, w + passo, passo):
            dx = (passo // 2) if (y // passo) % 2 else 0
            cx, cy, r = x + dx, y, passo * 0.28
            d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=255)
    return t


def faixas(img, x0, y0, x1, y1):
    """As tiras inclinadas: losangos bem leves por dentro, e o contorno fino."""
    w, h = x1 - x0, y1 - y0
    tiras = [
        (0.16, 0.20, 0.30, 0.12), (0.34, 0.15, 0.20, 0.10),
        (0.84, 0.82, 0.28, 0.12), (0.66, 0.88, 0.18, 0.10),
    ]
    textura = losangos(img.width, img.height)
    cinza = Image.new("RGB", img.size, (150, 150, 150))
    d = ImageDraw.Draw(img)
    for fx, fy, fc, fe in tiras:
        cx, cy, comp, esp = x0 + w * fx, y0 + h * fy, h * fc, w * fe
        dx = comp * 0.22
        pts = [(cx - esp / 2 + dx, cy - comp / 2), (cx + esp / 2 + dx, cy - comp / 2),
               (cx + esp / 2 - dx, cy + comp / 2), (cx - esp / 2 - dx, cy + comp / 2)]
        dentro = Image.new("L", img.size, 0)
        ImageDraw.Draw(dentro).polygon(pts, fill=255)
        alfa = Image.composite(textura, Image.new("L", img.size, 0), dentro).point(lambda v: v * 0.35)
        img.paste(cinza, (0, 0), alfa)
        d.polygon(pts, outline=(120, 120, 120), width=2)


def cabe(d, texto, fonte, tam_max, largura):
    tam = tam_max
    while tam > 20:
        f = ImageFont.truetype(fonte, tam)
        if d.textlength(texto, font=f) <= largura:
            return f
        tam -= 2
    return ImageFont.truetype(fonte, tam)


def linhas_do_nome(d, nome, largura):
    palavras = nome.split()
    f = ImageFont.truetype(SERIFA, 104)
    if len(palavras) == 1 or d.textlength(nome, font=f) <= largura:
        return [nome]
    melhor = None
    for i in range(1, len(palavras)):
        a, b = " ".join(palavras[:i]), " ".join(palavras[i:])
        m = max(d.textlength(a, font=f), d.textlength(b, font=f))
        if melhor is None or m < melhor[0]:
            melhor = (m, [a, b])
    return melhor[1]


def escreve_junto(d, cx, cy, texto, fonte, cor, aperto):
    # letra a letra, apertado; o ponto e o espaco nao apertam, senao o "." some
    larg = [d.textlength(ch, font=fonte) for ch in texto]
    passo = [w - (0 if ch in ". " or (i + 1 < len(texto) and texto[i + 1] in ". ") else aperto)
             for i, (ch, w) in enumerate(zip(texto, larg))]
    total = sum(passo[:-1]) + larg[-1]
    x = cx - total / 2
    for ch, p in zip(texto, passo):
        d.text((x, cy), ch, font=fonte, fill=cor, anchor="lm")
        x += p


def moldura(d, ox, oy):
    """A aba chanfrada que sobe do bloco de baixo; ox/oy deslocam pela sangria."""
    jy1 = oy + H - BLOCO
    meio = ox + W / 2
    meia = W * ABA_LARG / 2
    ch = ABA_ALT * 1.1
    d.polygon([(meio - meia - ch, jy1 + 1), (meio - meia, jy1 - ABA_ALT),
               (meio + meia, jy1 - ABA_ALT), (meio + meia + ch, jy1 + 1)], fill="black")
    return meio, jy1


def rodape(d, meio, jy1, volume, caps):
    fv = fonte_reta(mm(4.2))
    escreve_junto(d, meio, jy1 - ABA_ALT + mm(2.6), "Vol. %03d" % volume,
                  fv, CINZA_TEXTO, mm(0.25))
    fc = fonte_reta(mm(2.9), "SemiBold Condensed")
    ini, fim = caps
    texto = "Cap. %03d \u2013 %03d" % caps if fim else "Cap. %03d \u2013" % ini
    escreve_junto(d, meio, jy1 + mm(6.3), texto,
                  fc, CINZA_APOIO, mm(0.12))


TOM_TRACO = 140   # o quanto a linha clareia o preto do numero: cinza, e nao branco


def tracos(cinza):
    """A arte-final da capa: so as linhas de nanquim, sem cor nem preenchimento.
    Linha e o pixel bem mais escuro que a vizinhanca; uma area preta grande e
    igual ao proprio desfoque e por isso some."""
    from PIL import ImageChops
    g = ImageOps.autocontrast(cinza)
    fundo = g.filter(ImageFilter.GaussianBlur(3))
    dif = ImageChops.subtract(fundo, g)          # quanto o pixel e mais escuro que em volta
    # rampa em vez de corte seco, e um desfoque leve: a linha sai suave, sem serrilhado
    dif = dif.filter(ImageFilter.GaussianBlur(0.8))
    return dif.point(lambda v: 255 - round(TOM_TRACO * min(1, max(0, (v - 8) / 30))))


def nome_e_numero(d, img, b, jy0, jh, util, numero, nome, sub, cor, capa=None, volume=None):
    meio = b + W / 2
    num = str(numero)
    fn = cabe(d, num, SERIFA, 470, util * 0.9)
    fp = ImageFont.truetype(SERIFA, round(fn.size * 0.30))
    wn = d.textlength(num, font=fn)
    wp = d.textlength(".", font=fp)
    x0 = meio - (wn + wp) / 2
    base = jy0 + jh * 0.56
    d.text((x0, base), num, font=fn, fill=cor, anchor="ls",
           stroke_width=mm(0.6 if capa else 0.35), stroke_fill=cor)
    if capa:
        # dentro do numero: o preto do numero, com so o traco da ilustracao em branco
        dentro = Image.new("L", img.size, 0)
        ImageDraw.Draw(dentro).text((x0, base), num, font=fn, fill=255, anchor="ls")
        dentro = dentro.filter(ImageFilter.MinFilter(3))
        traco = ImageOps.invert(tracos(arte(capa, volume, *img.size)))
        img.paste(Image.merge("RGB", [traco] * 3), (0, 0), dentro)
    d.text((x0 + wn + 4, base), ".", font=fp, fill=cor, anchor="ls")

    linhas = linhas_do_nome(d, nome.upper(), util)
    fonte = min((cabe(d, l, SERIFA, 104, util) for l in linhas), key=lambda f: f.size)
    y = base + mm(4)
    for l in linhas:
        d.text((meio, y), l, font=fonte, fill=cor, anchor="mt")
        y += fonte.size * 1.02
    if sub:
        # "SAGA" logo abaixo, no mesmo desenho e um pouco menor
        fs = ImageFont.truetype(SERIFA, round(fonte.size * 0.62))
        escreve_junto(d, meio, y + fs.size * 0.55, " ".join(sub), fs, cor, 0)


def frente(arco, pasta_capas, sangria):
    numero, nome, volume, caps, novo, vol_capa, sub = arco
    b = SANGRIA if sangria else 0
    img = Image.new("RGB", (W + 2 * b, H + 2 * b), "black")
    jx0, jy0, jx1, jy1 = b + LADO, b + LADO, b + W - LADO, b + H - BLOCO
    jw, jh = jx1 - jx0, jy1 - jy0

    capa = capa_de(pasta_capas, vol_capa)
    a = arte(capa, vol_capa, jw, jh) if capa else Image.new("L", (jw, jh), 255)
    janela = Image.blend(Image.new("L", (jw, jh), 255), a, OPACIDADE).convert("RGB")
    mj = Image.new("L", (jw, jh), 0)
    ImageDraw.Draw(mj).rounded_rectangle([0, 0, jw - 1, jh - 1], radius=RAIO_DENTRO, fill=255)
    img.paste(janela, (jx0, jy0), mj)

    faixas(img, jx0, jy0, jx1, jy1)
    d = ImageDraw.Draw(img)
    meio, _ = moldura(d, b, b)

    if novo:
        fs = fonte_reta(mm(2.6), "SemiBold Condensed")
        y = jy0 + mm(3.2)
        texto = "N E W   W O R L D"
        escreve_junto(d, meio, y, texto, fs, (40, 40, 40), 0)
        tl = d.textlength(texto, font=fs)
        for s in (-1, 1):
            xa = meio + s * (tl / 2 + mm(1.5))
            d.line([(xa, y), (xa + s * mm(6), y)], fill=(40, 40, 40), width=2)

    nome_e_numero(d, img, b, jy0, jh, jw - mm(6), numero, nome, sub, "black", capa, vol_capa)
    rodape(d, meio, jy1, volume, caps)
    return img


def verso(arco, sangria):
    """Preto liso, para o bolso de tras do fichario mostrar a mesma divisoria."""
    numero, nome, volume, caps, _, _, sub = arco
    b = SANGRIA if sangria else 0
    img = Image.new("RGB", (W + 2 * b, H + 2 * b), "black")
    d = ImageDraw.Draw(img)
    jx0, jy0, jx1, jy1 = b + LADO, b + LADO, b + W - LADO, b + H - BLOCO
    # fio fino da janela, para o verso ter a forma da frente
    d.rounded_rectangle([jx0, jy0, jx1, jy1], radius=RAIO_DENTRO, outline=(70, 70, 70), width=2)
    nome_e_numero(d, img, b, jy0, jy1 - jy0, jx1 - jx0 - mm(6), numero, nome, sub, "white")
    meio, jy1 = moldura(d, b, b)
    rodape(d, meio, jy1, volume, caps)
    return img


def arredonda(img):
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, img.width - 1, img.height - 1], radius=RAIO_FORA, fill=255)
    f = Image.new("RGBA", img.size, (0, 0, 0, 0))
    f.paste(img, (0, 0), m)
    return f


# A4 3 x 3, cada carta com a sangria encostando na da vizinha
A4W, A4H = mm(210), mm(297)
CW, CH = W + 2 * SANGRIA, H + 2 * SANGRIA


def folha(cartas, espelhar=False):
    pg = Image.new("RGB", (A4W, A4H), "white")
    mx, my = (A4W - 3 * CW) // 2, (A4H - 3 * CH) // 2
    d = ImageDraw.Draw(pg)
    for i, c in enumerate(cartas):
        col, lin = i % 3, i // 3
        if espelhar:      # o verso e impresso virando pela borda longa
            col = 2 - col
        pg.paste(c, (mx + col * CW, my + lin * CH))
    # marcas de corte na margem, alinhadas com as linhas de corte
    marca, folga = mm(4), mm(1)
    cortes_x = sorted({mx + c * CW + s for c in range(3) for s in (SANGRIA, SANGRIA + W)})
    cortes_y = sorted({my + l * CH + s for l in range(3) for s in (SANGRIA, SANGRIA + H)})
    for x in cortes_x:
        d.line([(x, my - folga - marca), (x, my - folga)], fill="black", width=2)
        d.line([(x, my + 3 * CH + folga), (x, my + 3 * CH + folga + marca)], fill="black", width=2)
    for y in cortes_y:
        d.line([(mx - folga - marca, y), (mx - folga, y)], fill="black", width=2)
        d.line([(mx + 3 * CW + folga, y), (mx + 3 * CW + folga + marca, y)], fill="black", width=2)
    return pg


def gera(pasta, lista, sub, capas):
    os.makedirs(os.path.join(pasta, "cartas"), exist_ok=True)
    frentes, versos, sem_capa = [], [], []
    for n, (nome, volume, caps, novo, vol_capa) in enumerate(lista, 1):
        arco = (n, nome, volume, caps, novo, vol_capa or volume, sub)
        if not capa_de(capas, arco[5]):
            sem_capa.append(nome)
        arredonda(frente(arco, capas, False)).save(
            os.path.join(pasta, "cartas", "%02d-frente.png" % n), dpi=(DPI, DPI))
        arredonda(verso(arco, False)).save(
            os.path.join(pasta, "cartas", "%02d-verso.png" % n), dpi=(DPI, DPI))
        frentes.append(frente(arco, capas, True))
        versos.append(verso(arco, True))

    paginas = []
    for i in range(0, len(frentes), 9):
        paginas.append(folha(frentes[i:i + 9]))
        paginas.append(folha(versos[i:i + 9], espelhar=True))
    paginas[0].save(os.path.join(pasta, "divisorias-A4.pdf"), save_all=True,
                    append_images=paginas[1:], resolution=DPI)

    # todas as frentes lado a lado, em meia resolucao
    col = 7
    lin = -(-len(frentes) // col)
    p = Image.new("RGB", (col * (W + 20) + 20, lin * (H + 20) + 20), (200, 200, 200))
    for k in range(len(frentes)):
        im = Image.open(os.path.join(pasta, "cartas", "%02d-frente.png" % (k + 1)))
        p.paste(im, (20 + k % col * (W + 20), 20 + k // col * (H + 20)), im)
    p.resize((p.width // 2, p.height // 2), Image.LANCZOS).save(os.path.join(pasta, "previa.png"))
    return sem_capa


if __name__ == "__main__":
    saida, capas = sys.argv[1], sys.argv[2]
    for nome, lista, sub in CONJUNTOS:
        sem = gera(os.path.join(saida, nome), lista, sub, capas)
        print("%s: %d divisorias; sem capa: %s" % (nome, len(lista), ", ".join(sem) or "-"))
