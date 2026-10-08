"""ETL: CSVs brutos do TSE (0FN) + JSONs de votos -> modelo relacional 3FN em JSON compacto.

uso: python -I etl.py <detalhe_votacao.csv> <lista_candidatos.csv> <dir_json_votos> <saida.json>
"""
import csv, json, os, sys, glob
from collections import Counter

DET, CAND, VDIR, OUT = sys.argv[1:5]

UF_NOME = {
    'AC': 'Acre', 'AL': 'Alagoas', 'AM': 'Amazonas', 'AP': 'Amapá', 'BA': 'Bahia', 'CE': 'Ceará',
    'DF': 'Distrito Federal', 'ES': 'Espírito Santo', 'GO': 'Goiás', 'MA': 'Maranhão',
    'MG': 'Minas Gerais', 'MS': 'Mato Grosso do Sul', 'MT': 'Mato Grosso', 'PA': 'Pará',
    'PB': 'Paraíba', 'PE': 'Pernambuco', 'PI': 'Piauí', 'PR': 'Paraná', 'RJ': 'Rio de Janeiro',
    'RN': 'Rio Grande do Norte', 'RO': 'Rondônia', 'RR': 'Roraima', 'RS': 'Rio Grande do Sul',
    'SC': 'Santa Catarina', 'SE': 'Sergipe', 'SP': 'São Paulo', 'TO': 'Tocantins', 'ZZ': 'Exterior',
}
CARGOS = [(1, 'Presidente'), (2, 'Vice-presidente'), (3, 'Governador'), (4, 'Vice-governador'),
          (5, 'Senador'), (6, 'Deputado Federal'), (7, 'Deputado Estadual'), (8, 'Deputado Distrital'),
          (9, '1º Suplente'), (10, '2º Suplente')]
CARGO_IDX = {ds: i for i, (_, ds) in enumerate(CARGOS)}
# membro de chapa -> cargo do titular
CHAPA = {'Vice-presidente': ('Presidente', 'Vice'), 'Vice-governador': ('Governador', 'Vice'),
         '1º Suplente': ('Senador', '1º Suplente'), '2º Suplente': ('Senador', '2º Suplente')}
# nomes oficiais dos partidos (o CSV traz só a sigla; o JSON do TSE vem com acentos corrompidos)
PARTIDO_NOME = {
    'AGIR': 'Agir', 'AVANTE': 'Avante', 'CIDADANIA': 'Cidadania', 'DC': 'Democracia Cristã',
    'DEMOCRATA': 'Democrata', 'MDB': 'Movimento Democrático Brasileiro', 'MISSÃO': 'Partido Missão',
    'MOBILIZA': 'Mobilização Nacional', 'NOVO': 'Partido Novo', 'PCDOB': 'Partido Comunista do Brasil',
    'PCB': 'Partido Comunista Brasileiro', 'PCO': 'Partido da Causa Operária', 'PDT': 'Partido Democrático Trabalhista',
    'PL': 'Partido Liberal', 'PMB': 'Partido da Mulher Brasileira', 'PODE': 'Podemos', 'PP': 'Progressistas',
    'PRD': 'Partido Renovação Democrática', 'PRTB': 'Partido Renovador Trabalhista Brasileiro',
    'PSB': 'Partido Socialista Brasileiro', 'PSD': 'Partido Social Democrático',
    'PSDB': 'Partido da Social Democracia Brasileira', 'PSOL': 'Partido Socialismo e Liberdade',
    'PSTU': 'Partido Socialista dos Trabalhadores Unificado', 'PT': 'Partido dos Trabalhadores',
    'PV': 'Partido Verde', 'REDE': 'Rede Sustentabilidade', 'REPUBLICANOS': 'Republicanos',
    'SOLIDARIEDADE': 'Solidariedade', 'UNIÃO': 'União Brasil', 'UP': 'Unidade Popular',
}

def num(s):
    s = (s or '').strip()
    if s in ('', '#NULO', '#NE'):
        return None
    try:
        return float(s.replace('.', '').replace(',', '.')) if ',' in s else int(s)
    except ValueError:
        return None

