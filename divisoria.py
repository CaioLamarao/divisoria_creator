"""Divisorias de arco para o fichario: frente, verso e folhas A4 com sangria.

uso: python divisoria.py <pasta-de-saida> <pasta-das-capas>
As capas sao vol-NNN.jpg: o volume onde o arco comeca, ou o escolhido em CAPAS.
Capa que falta sai sem fundo.
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

ARCOS = [
    # numero, nome, volume, capitulos, novo mundo
    (1, "East Blue", 1, (1, 100), False),
    (2, "Alabasta", 17, (155, 217), False),
    (3, "Skypiea", 26, (237, 302), False),
    (4, "Water 7", 34, (322, 374), False),
    (5, "Enies Lobby", 39, (375, 430), False),
    (6, "Thriller Bark", 46, (442, 489), False),
    (7, "Sabaody", 50, (490, 513), False),
    (8, "Impel Down", 54, (525, 548), False),
    (9, "Marineford", 56, (549, 580), False),
    (10, "Fish-Man Island", 61, (603, 653), True),
    (11, "Punk Hazard", 66, (654, 699), True),
    (12, "Dressrosa", 70, (700, 801), True),
    (13, "Whole Cake Island", 82, (825, 902), True),
    (14, "Wano", 90, (909, 1057), True),
    (15, "Egghead", 105, (1058, 1125), True),
    (16, "Elbaph", 111, (1126, None), True),     # em andamento: sem capitulo final
]

# arcos cujo fundo vem de outra capa que nao a do volume de inicio
CAPAS = {2: 20, 3: 30, 4: 37}

# o recorte de cada capa que fica no fundo: sem o logo e sem os creditos
# (esquerda, topo, direita, base), em fracao da capa
RECORTES = {
    1: (0.12, 0.27, 0.875, 0.695),   # so o quadro da ilustracao
    20: (0.0, 0.31, 1.0, 0.89),
    30: (0.0, 0.315, 1.0, 0.90),
    37: (0.0, 0.295, 1.0, 0.89),
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


def nome_e_numero(d, img, b, jy0, jh, util, numero, nome, cor, capa=None, volume=None):
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


def frente(arco, pasta_capas, sangria):
    numero, nome, volume, caps, novo = arco
    b = SANGRIA if sangria else 0
    img = Image.new("RGB", (W + 2 * b, H + 2 * b), "black")
    jx0, jy0, jx1, jy1 = b + LADO, b + LADO, b + W - LADO, b + H - BLOCO
    jw, jh = jx1 - jx0, jy1 - jy0

    vol_capa = CAPAS.get(numero, volume)
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

    nome_e_numero(d, img, b, jy0, jh, jw - mm(6), numero, nome, "black", capa, vol_capa)
    rodape(d, meio, jy1, volume, caps)
    return img


def verso(arco, sangria):
    """Preto liso, para o bolso de tras do fichario mostrar a mesma divisoria."""
    numero, nome, volume, caps, _ = arco
    b = SANGRIA if sangria else 0
    img = Image.new("RGB", (W + 2 * b, H + 2 * b), "black")
    d = ImageDraw.Draw(img)
    jx0, jy0, jx1, jy1 = b + LADO, b + LADO, b + W - LADO, b + H - BLOCO
    # fio fino da janela, para o verso ter a forma da frente
    d.rounded_rectangle([jx0, jy0, jx1, jy1], radius=RAIO_DENTRO, outline=(70, 70, 70), width=2)
    nome_e_numero(d, img, b, jy0, jy1 - jy0, jx1 - jx0 - mm(6), numero, nome, "white")
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


if __name__ == "__main__":
    saida, capas = sys.argv[1], sys.argv[2]
    os.makedirs(os.path.join(saida, "cartas"), exist_ok=True)
    frentes, versos, sem_capa = [], [], []
    for arco in ARCOS:
        n = arco[0]
        vol = CAPAS.get(n, arco[2])
        if not capa_de(capas, vol):
            sem_capa.append(vol)
        arredonda(frente(arco, capas, False)).save(
            os.path.join(saida, "cartas", "arco-%02d-frente.png" % n), dpi=(DPI, DPI))
        arredonda(verso(arco, False)).save(
            os.path.join(saida, "cartas", "arco-%02d-verso.png" % n), dpi=(DPI, DPI))
        frentes.append(frente(arco, capas, True))
        versos.append(verso(arco, True))

    paginas = []
    for i in range(0, len(frentes), 9):
        paginas.append(folha(frentes[i:i + 9]))
        paginas.append(folha(versos[i:i + 9], espelhar=True))
    paginas[0].save(os.path.join(saida, "divisorias-A4.pdf"), save_all=True,
                    append_images=paginas[1:], resolution=DPI)
    for i, p in enumerate(paginas):
        p.resize((A4W // 4, A4H // 4)).save(os.path.join(saida, "folha-%d.png" % (i + 1)))

    ims = [Image.open(os.path.join(saida, "cartas", f)) for f in
           ("arco-01-frente.png", "arco-08-frente.png", "arco-13-frente.png", "arco-08-verso.png")]
    p = Image.new("RGB", (W * 4 + 100, H + 40), (200, 200, 200))
    for k, im in enumerate(ims):
        p.paste(im, (20 + k * (W + 20), 20), im)
    p.save(os.path.join(saida, "previa.png"))
    print("sem capa:", ", ".join("%03d" % v for v in sem_capa))