# ---------------- RESULTADO_MUNICIPIO_CARGO (detalhe) ----------------
regioes, ufs, muns, res = [], [], [], []
reg_idx, uf_idx, mun_idx = {}, {}, {}
RES_COLS = ['qt_aptos', 'qt_comparecimento', 'qt_abstencoes', 'qt_votos_validos', 'qt_votos_nominais',
            'qt_votos_legenda', 'qt_votos_brancos', 'qt_votos_nulos', 'qt_anulados_subjudice',
            'qt_secoes', 'qt_secoes_instaladas']
RES_SRC = [18, 9, 20, 13, 11, 8, 7, 26, 24, 15, 32]
dt_carga = ''
with open(DET, encoding='latin-1', newline='') as f:
    r = csv.reader(f, delimiter=';')
    next(r)
    for row in r:
        ano, cargo, cdm, nmm, reg, turno, uf = row[:7]
        if reg not in reg_idx:
            reg_idx[reg] = len(regioes); regioes.append(reg.title().replace('-O', '-o'))
        if uf not in uf_idx:
            uf_idx[uf] = len(ufs); ufs.append([uf, UF_NOME[uf], reg_idx[reg]])
        if cdm not in mun_idx:
            mun_idx[cdm] = len(muns); muns.append([cdm, nmm, uf_idx[uf]])
        res.append([mun_idx[cdm], CARGO_IDX[cargo]] + [int(row[i]) for i in RES_SRC])
        dt_carga = row[33]
uf_idx['BR'] = len(ufs); ufs.append(['BR', 'Brasil', None])

# ---------------- CANDIDATURA / PARTIDO / COMPOSICAO_CHAPA ----------------
partidos, part_idx, cands, cand_idx = [], {}, [], {}
with open(CAND, encoding='latin-1', newline='') as f:
    r = csv.DictReader(f, delimiter=';')
    for row in r:
        sg = row['sg_partido']
        if sg not in part_idx:
            part_idx[sg] = len(partidos); partidos.append([sg, PARTIDO_NOME.get(sg, sg)])
        uf = row['sg_uf']
        if uf not in uf_idx:
            raise SystemExit(f'UF desconhecida {uf}')
        sit = row['ds_sit_tot_turno']
        cand_idx[row['sq_candidato']] = len(cands)
        cands.append([row['sq_candidato'], int(row['nr_candidato']), row['nm_candidato'].strip(),
                      row['nm_urna_candidato'].strip(), part_idx[sg], CARGO_IDX[row['ds_cargo']],
                      uf_idx[uf], row['ds_situacao_julgamento'], None if sit == '#NULO' else sit,
                      num(row['vr_despesa_max_campanha'])])
CAND_COLS = ['sq_candidato', 'nr_candidato', 'nm_candidato', 'nm_urna', 'partido', 'cargo', 'uf',
             'ds_situacao_julgamento', 'ds_sit_tot_turno', 'vr_despesa_max']

# composição: vínculo oficial do JSON (vs) quando houver; senão mesmo (UF, cargo-pai, nr), sq mais próximo
chapa = {}
titulares = {}
for i, c in enumerate(cands):
    titulares.setdefault((c[6], CARGOS[c[5]][1], c[1]), []).append(i)

# ---------------- VOTACAO_CANDIDATO (JSONs por UF) ----------------
votos = []
abr_tot = []  # totais oficiais por abrangência/cargo vindos do JSON (conferência)
miss = 0
for fp in sorted(glob.glob(os.path.join(VDIR, '*-u.json'))):
    d = json.loads(open(fp, 'rb').read().decode('utf-8', 'replace'))
    uf = d['cdabr'].upper()
    for cg in d['carg']:
        cgi = CARGO_IDX[{1: 'Presidente', 3: 'Governador', 5: 'Senador', 6: 'Deputado Federal',
                         7: 'Deputado Estadual', 8: 'Deputado Distrital'}[int(cg['cd'])]]
        for ag in cg['agr']:
            for p in ag['par']:
                for c in p.get('cand', []):
                    ci = cand_idx.get(c['sqcand'])
                    if ci is None:
                        miss += 1; continue
                    votos.append([ci, uf_idx[uf], int(c['vap'] or 0), float(c['pvapn'].replace(',', '.') or 0),
                                  int(c['seq'] or 0), 1 if c.get('dvt','').startswith('V') else 0])
                    for m in c.get('vs', []):
                        mi = cand_idx.get(m['sqcand'])
                        if mi is not None:
                            chapa[mi] = (ci, {'v': 'Vice', 'vp': 'Vice', 'vg': 'Vice', 's1': '1º Suplente',
                                              's2': '2º Suplente'}.get(m['tp'], CHAPA[CARGOS[cands[mi][5]][1]][1]))
        v = d['v']
        abr_tot.append([uf_idx[uf], cgi, int(v['vnom']), int(v['vb']), int(v['tvn'])])

for i, c in enumerate(cands):
    ds = CARGOS[c[5]][1]
    if ds not in CHAPA or i in chapa:
        continue
    pai, tp = CHAPA[ds]
    opts = titulares.get((c[6], pai, c[1]), [])
    if opts:
        t = min(opts, key=lambda j: abs(int(cands[j][0]) - int(c[0])))
        chapa[i] = (t, tp)
composicao = sorted([[t, m, tp] for m, (t, tp) in chapa.items()])

# ---------------- validações ----------------
assert len({(r_[0], r_[1]) for r_ in res}) == len(res), 'PK RESULTADO duplicada'
assert len({(v[0], v[1]) for v in votos}) == len(votos), 'PK VOTACAO duplicada'
assert len(cand_idx) == len(cands), 'sq_candidato duplicado'
membros_sem_titular = sum(1 for i, c in enumerate(cands) if CARGOS[c[5]][1] in CHAPA and i not in chapa)

out = {
    'meta': {'ano': 2026, 'turno': 1, 'dt_eleicao': '2026-10-04', 'dt_carga': dt_carga},
    'regiao': regioes, 'uf': ufs, 'municipio': muns, 'cargo': CARGOS, 'partido': partidos,
    'candidatura_cols': CAND_COLS, 'candidatura': cands,
    'composicao_chapa': composicao,
    'votacao_candidato_cols': ['candidatura', 'uf', 'qt_votos', 'pc_votos_validos', 'nr_ordem', 'st_voto_valido'],
    'votacao_candidato': votos,
    'resultado_cols': ['municipio', 'cargo'] + RES_COLS, 'resultado': res,
    'abrangencia_tse': abr_tot,
}
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, separators=(',', ':'))

print('regioes', len(regioes), 'ufs', len(ufs), 'municipios', len(muns), 'resultados', len(res))
print('partidos', len(partidos), 'candidaturas', len(cands), 'chapa', len(composicao),
      'membros sem titular', membros_sem_titular)
print('votacao', len(votos), 'sq nao encontrados', miss)
print('sem nome de partido:', [p[0] for p in partidos if p[0] == p[1]])
# conferência: votos nominais por UF/cargo (detalhe) x soma dos candidatos (JSON)
det = Counter()
for r_ in res:
    det[(muns[r_[0]][2], r_[1])] += r_[6]
det_br = Counter()
for (u, cg), q in det.items():
    det_br[cg] += q
soma = Counter()
for v in votos:
    if v[5]:
        soma[(v[1], cands[v[0]][5])] += v[2]
dif = []
for u, cg, vnom, _, _ in abr_tot:
    ref = det_br[cg] if ufs[u][0] == 'BR' else det[(u, cg)]
    dif.append((ufs[u][0], CARGOS[cg][1], vnom, ref, soma[(u, cg)]))
bad = [x for x in dif if not (x[2] == x[3])]
print('abrangencias', len(dif), 'divergencias vnom(JSON) x nominais(detalhe):', len(bad), bad[:5])
bad2 = [x for x in dif if abs(x[4] - x[2]) > 0]
print('divergencias soma candidatos x vnom:', len(bad2), bad2[:5])
print('tamanho', os.path.getsize(OUT) // 1024, 'KB')
