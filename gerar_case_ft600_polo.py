# -*- coding: utf-8 -*-
"""
gerar_case_ft600_polo.py
Modelagem Paramétrica 3D (Blender / bpy) — Carenagem Estilo FuelTech FT600 (4.3")
Projeto: Painel Digital de Telemetria VW Polo Track 2026 (ESP32-S3 Guition JC4827W543C)

Unidades: 1 unidade Blender = 1.0 mm
Peças geradas (3 etapas separadas, otimizadas para impressão 3D FDM em PETG/ABS sem pintura):
  - Etapa 1: 01_tampa_frontal  (Preto Fosco - Somente 10 LEDs 5mm de kit comum no topo)
  - Etapa 2: 02_anel_vermelho  (Vermelho Vibrante - Friso assinatura FT600 com encaixe macho/fêmea)
  - Etapa 3: 03_tampa_traseira (Preto Fosco - Berços p/ SN65HVD230, Step-Down MP1584, Buzzer 12mm e GX16-4P)
  + Coleção 04_Componentes_Internos (Todos os componentes reais modelados em 3D para auditoria física de espaço)
"""

import bpy
import bmesh
import math
import os
from mathutils import Vector, Matrix

# ==============================================================================
# 1. PARÂMETROS DIMENSIONAIS (TODOS EM MILÍMETROS - 1 UNIDADE = 1 MM)
# ==============================================================================

# --- Dimensões Globais da Carcaça (Recalibradas para caber PCB + LEDs 5mm + Plugues JST com folga real) ---
CASE_W = 154.0              # Largura externa total (eixo X) - comporta PCB 120mm + plugue P1/USB-C + paredes
CASE_H = 105.0              # Altura externa total (eixo Y) - comporta canal JST inferior (10.9mm) + PCB (70.2mm) + LEDs 5mm no topo
CASE_D = 35.0               # Profundidade externa total do corpo (eixo Z, sem contar pés traseiros)

CORNER_R = 14.0             # Raio dos 4 cantos arredondados
ARCH_TOP_SAG = 3.2          # Flecha do arco convexo superior (estilo FT600)
ARCH_BOT_SAG = 2.0          # Flecha do arco convexo inferior (estilo FT600)
ARCH_SIDE_SAG = 1.2         # Flecha do arco convexo lateral esquerdo/direito

TOLERANCE_3D = 0.4          # Folga geral para impressão 3D (FDM ABS/PETG)
WALL_MIN = 3.0              # Espessura mínima de parede estrutural (3.0 mm para alta resistência térmica no painel)
FLOOR_THICK = 3.0           # Espessura da parede de fundo da tampa traseira

# --- Divisão Longitudinal (Eixo Z) das 3 Etapas ---
# Z = +17.5 (frente da tampa frontal) até Z = -17.5 (costas da tampa traseira)
FRONT_DEPTH = 12.0          # Profundidade da 01_tampa_frontal (Z: +5.5 a +17.5)
RING_THICK = 3.0            # Espessura axial do 02_anel_vermelho (Z: +2.5 a +5.5)
REAR_DEPTH = 20.0           # Profundidade da 03_tampa_traseira (Z: -17.5 a +2.5)

# --- Aba Frontal / Moldura Chanfrada Anti-Sol ---
VISOR_DEPTH = 5.0           # Recuo chanfrado de 5 mm ao redor do vidro (aba anti-sol)
BEZEL_RIM_W = 5.2           # Largura da borda externa antes do chanfro da aba
FRONT_PANEL_THICK = 2.2     # Espessura da parede frontal entre o fundo do chanfro e o vidro do LCD

# --- Placa Guition JC4827W543 (ESP32-S3 4.3") ---
PCB_W_TOTAL = 120.0         # Largura total do PCB incluindo as 4 orelhas de fixação (R1.6)
PCB_W_BODY = 105.8          # Largura do corpo retangular do PCB/LCD (sem as orelhas)
PCB_H = 70.2                # Altura total do PCB
PCB_EAR_H = 7.4             # Altura de cada uma das 4 orelhas de fixação nos cantos do PCB
PCB_THICK = 1.6             # Espessura da fibra do PCB
LCD_THICK = 3.1             # Espessura do módulo LCD + Touch Capacitivo GT911 na frente do PCB
PCB_HOLE_DX = 112.6         # Distância X centro-a-centro entre os 4 furos de fixação do PCB
PCB_HOLE_DY = 62.1          # Distância Y centro-a-centro entre os 4 furos de fixação do PCB
PCB_OFFSET_Y = -5.5         # Deslocamento Y do PCB: libera +15.0 mm no topo p/ LEDs 5mm e +11.4 mm na base p/ cabos JST!

# --- Área Visível da Tela IPS 4.3" ---
SCREEN_VIS_W = 95.04        # Largura ativa da tela IPS 480x272
SCREEN_VIS_H = 53.86        # Altura ativa da tela IPS 480x272
WINDOW_W = round(SCREEN_VIS_W + TOLERANCE_3D, 2)   # 95.44 mm
WINDOW_H = round(SCREEN_VIS_H + TOLERANCE_3D, 2)   # 54.26 mm

# --- Barra de Shift Light Superior: 10x LEDs 5mm Comuns de Kit (Verde, Vermelho, Azul - APENAS NO TOPO) ---
SHIFT_LED_COUNT = 10        # 10 LEDs difusos de 5mm no topo (ex: 4 Verdes, 3 Vermelhos, 3 Azuis)
LED5MM_DOME_DIA = 5.0       # Diâmetro nominal do corpo/lente do LED de 5mm comum
LED5MM_HOLE_DIA = 5.25      # Furo frontal passante (5.0 mm + 0.25 mm de folga para encaixe suave)
LED5MM_FLANGE_DIA = 5.9     # Diâmetro do colarinho (aba base) do LED de 5mm comum
LED5MM_SOCKET_DIA = 6.4     # Alojamento traseiro escalonado p/ travar o colarinho do LED 5mm (parede entre furos = 1.8 mm)
LED5MM_BODY_LEN = 8.6       # Comprimento total da cápsula plástica do LED 5mm
LED5MM_STOP_THICK = 2.6     # Espessura do batente frontal (deixa a ponta redonda do LED 5mm aflorar ~2.2 mm na frente)
SHIFT_LED_PITCH = 8.2       # Espaçamento centro-a-centro entre os 10 LEDs de 5mm (9 x 8.2 = 73.8 mm total)
SHIFT_LED_Y = 38.0          # Altura Y central da barra de LEDs no arco superior (8.4 mm acima da borda superior do PCB!)
SHIFT_LED_ARCH = 1.6        # Curvatura suave em arco acompanhando o topo da FT600
LED_CHANNEL_W = 86.0        # Comprimento da canaleta traseira para os terminais/resistores dos 10 LEDs 5mm
LED_CHANNEL_H = 10.8        # Largura (altura Y) da canaleta traseira dos LEDs 5mm
LED_CHANNEL_D = 4.6         # Profundidade da canaleta traseira na tampa frontal

# --- Torres Internas de Fixação (PCB M3 e Fechamento da Carcaça M3) ---
M3_INSERT_DIA = 4.2         # Furo para inserto metálico térmico M3 (OD ~4.2-4.5 mm)
M3_THROUGH_DIA = 3.4        # Furo passante para parafuso M3 na tampa traseira
M3_HEAD_DIA = 6.2           # Escareado para cabeça cilíndrica Allen M3
PCB_BOSS_OD = 7.8           # Diâmetro externo das 4 torres do PCB
CASE_BOSS_OD = 9.0          # Diâmetro externo das 4 torres de fechamento nos cantos
CASE_BOSS_DX = 134.0        # Distância X entre as 4 torres de fechamento da carcaça (nos 4 cantos extremos)
CASE_BOSS_DY = 78.0         # Distância Y entre as 4 torres de fechamento da carcaça

# --- Anel Vermelho Central (02_anel_vermelho) ---
RING_PROTRUSION = 0.5       # Ressalto externo do friso vermelho (+0.5 mm além do contorno)
RING_WALL_W = 3.6           # Espessura radial do anel vermelho
RING_LIP_H = 1.4            # Altura axial do degrau macho/fêmea de alinhamento
RING_LIP_W = 1.5            # Largura radial do degrau de encaixe

# --- Tampa Traseira (03_tampa_traseira) ---
# Vão livre atrás do PCB: de Z = +3.9 (costas do PCB) até Z = -14.5 (piso interno traseiro) = 18.4 mm livres!
REAR_FOOT_OD = 10.0         # Diâmetro dos 4 pés/torres traseiros de fixação
REAR_FOOT_H = 6.0           # Altura dos 4 pés traseiros
REAR_FOOT_HOLE_DIA = 5.2    # Furo Ø 5.2 mm para inserto M4 nos 4 pés traseiros
REAR_FOOT_DX = 110.0        # Distância X dos 4 pés traseiros M4 (livres dos parafusos M3 de canto)
REAR_FOOT_DY = 60.0         # Distância Y dos 4 pés traseiros M4

# --- Aletas Laterais e Ventilação Traseira ---
SIDE_RIB_COUNT = 5          # 5 aletas/nervuras verticais em baixo-relevo em cada lateral
SIDE_RIB_W = 1.8            # Largura Z de cada nervura
SIDE_RIB_DEPTH = 1.6        # Profundidade X do baixo-relevo na lateral
SIDE_RIB_SPACING = 3.1      # Passo no eixo Z entre as 5 nervuras
VENT_SLOT_H = 36.0          # Comprimento vertical dos 2 rasgos de ventilação por lado
VENT_SLOT_W = 1.5           # Abertura Z do rasgo

# --- Baia Rebaixada Traseira e Conector GX16-4P ---
REAR_BAY_W = 45.0           # Largura da baia rebaixada centro-inferior traseira
REAR_BAY_H = 24.0           # Altura da baia rebaixada centro-inferior traseira
REAR_BAY_DEPTH = 2.2        # Profundidade do rebaixo externo da baia traseira
REAR_BAY_Y = -20.0          # Posição Y do centro da baia traseira
GX16_HOLE_DIA = 16.2        # Furo circular Ø 16.2 mm para conector de painel GX16-4P

# --- Recortes Periféricos (USB-C na Direita e MicroSD na Base) ---
USBC_CUT_W = 3.8            # Altura Z do rasgo para acesso ao conector USB-C
USBC_CUT_H = 12.0           # Largura Y do rasgo USB-C na lateral direita
USBC_OFFSET_Y = PCB_OFFSET_Y + 3.5  # Alinhado ao conector USB1 da JC4827W543

SD_CUT_W = 17.0             # Largura X do rasgo para cartão microSD (slot TF) na base
SD_CUT_H = 3.6              # Altura Z do rasgo microSD
SD_OFFSET_X = -27.5         # Alinhado ao slot TF1 na borda inferior da JC4827W543

# --- Berços Internos Snap-Fit para Todos os Componentes Traseiros ---
# 1) Módulo Transceiver CAN SN65HVD230 (16.5 x 14.5 x 6.0 mm) - Lado Direito Superior/Centro
CAN_W = 16.5
CAN_H = 14.5
CAN_D = 6.0
CAN_CRADLE_X = 40.0         # Lado direito traseiro (longe da antena Wi-Fi na esquerda X < 0)
CAN_CRADLE_Y = 14.0         # Região centro-direita interna
CAN_CRADLE_WALL = 1.8
CAN_CRADLE_H = 5.5

# 2) Módulo Conversor Step-Down DC-DC MP1584EN (22.0 x 17.0 x 4.5 mm) - Lado Esquerdo Inferior
STEPDOWN_W = 22.0
STEPDOWN_H = 17.0
STEPDOWN_D = 4.5
STEPDOWN_X = -40.0          # Abaixo da região da antena do ESP32-S3 e à esquerda da baia GX16
STEPDOWN_Y = -18.0
STEPDOWN_WALL = 1.8
STEPDOWN_CRADLE_H = 4.8

# 3) Buzzer Piezo 12mm para saída Speak (P7) - Lado Centro-Esquerdo Superior
BUZZER_DIA = 12.0
BUZZER_H = 7.5
BUZZER_X = -15.0
BUZZER_Y = 16.0
BUZZER_WALL = 1.6

# --- Logo SchutzMachine (SVG Vetorial em Baixo-Relevo na Frente e na Traseira) ---
LOGO_SVG_PATH = r"c:\Users\ryhan\Documents\schutzmachine\SchutzMachine_monocromatica.svg"
FRONT_LOGO_W = 58.0         # Largura da logo na moldura inferior frontal (mm)
FRONT_LOGO_Y = -37.8        # Posição Y abaixo da tela 4.3"
FRONT_LOGO_DEPTH = 0.6      # Profundidade do baixo-relevo frontal (ideal p/ bico 0.4 mm sem suportes)
REAR_LOGO_W = 82.0          # Largura da logo na tampa traseira (mm)
REAR_LOGO_Y = 14.0          # Posição Y acima da baia do conector GX16-4P
REAR_LOGO_DEPTH = 0.8       # Profundidade do baixo-relevo traseiro (deixa 2.2 mm de parede sólida)



# ==============================================================================
# 2. FUNÇÕES GEOMÉTRICAS E PERFIL CONVEXO ESTILO FT600
# ==============================================================================

def ft600_contour_points(width, height, corner_r, sag_top, sag_bot, sag_side, n_corner=12, n_edge=20):
    hw = width / 2.0
    hh = height / 2.0
    r = min(corner_r, hw - 2.0, hh - 2.0)
    cx = hw - r
    cy = hh - r

    pts = []
    corners = [
        ( cx,  cy, 0.0,           math.pi * 0.5),
        (-cx,  cy, math.pi * 0.5, math.pi),
        (-cx, -cy, math.pi,       math.pi * 1.5),
        ( cx, -cy, math.pi * 1.5, math.pi * 2.0),
    ]

    for idx, (ox, oy, a0, a1) in enumerate(corners):
        for i in range(n_corner):
            t = i / float(n_corner)
            ang = a0 + t * (a1 - a0)
            x = ox + r * math.cos(ang)
            y = oy + r * math.sin(ang)
            nx = max(-1.0, min(1.0, x / cx)) if cx > 0 else 0.0
            ny = max(-1.0, min(1.0, y / cy)) if cy > 0 else 0.0
            if y > 0:
                y += sag_top * max(0.0, 1.0 - nx * nx) * math.sin(ang)
            else:
                y -= sag_bot * max(0.0, 1.0 - nx * nx) * (-math.sin(ang))
            x += math.copysign(sag_side * max(0.0, 1.0 - ny * ny) * abs(math.cos(ang)), x)
            pts.append((x, y))

        next_ox, next_oy, next_a0, _ = corners[(idx + 1) % 4]
        p_start_x = ox + r * math.cos(a1)
        p_start_y = oy + r * math.sin(a1)
        p_end_x = next_ox + r * math.cos(next_a0)
        p_end_y = next_oy + r * math.sin(next_a0)

        for j in range(1, n_edge):
            u = j / float(n_edge)
            x = p_start_x + u * (p_end_x - p_start_x)
            y = p_start_y + u * (p_end_y - p_start_y)
            bulge = math.sin(u * math.pi)
            if idx == 0:
                y += sag_top * bulge
            elif idx == 1:
                x -= sag_side * bulge
            elif idx == 2:
                y -= sag_bot * bulge
            elif idx == 3:
                x += sag_side * bulge
            pts.append((x, y))

    return pts


def rounded_rect_points(width, height, radius, cx_off=0.0, cy_off=0.0, n_corner=10):
    hw = width / 2.0
    hh = height / 2.0
    r = max(0.2, min(radius, hw - 0.1, hh - 0.1))
    ix = hw - r
    iy = hh - r
    corners = [
        ( cx_off + ix, cy_off + iy, 0.0,           math.pi * 0.5),
        ( cx_off - ix, cy_off + iy, math.pi * 0.5, math.pi),
        ( cx_off - ix, cy_off - iy, math.pi,       math.pi * 1.5),
        ( cx_off + ix, cy_off - iy, math.pi * 1.5, math.pi * 2.0),
    ]
    pts = []
    for ox, oy, a0, a1 in corners:
        for i in range(n_corner + 1):
            ang = a0 + (i / float(n_corner)) * (a1 - a0)
            pts.append((ox + r * math.cos(ang), oy + r * math.sin(ang)))
    return pts


def create_extruded_profile_obj(name, pts_2d, z0, z1, collection):
    mesh = bpy.data.meshes.new(name + "_Mesh")
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)

    bm = bmesh.new()
    v_bot = [bm.verts.new((x, y, z0)) for (x, y) in pts_2d]
    v_top = [bm.verts.new((x, y, z1)) for (x, y) in pts_2d]
    bm.verts.ensure_lookup_table()

    n = len(pts_2d)
    for i in range(n):
        ni = (i + 1) % n
        bm.faces.new((v_bot[i], v_bot[ni], v_top[ni], v_top[i]))

    bm.faces.new(reversed(v_bot))
    bm.faces.new(v_top)

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    return obj


def create_ring_loft_obj(name, outer_layers, inner_layers, collection):
    mesh = bpy.data.meshes.new(name + "_Mesh")
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)

    bm = bmesh.new()
    n_pts = len(outer_layers[0][0])

    out_rings = []
    for pts, z_val in outer_layers:
        ring = [bm.verts.new((x, y, z_val if isinstance(z_val, (int, float)) else z_val(x, y))) for (x, y) in pts]
        out_rings.append(ring)

    in_rings = []
    for pts, z_val in inner_layers:
        ring = [bm.verts.new((x, y, z_val if isinstance(z_val, (int, float)) else z_val(x, y))) for (x, y) in pts]
        in_rings.append(ring)

    bm.verts.ensure_lookup_table()

    for k in range(len(out_rings) - 1):
        r0, r1 = out_rings[k], out_rings[k + 1]
        for i in range(n_pts):
            ni = (i + 1) % n_pts
            bm.faces.new((r0[i], r0[ni], r1[ni], r1[i]))

    for k in range(len(in_rings) - 1):
        r0, r1 = in_rings[k], in_rings[k + 1]
        for i in range(n_pts):
            ni = (i + 1) % n_pts
            bm.faces.new((r1[i], r1[ni], r0[ni], r0[i]))

    for i in range(n_pts):
        ni = (i + 1) % n_pts
        bm.faces.new((out_rings[0][ni], out_rings[0][i], in_rings[0][i], in_rings[0][ni]))

    for i in range(n_pts):
        ni = (i + 1) % n_pts
        bm.faces.new((out_rings[-1][i], out_rings[-1][ni], in_rings[-1][ni], in_rings[-1][i]))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    return obj


def make_box(name, size_xyz, center_xyz, collection):
    mesh = bpy.data.meshes.new(name + "_Mesh")
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size_xyz, verts=bm.verts)
    bmesh.ops.translate(bm, vec=center_xyz, verts=bm.verts)
    bm.to_mesh(mesh)
    bm.free()
    return obj


def make_cylinder(name, radius, depth, center_xyz, collection, segments=32):
    mesh = bpy.data.meshes.new(name + "_Mesh")
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=segments,
        radius1=radius,
        radius2=radius,
        depth=depth,
    )
    bmesh.ops.translate(bm, vec=center_xyz, verts=bm.verts)
    bm.to_mesh(mesh)
    bm.free()
    return obj


def apply_boolean(target_obj, cutter_obj, operation='DIFFERENCE', solver='EXACT', use_self=False):
    bpy.context.view_layer.objects.active = target_obj
    mod = target_obj.modifiers.new(name=f"Bool_{cutter_obj.name}", type='BOOLEAN')
    mod.operation = operation
    mod.solver = solver
    if solver == 'EXACT' and use_self:
        mod.use_self = True
    mod.object = cutter_obj
    bpy.ops.object.modifier_apply(modifier=mod.name)
    mesh_data = cutter_obj.data
    bpy.data.objects.remove(cutter_obj, do_unlink=True)
    if mesh_data and mesh_data.users == 0:
        bpy.data.meshes.remove(mesh_data)


def assign_single_material(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    for poly in obj.data.polygons:
        poly.material_index = 0


def create_svg_logo_cutter(name, svg_path, target_width, center_xy, z_min, z_max, collection, mirror_x=False):
    """
    Importa o SVG vetorial da logo SchutzMachine, converte para malha 3D sólida fechada
    e posiciona em (center_xy, z_min..z_max) para gravação em baixo-relevo (boolean DIFFERENCE).
    """
    if not os.path.exists(svg_path):
        print(f"Aviso: SVG não encontrado em {svg_path}")
        return None

    before = set(bpy.data.objects)
    bpy.ops.import_curve.svg(filepath=svg_path)
    imported = list(set(bpy.data.objects) - before)
    if not imported:
        return None

    # Remove coleções extras criadas pelo importador de SVG e move os objetos para col_tmp
    svg_cols = set()
    mesh_objs = []
    for obj in imported:
        for c in list(obj.users_collection):
            if c != collection:
                svg_cols.add(c)
                c.objects.unlink(obj)
        if obj.name not in collection.objects:
            collection.objects.link(obj)

        if obj.type == 'CURVE':
            obj.data.resolution_u = 2
            obj.data.dimensions = '2D'
            obj.data.fill_mode = 'BOTH'
            # Extrusão nativa da Curve gera sólido 100% fechado (tampa superior + inferior + paredes = 0 boundary edges)
            obj.data.extrude = 0.005
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.convert(target='MESH')
            mesh_objs.append(bpy.context.active_object)

    for c in svg_cols:
        if len(c.objects) == 0:
            bpy.data.collections.remove(c)

    if not mesh_objs:
        return None

    # Une todos os paths da logo num único objeto Mesh
    bpy.ops.object.select_all(action='DESELECT')
    for m in mesh_objs:
        m.select_set(True)
    bpy.context.view_layer.objects.active = mesh_objs[0]
    if len(mesh_objs) > 1:
        bpy.ops.object.join()
    logo_obj = bpy.context.active_object
    logo_obj.name = name

    # Normaliza escala em milímetros, centraliza em XY e mapeia Z exatamente para [z_min, z_max]
    bm = bmesh.new()
    bm.from_mesh(logo_obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)

    xs = [v.co.x for v in bm.verts]
    ys = [v.co.y for v in bm.verts]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    w = max_x - min_x
    cx = (min_x + max_x) / 2.0
    cy = (min_y + max_y) / 2.0
    scale = target_width / w if w > 1e-6 else 1.0

    # Mapeia sempre primeiro sem espelhamento (100% validado na frontal) centrado na origem
    half_h = (z_max - z_min) / 2.0
    z_mid = (z_min + z_max) / 2.0
    for v in bm.verts:
        nx = (v.co.x - cx) * scale
        ny = (v.co.y - cy) * scale
        nz = half_h if v.co.z > 0.0 else -half_h
        v.co = Vector((nx, ny, nz))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    if mirror_x:
        # Rotação rígida de 180° em torno de Y (mantém +Y para cima, espelha X para leitura correta por trás, preserva normais 100%)
        bmesh.ops.rotate(bm, cent=(0.0, 0.0, 0.0), matrix=Matrix.Rotation(math.pi, 3, 'Y'), verts=bm.verts)

    bmesh.ops.translate(bm, verts=bm.verts, vec=(center_xy[0], center_xy[1], z_mid))
    bm.to_mesh(logo_obj.data)
    bm.free()
    logo_obj.location = (0.0, 0.0, 0.0)
    logo_obj.scale = (1.0, 1.0, 1.0)
    logo_obj.rotation_euler = (0.0, 0.0, 0.0)
    return logo_obj



# ==============================================================================
# 3. MATERIAIS DE VISUALIZAÇÃO
# ==============================================================================

def create_materials():
    def build_mat(name, color, metallic=0.0, roughness=0.4, emission=None, em_strength=0.0):
        mat = bpy.data.materials.get(name)
        if not mat:
            mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Roughness"].default_value = roughness
        if emission and "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
            bsdf.inputs["Emission Strength"].default_value = em_strength
        mat.diffuse_color = (*color, 1.0)
        return mat

    return {
        "preto_fosco": build_mat("FT_PETG_Preto_Fosco", (0.045, 0.048, 0.055), metallic=0.08, roughness=0.38),
        "vermelho_ft": build_mat("FT_PETG_Vermelho_Vibrante", (0.88, 0.02, 0.02), metallic=0.18, roughness=0.22),
        "vidro_tela":  build_mat("FT_Vidro_Display_43", (0.01, 0.015, 0.025), metallic=0.1, roughness=0.05,
                                 emission=(0.02, 0.12, 0.25), em_strength=0.35),
        "pcb_preto":   build_mat("Guition_PCB_Preto", (0.025, 0.025, 0.03), metallic=0.15, roughness=0.3),
        "can_azul":    build_mat("SN65HVD230_PCB_Azul", (0.04, 0.25, 0.72), metallic=0.15, roughness=0.3),
        "step_verde":  build_mat("MP1584_PCB_Verde", (0.04, 0.48, 0.18), metallic=0.15, roughness=0.3),
        "metal":       build_mat("Metal_Componentes", (0.75, 0.77, 0.80), metallic=0.85, roughness=0.22),
        "jst_branco":  build_mat("JST_Conector_Branco", (0.88, 0.88, 0.84), metallic=0.0, roughness=0.35),
        "led_verde":   build_mat("LED5mm_Verde", (0.05, 0.95, 0.15), roughness=0.12, emission=(0.05, 1.0, 0.15), em_strength=4.0),
        "led_vermelho":build_mat("LED5mm_Vermelho", (1.0, 0.03, 0.02), roughness=0.12, emission=(1.0, 0.03, 0.02), em_strength=4.2),
        "led_azul":    build_mat("LED5mm_Azul", (0.05, 0.45, 1.0), roughness=0.12, emission=(0.05, 0.45, 1.0), em_strength=4.2),
    }


# ==============================================================================
# 4. CONSTRUÇÃO DAS 3 PEÇAS + COMPONENTES INTERNOS + AUDITORIA DE ESPAÇO
# ==============================================================================

def build_ft600_polo_case():
    bpy.ops.object.select_all(action='DESELECT')
    for obj in list(bpy.data.objects):
        if obj.type in {'MESH', 'CURVE', 'TEXT', 'EMPTY', 'LIGHT', 'CAMERA'}:
            bpy.data.objects.remove(obj, do_unlink=True)

    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 0.001
    scene.unit_settings.length_unit = 'MILLIMETERS'

    def ensure_col(name, parent=scene.collection):
        c = bpy.data.collections.get(name)
        if not c:
            c = bpy.data.collections.new(name)
        if c.name not in parent.children:
            parent.children.link(c)
        return c

    col_etapa1 = ensure_col("Etapa_01_Tampa_Frontal")
    col_etapa2 = ensure_col("Etapa_02_Anel_Vermelho")
    col_etapa3 = ensure_col("Etapa_03_Tampa_Traseira")
    col_ref    = ensure_col("04_Componentes_Internos")
    col_tmp    = ensure_col("_Bool_Temp")

    mats = create_materials()

    # Planos Z da montagem (centro em Z=0):
    z_front_face  = CASE_D / 2.0                          # +17.5 mm
    z_front_split = z_front_face - FRONT_DEPTH            # +5.5 mm
    z_rear_split  = z_front_split - RING_THICK            # +2.5 mm
    z_rear_back   = -CASE_D / 2.0                         # -17.5 mm
    z_rear_floor  = z_rear_back + FLOOR_THICK             # -14.5 mm

    # Posição Z do PCB da Guition JC4827W543:
    # Fundo do chanfro da viseira = +12.5 mm
    # Parede frontal da moldura = 2.2 mm -> Face do vidro LCD encosta em Z = +10.3 mm
    # Módulo LCD+Touch (3.1 mm) vai de Z = +7.2 a +10.3 mm (folga de +0.2 mm -> assento do PCB em Z = +7.0 mm)
    # Wait: se as 4 torres do PCB terminam em Z = +5.5 mm (plano de divisão da tampa frontal),
    # o módulo LCD+Touch (3.1 mm) fica alojado num rebaixo de 3.3 mm (Z: +5.5 a +8.8 mm),
    # e a parede frontal da moldura vai de Z = +8.8 a +12.5 mm (3.7 mm de espessura sólida!).
    z_pcb_front = z_front_split                           # +5.5 mm (face frontal do PCB apoia nas 4 torres da tampa frontal)
    z_pcb_back  = z_pcb_front - PCB_THICK                 # +3.9 mm (face traseira do PCB)
    z_lcd_front = z_pcb_front + LCD_THICK + 0.2           # +8.8 mm (topo do bolso do LCD na tampa frontal)
    z_visor_floor = z_front_face - VISOR_DEPTH            # +12.5 mm (fundo externo da aba anti-sol)

    N_CORNER = 12
    N_EDGE = 20
    pts_outer = ft600_contour_points(
        CASE_W, CASE_H, CORNER_R, ARCH_TOP_SAG, ARCH_BOT_SAG, ARCH_SIDE_SAG, N_CORNER, N_EDGE
    )
    pts_inner_cavity = ft600_contour_points(
        CASE_W - 2.0 * WALL_MIN, CASE_H - 2.0 * WALL_MIN, CORNER_R - WALL_MIN,
        ARCH_TOP_SAG * 0.82, ARCH_BOT_SAG * 0.82, ARCH_SIDE_SAG * 0.82, N_CORNER, N_EDGE
    )

    # ==========================================================================
    # ETAPA 1: 01_tampa_frontal (Preto Fosco - SOMENTE 10 LEDs 5mm NO TOPO)
    # ==========================================================================
    obj_front = create_extruded_profile_obj("01_tampa_frontal", pts_outer, z_front_split, z_front_face, col_etapa1)

    # 1.1 Moldura frontal chanfrada para dentro (aba anti-sol de 5.0 mm)
    pts_visor_outer = ft600_contour_points(
        CASE_W - 2.0 * BEZEL_RIM_W, CASE_H - 2.0 * BEZEL_RIM_W, CORNER_R - BEZEL_RIM_W * 0.8,
        ARCH_TOP_SAG * 0.78, ARCH_BOT_SAG * 0.78, ARCH_SIDE_SAG * 0.78, N_CORNER, N_EDGE
    )
    pts_visor_inner = ft600_contour_points(
        CASE_W - 2.0 * (BEZEL_RIM_W + 4.2), CASE_H - 2.0 * (BEZEL_RIM_W + 4.2), CORNER_R - (BEZEL_RIM_W + 3.5),
        ARCH_TOP_SAG * 0.55, ARCH_BOT_SAG * 0.55, ARCH_SIDE_SAG * 0.55, N_CORNER, N_EDGE
    )
    mesh_visor = bpy.data.meshes.new("Visor_Cut_Mesh")
    cut_visor = bpy.data.objects.new("Cut_Visor", mesh_visor)
    col_tmp.objects.link(cut_visor)
    bm = bmesh.new()
    v_in = [bm.verts.new((x, y, z_visor_floor)) for (x, y) in pts_visor_inner]
    v_out = [bm.verts.new((x, y, z_front_face + 0.5)) for (x, y) in pts_visor_outer]
    n_v = len(pts_visor_outer)
    for i in range(n_v):
        ni = (i + 1) % n_v
        bm.faces.new((v_in[i], v_in[ni], v_out[ni], v_out[i]))
    bm.faces.new(reversed(v_in))
    bm.faces.new(v_out)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh_visor)
    bm.free()
    apply_boolean(obj_front, cut_visor, 'DIFFERENCE')

    # 1.2 Janela central recortada para a área visível da tela (95.44 x 54.26 mm)
    cut_win = make_box(
        "Cut_Screen_Window",
        (WINDOW_W, WINDOW_H, FRONT_DEPTH + 4.0),
        (0.0, PCB_OFFSET_Y, z_front_split + FRONT_DEPTH / 2.0),
        col_tmp,
    )
    apply_boolean(obj_front, cut_win, 'DIFFERENCE')

    # 1.3 Berço traseiro escalonado na tampa frontal para o vidro do LCD/Touch (106.6 x 71.0 mm, Z: +5.5 a +8.8 mm)
    lcd_pocket_h = z_lcd_front - z_front_split
    cut_lcd_body = make_box(
        "Cut_LCD_Body",
        (PCB_W_BODY + TOLERANCE_3D * 2.0, PCB_H + TOLERANCE_3D * 2.0, lcd_pocket_h + 0.4),
        (0.0, PCB_OFFSET_Y, z_front_split + lcd_pocket_h / 2.0 - 0.2),
        col_tmp,
    )
    apply_boolean(obj_front, cut_lcd_body, 'DIFFERENCE')

    # Alívio interno da tampa frontal (Z: +5.5 a +8.2 mm) preservando paredes e região das torres
    pts_front_hollow = ft600_contour_points(
        CASE_W - 2.0 * (WALL_MIN + 1.2), CASE_H - 2.0 * (WALL_MIN + 1.2), CORNER_R - (WALL_MIN + 1.2),
        ARCH_TOP_SAG * 0.75, ARCH_BOT_SAG * 0.75, ARCH_SIDE_SAG * 0.75, N_CORNER, N_EDGE
    )
    cut_front_hollow = create_extruded_profile_obj(
        "Cut_Front_Hollow", pts_front_hollow, z_front_split - 0.5, z_front_split + 2.5, col_tmp
    )
    apply_boolean(obj_front, cut_front_hollow, 'DIFFERENCE')

    # 1.4 Barra de Shift Light no topo para 10x LEDs de 5mm comuns (Verde, Vermelho, Azul - APENAS NO TOPO)
    # Canaleta traseira para os terminais e fios dos 10 LEDs 5mm (Z: +5.5 a +8.2 mm)
    cut_led_channel = make_box(
        "Cut_LED5mm_Channel",
        (LED_CHANNEL_W, LED_CHANNEL_H, 2.8),
        (0.0, SHIFT_LED_Y, z_front_split + 1.3),
        col_tmp,
    )
    apply_boolean(obj_front, cut_led_channel, 'DIFFERENCE')

    # 10 furos escalonados para LED 5mm comum:
    # - Furo frontal passante Ø 5.25 mm (para a lente cilíndrica de 5.0 mm do LED)
    # - Alojamento traseiro Ø 6.40 mm até Z = z_visor_floor - 2.0 mm (para encaixar o colarinho de 5.9 mm do LED 5mm!)
    led_positions = []
    z_socket_top = z_visor_floor - 1.8  # Batente interno onde o colarinho do LED 5mm encosta
    socket_depth = (z_socket_top - z_front_split) + 1.0

    for i in range(SHIFT_LED_COUNT):
        norm_idx = (i - (SHIFT_LED_COUNT - 1) / 2.0)
        lx = norm_idx * SHIFT_LED_PITCH
        u_arch = lx / (4.5 * SHIFT_LED_PITCH)
        ly = SHIFT_LED_Y + SHIFT_LED_ARCH * (1.0 - u_arch * u_arch)
        led_positions.append((lx, ly))

        # Furo passante Ø 5.25 mm para o corpo de 5mm do LED
        cut_led_dome = make_cylinder(
            f"Cut_LED5mm_Dome_{i+1:02d}",
            LED5MM_HOLE_DIA / 2.0,
            FRONT_DEPTH + 4.0,
            (lx, ly, z_front_split + FRONT_DEPTH / 2.0),
            col_tmp,
            segments=28,
        )
        apply_boolean(obj_front, cut_led_dome, 'DIFFERENCE')

        # Rebaixo traseiro Ø 6.4 mm para o colarinho (flange) do LED 5mm
        cut_led_flange = make_cylinder(
            f"Cut_LED5mm_Flange_{i+1:02d}",
            LED5MM_SOCKET_DIA / 2.0,
            socket_depth,
            (lx, ly, z_socket_top - socket_depth / 2.0),
            col_tmp,
            segments=28,
        )
        apply_boolean(obj_front, cut_led_flange, 'DIFFERENCE')

    # 1.5 Degrau traseiro de alinhamento (encaixe com o 02_anel_vermelho)
    pts_lip_outer = ft600_contour_points(
        CASE_W - 2.0 * (RING_WALL_W - RING_LIP_W - TOLERANCE_3D * 0.5),
        CASE_H - 2.0 * (RING_WALL_W - RING_LIP_W - TOLERANCE_3D * 0.5),
        CORNER_R - (RING_WALL_W - RING_LIP_W),
        ARCH_TOP_SAG * 0.85, ARCH_BOT_SAG * 0.85, ARCH_SIDE_SAG * 0.85, N_CORNER, N_EDGE
    )
    pts_lip_inner = ft600_contour_points(
        CASE_W - 2.0 * (WALL_MIN + 0.8),
        CASE_H - 2.0 * (WALL_MIN + 0.8),
        CORNER_R - (WALL_MIN + 0.8),
        ARCH_TOP_SAG * 0.80, ARCH_BOT_SAG * 0.80, ARCH_SIDE_SAG * 0.80, N_CORNER, N_EDGE
    )
    front_lip = create_ring_loft_obj(
        "Front_Alignment_Lip",
        [(pts_lip_outer, z_front_split - RING_LIP_H), (pts_lip_outer, z_front_split + 0.2)],
        [(pts_lip_inner, z_front_split - RING_LIP_H), (pts_lip_inner, z_front_split + 0.2)],
        col_tmp,
    )
    apply_boolean(obj_front, front_lip, 'UNION')

    # 1.6 Quatro torres internas M3 para o PCB da JC4827W543 (112.6 x 62.1 mm) + 4 torres nos cantos p/ fechar a carcaça
    pcb_boss_coords = [
        (-PCB_HOLE_DX / 2.0, PCB_OFFSET_Y - PCB_HOLE_DY / 2.0),
        ( PCB_HOLE_DX / 2.0, PCB_OFFSET_Y - PCB_HOLE_DY / 2.0),
        ( PCB_HOLE_DX / 2.0, PCB_OFFSET_Y + PCB_HOLE_DY / 2.0),
        (-PCB_HOLE_DX / 2.0, PCB_OFFSET_Y + PCB_HOLE_DY / 2.0),
    ]
    boss_z_top = z_visor_floor - 1.0
    boss_z_bot = z_pcb_front
    boss_h = boss_z_top - boss_z_bot

    for idx, (bx, by) in enumerate(pcb_boss_coords):
        boss = make_cylinder(
            f"Boss_PCB_{idx+1}", PCB_BOSS_OD / 2.0, boss_h,
            (bx, by, boss_z_bot + boss_h / 2.0), col_tmp, segments=28
        )
        apply_boolean(obj_front, boss, 'UNION')
        hole = make_cylinder(
            f"Hole_PCB_M3_{idx+1}", M3_INSERT_DIA / 2.0, boss_h + 0.6,
            (bx, by, boss_z_bot + boss_h / 2.0 - 0.4), col_tmp, segments=24
        )
        apply_boolean(obj_front, hole, 'DIFFERENCE')

    case_boss_coords = [
        (-CASE_BOSS_DX / 2.0, -CASE_BOSS_DY / 2.0),
        ( CASE_BOSS_DX / 2.0, -CASE_BOSS_DY / 2.0),
        ( CASE_BOSS_DX / 2.0,  CASE_BOSS_DY / 2.0),
        (-CASE_BOSS_DX / 2.0,  CASE_BOSS_DY / 2.0),
    ]
    for idx, (cx, cy) in enumerate(case_boss_coords):
        cboss = make_cylinder(
            f"Boss_CaseFront_{idx+1}", CASE_BOSS_OD / 2.0, boss_h,
            (cx, cy, boss_z_bot + boss_h / 2.0), col_tmp, segments=28
        )
        apply_boolean(obj_front, cboss, 'UNION')
        chole = make_cylinder(
            f"Hole_CaseFront_M3_{idx+1}", M3_INSERT_DIA / 2.0, boss_h + 0.6,
            (cx, cy, boss_z_bot + boss_h / 2.0 - 0.4), col_tmp, segments=24
        )
        apply_boolean(obj_front, chole, 'DIFFERENCE')

    # 1.7 Gravação da Logo SchutzMachine em baixo-relevo na moldura inferior frontal (abaixo da tela)
    cut_front_logo = create_svg_logo_cutter(
        "Cut_Logo_Frontal",
        LOGO_SVG_PATH,
        FRONT_LOGO_W,
        (0.0, FRONT_LOGO_Y),
        z_visor_floor - FRONT_LOGO_DEPTH,
        z_visor_floor + 0.8,
        col_tmp,
        mirror_x=False,
    )
    if cut_front_logo:
        apply_boolean(obj_front, cut_front_logo, 'DIFFERENCE', solver='MANIFOLD')

    assign_single_material(obj_front, mats["preto_fosco"])

    # ==========================================================================
    # ETAPA 2: 02_anel_vermelho (Friso Assinatura FT600 - 3.0 mm espessura)
    # ==========================================================================
    pts_ring_outer_edge = ft600_contour_points(
        CASE_W + 2.0 * (RING_PROTRUSION * 0.25),
        CASE_H + 2.0 * (RING_PROTRUSION * 0.25),
        CORNER_R + RING_PROTRUSION * 0.25,
        ARCH_TOP_SAG, ARCH_BOT_SAG, ARCH_SIDE_SAG, N_CORNER, N_EDGE
    )
    pts_ring_outer_peak = ft600_contour_points(
        CASE_W + 2.0 * RING_PROTRUSION,
        CASE_H + 2.0 * RING_PROTRUSION,
        CORNER_R + RING_PROTRUSION,
        ARCH_TOP_SAG, ARCH_BOT_SAG, ARCH_SIDE_SAG, N_CORNER, N_EDGE
    )
    pts_ring_inner = ft600_contour_points(
        CASE_W - 2.0 * RING_WALL_W,
        CASE_H - 2.0 * RING_WALL_W,
        CORNER_R - RING_WALL_W,
        ARCH_TOP_SAG * 0.84, ARCH_BOT_SAG * 0.84, ARCH_SIDE_SAG * 0.84, N_CORNER, N_EDGE
    )

    z_r0 = z_rear_split
    z_r1 = z_rear_split + 0.6
    z_r2 = z_front_split - 0.6
    z_r3 = z_front_split

    obj_ring = create_ring_loft_obj(
        "02_anel_vermelho",
        [
            (pts_ring_outer_edge, z_r0),
            (pts_ring_outer_peak, z_r1),
            (pts_ring_outer_peak, z_r2),
            (pts_ring_outer_edge, z_r3),
        ],
        [
            (pts_ring_inner, z_r0),
            (pts_ring_inner, z_r1),
            (pts_ring_inner, z_r2),
            (pts_ring_inner, z_r3),
        ],
        col_etapa2,
    )

    pts_ring_groove_out = ft600_contour_points(
        CASE_W - 2.0 * (RING_WALL_W - RING_LIP_W - TOLERANCE_3D),
        CASE_H - 2.0 * (RING_WALL_W - RING_LIP_W - TOLERANCE_3D),
        CORNER_R - (RING_WALL_W - RING_LIP_W),
        ARCH_TOP_SAG * 0.85, ARCH_BOT_SAG * 0.85, ARCH_SIDE_SAG * 0.85, N_CORNER, N_EDGE
    )
    pts_ring_groove_in = ft600_contour_points(
        CASE_W - 2.0 * (RING_WALL_W + 1.0),
        CASE_H - 2.0 * (RING_WALL_W + 1.0),
        CORNER_R - (RING_WALL_W + 1.0),
        ARCH_TOP_SAG * 0.80, ARCH_BOT_SAG * 0.80, ARCH_SIDE_SAG * 0.80, N_CORNER, N_EDGE
    )
    cut_ring_front_groove = create_ring_loft_obj(
        "Cut_Ring_Front_Groove",
        [(pts_ring_groove_out, z_front_split - RING_LIP_H - 0.2), (pts_ring_groove_out, z_front_split + 0.3)],
        [(pts_ring_groove_in,  z_front_split - RING_LIP_H - 0.2), (pts_ring_groove_in,  z_front_split + 0.3)],
        col_tmp,
    )
    apply_boolean(obj_ring, cut_ring_front_groove, 'DIFFERENCE')

    pts_ring_rear_lip_out = ft600_contour_points(
        CASE_W - 2.0 * (WALL_MIN + TOLERANCE_3D * 0.5),
        CASE_H - 2.0 * (WALL_MIN + TOLERANCE_3D * 0.5),
        CORNER_R - (WALL_MIN + TOLERANCE_3D * 0.5),
        ARCH_TOP_SAG * 0.82, ARCH_BOT_SAG * 0.82, ARCH_SIDE_SAG * 0.82, N_CORNER, N_EDGE
    )
    ring_rear_lip = create_ring_loft_obj(
        "Ring_Rear_Male_Lip",
        [(pts_ring_rear_lip_out, z_rear_split - RING_LIP_H), (pts_ring_rear_lip_out, z_rear_split + 0.2)],
        [(pts_ring_inner,        z_rear_split - RING_LIP_H), (pts_ring_inner,        z_rear_split + 0.2)],
        col_tmp,
    )
    apply_boolean(obj_ring, ring_rear_lip, 'UNION')

    assign_single_material(obj_ring, mats["vermelho_ft"])

    # ==========================================================================
    # ETAPA 3: 03_tampa_traseira (Preto Fosco - Berços p/ todos os componentes)
    # ==========================================================================
    obj_rear = create_extruded_profile_obj("03_tampa_traseira", pts_outer, z_rear_back, z_rear_split, col_etapa3)

    cut_rear_cavity = create_extruded_profile_obj(
        "Cut_Rear_Internal_Cavity", pts_inner_cavity, z_rear_floor, z_rear_split + 0.5, col_tmp
    )
    apply_boolean(obj_rear, cut_rear_cavity, 'DIFFERENCE')

    # 3.1 Quatro pés/torres cilíndricas de montagem nos 4 cantos traseiros (Ø 10 mm, altura 6 mm, furo Ø 5.2 mm p/ inserto M4)
    rear_foot_coords = [
        (-REAR_FOOT_DX / 2.0, -REAR_FOOT_DY / 2.0),
        ( REAR_FOOT_DX / 2.0, -REAR_FOOT_DY / 2.0),
        ( REAR_FOOT_DX / 2.0,  REAR_FOOT_DY / 2.0),
        (-REAR_FOOT_DX / 2.0,  REAR_FOOT_DY / 2.0),
    ]
    for idx, (fx, fy) in enumerate(rear_foot_coords):
        foot = make_cylinder(
            f"Rear_Mount_Foot_{idx+1}",
            REAR_FOOT_OD / 2.0,
            REAR_FOOT_H + 1.5,
            (fx, fy, z_rear_back - REAR_FOOT_H / 2.0 + 0.75),
            col_tmp,
            segments=32,
        )
        apply_boolean(obj_rear, foot, 'UNION')
        fhole = make_cylinder(
            f"Rear_Mount_Hole_M4_{idx+1}",
            REAR_FOOT_HOLE_DIA / 2.0,
            REAR_FOOT_H + 1.2,
            (fx, fy, z_rear_back - REAR_FOOT_H / 2.0 - 0.2),
            col_tmp,
            segments=24,
        )
        apply_boolean(obj_rear, fhole, 'DIFFERENCE')

    # 3.2 Quatro torres de fechamento da carcaça nos cantos extremos (alinhadas com a tampa frontal)
    rear_post_h = z_rear_split - z_rear_floor
    for idx, (cx, cy) in enumerate(case_boss_coords):
        rpost = make_cylinder(
            f"Rear_Corner_Post_{idx+1}",
            CASE_BOSS_OD / 2.0,
            rear_post_h,
            (cx, cy, z_rear_floor + rear_post_h / 2.0),
            col_tmp,
            segments=28,
        )
        apply_boolean(obj_rear, rpost, 'UNION')

        rhole = make_cylinder(
            f"Rear_Corner_Hole_M3_{idx+1}",
            M3_THROUGH_DIA / 2.0,
            REAR_DEPTH + 4.0,
            (cx, cy, z_rear_back + REAR_DEPTH / 2.0),
            col_tmp,
            segments=24,
        )
        apply_boolean(obj_rear, rhole, 'DIFFERENCE')

        rcbore = make_cylinder(
            f"Rear_Corner_Counterbore_{idx+1}",
            M3_HEAD_DIA / 2.0,
            3.0,
            (cx, cy, z_rear_back + 0.8),
            col_tmp,
            segments=24,
        )
        apply_boolean(obj_rear, rcbore, 'DIFFERENCE')

    # 3.3 Nas laterais esquerda e direita da traseira: 5 aletas/nervuras verticais em baixo-relevo + 2 rasgos de ventilação
    rib_z_center = (z_rear_back + z_rear_split) / 2.0 + 0.5
    rib_h_span = 50.0
    for side_sign in (-1.0, 1.0):
        side_x = side_sign * (CASE_W / 2.0 + ARCH_SIDE_SAG)
        for r_idx in range(SIDE_RIB_COUNT):
            rz = rib_z_center + (r_idx - (SIDE_RIB_COUNT - 1) / 2.0) * SIDE_RIB_SPACING
            cut_rib = make_box(
                f"Cut_SideRib_{int(side_sign)}_{r_idx}",
                (SIDE_RIB_DEPTH * 2.4, rib_h_span, SIDE_RIB_W),
                (side_x, 0.0, rz),
                col_tmp,
            )
            apply_boolean(obj_rear, cut_rib, 'DIFFERENCE')

            if r_idx in (1, 3):
                cut_vent = make_box(
                    f"Cut_SideVent_{int(side_sign)}_{r_idx}",
                    (WALL_MIN * 3.5, VENT_SLOT_H, VENT_SLOT_W),
                    (side_x - side_sign * 1.5, 0.0, rz),
                    col_tmp,
                )
                apply_boolean(obj_rear, cut_vent, 'DIFFERENCE')

    # 3.4 No centro-inferior traseiro: baia rebaixada (45 x 24 mm) com 1 furo circular Ø 16.2 mm p/ conector GX16-4P
    pts_bay_boss = rounded_rect_points(REAR_BAY_W + 6.0, REAR_BAY_H + 6.0, 6.0, 0.0, REAR_BAY_Y)
    bay_reinforce = create_extruded_profile_obj(
        "Rear_Bay_Reinforce", pts_bay_boss, z_rear_back + 0.2, z_rear_floor + REAR_BAY_DEPTH, col_tmp
    )
    apply_boolean(obj_rear, bay_reinforce, 'UNION')

    pts_bay_cut = rounded_rect_points(REAR_BAY_W, REAR_BAY_H, 4.5, 0.0, REAR_BAY_Y)
    cut_rear_bay = create_extruded_profile_obj(
        "Cut_Rear_Bay", pts_bay_cut, z_rear_back - 1.0, z_rear_back + REAR_BAY_DEPTH, col_tmp
    )
    apply_boolean(obj_rear, cut_rear_bay, 'DIFFERENCE')

    cut_gx16 = make_cylinder(
        "Cut_GX16_Hole",
        GX16_HOLE_DIA / 2.0,
        14.0,
        (0.0, REAR_BAY_Y, z_rear_back + 2.0),
        col_tmp,
        segments=36,
    )
    apply_boolean(obj_rear, cut_gx16, 'DIFFERENCE')

    # 3.5 Recortes discretos alinhados às bordas do PCB para acesso ao USB-C (lateral direita) e microSD (base)
    cut_usbc = make_box(
        "Cut_USBC_Access",
        (WALL_MIN * 3.5, USBC_CUT_H, USBC_CUT_W),
        (CASE_W / 2.0, USBC_OFFSET_Y, z_rear_split - USBC_CUT_W / 2.0 + 0.2),
        col_tmp,
    )
    apply_boolean(obj_rear, cut_usbc, 'DIFFERENCE')

    cut_sd = make_box(
        "Cut_MicroSD_Access",
        (SD_CUT_W, WALL_MIN * 3.5, SD_CUT_H),
        (SD_OFFSET_X, -CASE_H / 2.0, z_rear_split - SD_CUT_H / 2.0 + 0.2),
        col_tmp,
    )
    apply_boolean(obj_rear, cut_sd, 'DIFFERENCE')

    # 3.6 Berço interno #1 (snap-fit) na direita traseira para o módulo CAN SN65HVD230 (16.5 x 14.5 x 6.0 mm)
    def add_snap_cradle(parent_obj, prefix, mod_w, mod_h, cradle_h, wall_t, cx, cy):
        in_w = mod_w + TOLERANCE_3D
        in_h = mod_h + TOLERANCE_3D
        out_w = in_w + 2.0 * wall_t
        out_h = in_h + 2.0 * wall_t

        c_out = make_box(
            f"{prefix}_Outer",
            (out_w, out_h, cradle_h),
            (cx, cy, z_rear_floor + cradle_h / 2.0 - 0.2),
            col_tmp,
        )
        apply_boolean(parent_obj, c_out, 'UNION')

        c_pock = make_box(
            f"{prefix}_Pocket",
            (in_w, in_h, cradle_h + 1.0),
            (cx, cy, z_rear_floor + cradle_h / 2.0 + 1.2),
            col_tmp,
        )
        apply_boolean(parent_obj, c_pock, 'DIFFERENCE')

        c_sx = make_box(
            f"{prefix}_SlotX",
            (out_w + 2.0, max(4.0, in_h - 5.0), cradle_h + 1.0),
            (cx, cy, z_rear_floor + cradle_h / 2.0 + 1.6),
            col_tmp,
        )
        apply_boolean(parent_obj, c_sx, 'DIFFERENCE')

        c_sy = make_box(
            f"{prefix}_SlotY",
            (max(4.0, in_w - 6.0), out_h + 2.0, cradle_h + 1.0),
            (cx, cy, z_rear_floor + cradle_h / 2.0 + 1.6),
            col_tmp,
        )
        apply_boolean(parent_obj, c_sy, 'DIFFERENCE')

    # Berço #1: Transceiver CAN SN65HVD230 (lado direito superior)
    add_snap_cradle(obj_rear, "CAN_Cradle", CAN_W, CAN_H, CAN_CRADLE_H, CAN_CRADLE_WALL, CAN_CRADLE_X, CAN_CRADLE_Y)

    # Berço #2: Regulador Step-Down MP1584EN 12V->5V (lado esquerdo inferior, longe do GX16 e da antena)
    add_snap_cradle(obj_rear, "StepDown_Cradle", STEPDOWN_W, STEPDOWN_H, STEPDOWN_CRADLE_H, STEPDOWN_WALL, STEPDOWN_X, STEPDOWN_Y)

    # Berço #3: Anel de retenção para Buzzer Piezo 12mm (saída Speak P7)
    buz_ring_out = make_cylinder(
        "Buzzer_Cradle_Out",
        (BUZZER_DIA + TOLERANCE_3D) / 2.0 + BUZZER_WALL,
        4.0,
        (BUZZER_X, BUZZER_Y, z_rear_floor + 1.8),
        col_tmp,
        segments=28,
    )
    apply_boolean(obj_rear, buz_ring_out, 'UNION')
    buz_ring_in = make_cylinder(
        "Buzzer_Cradle_In",
        (BUZZER_DIA + TOLERANCE_3D) / 2.0,
        5.0,
        (BUZZER_X, BUZZER_Y, z_rear_floor + 2.5),
        col_tmp,
        segments=28,
    )
    apply_boolean(obj_rear, buz_ring_in, 'DIFFERENCE')

    # 3.7 Gravação da Logo SchutzMachine em baixo-relevo nas costas da tampa traseira (acima do conector GX16-4P)
    cut_rear_logo = create_svg_logo_cutter(
        "Cut_Logo_Traseira",
        LOGO_SVG_PATH,
        REAR_LOGO_W,
        (0.0, REAR_LOGO_Y),
        z_rear_back - 0.8,
        z_rear_back + REAR_LOGO_DEPTH,
        col_tmp,
        mirror_x=True,
    )
    if cut_rear_logo:
        apply_boolean(obj_rear, cut_rear_logo, 'DIFFERENCE', solver='EXACT', use_self=True)

    assign_single_material(obj_rear, mats["preto_fosco"])

    # ==========================================================================
    # 5. MODELAGEM 3D REALISTA DE TODOS OS COMPONENTES INTERNOS (AUDITORIA DE ESPAÇO)
    # ==========================================================================
    # 5.1 Tela IPS 4.3" + Vidro Touch GT911 (105.5 x 68.0 x 3.1 mm) e área ativa (95.04 x 53.86 mm)
    obj_lcd_mod = make_box(
        "Comp_01_Display_IPS_Touch",
        (SCREEN_VIS_W, SCREEN_VIS_H, LCD_THICK),
        (0.0, PCB_OFFSET_Y, z_pcb_front + LCD_THICK / 2.0),
        col_ref,
    )
    assign_single_material(obj_lcd_mod, mats["vidro_tela"])

    # 5.2 PCB Guition JC4827W543 completo com as 4 orelhas (120.0 x 70.2 x 1.6 mm)
    obj_pcb = make_box(
        "Comp_02_PCB_Guition_JC4827W543",
        (PCB_W_BODY, PCB_H, PCB_THICK),
        (0.0, PCB_OFFSET_Y, z_pcb_front - PCB_THICK / 2.0),
        col_ref,
    )
    for idx, (ex, ey) in enumerate(pcb_boss_coords):
        ear = make_cylinder(
            f"PCB_Ear_{idx+1}", 3.7, PCB_THICK,
            (ex, ey, z_pcb_front - PCB_THICK / 2.0), col_tmp, segments=20
        )
        apply_boolean(obj_pcb, ear, 'UNION')
        ear_hole = make_cylinder(
            f"PCB_EarHole_{idx+1}", 1.6, PCB_THICK + 1.0,
            (ex, ey, z_pcb_front - PCB_THICK / 2.0), col_tmp, segments=20
        )
        apply_boolean(obj_pcb, ear_hole, 'DIFFERENCE')
    assign_single_material(obj_pcb, mats["pcb_preto"])

    # 5.3 Módulo ESP32-S3-WROOM-1 N4R8 (18.0 x 25.5 x 3.1 mm) soldado na traseira esquerda do PCB
    obj_esp32 = make_box(
        "Comp_03_ESP32_S3_WROOM1",
        (25.5, 18.0, 3.1),
        (-39.5, PCB_OFFSET_Y + 8.5, z_pcb_back - 3.1 / 2.0),
        col_ref,
    )
    assign_single_material(obj_esp32, mats["metal"])

    # 5.4 Slot MicroSD (TF1 - 15.0 x 14.5 x 2.8 mm) + Conectores JST 1.25mm (P1..P7) + USB-C no PCB
    obj_sd_slot = make_box(
        "Comp_04_Slot_MicroSD_TF1",
        (15.0, 14.5, 2.8),
        (SD_OFFSET_X, PCB_OFFSET_Y - PCB_H / 2.0 + 6.5, z_pcb_back - 2.8 / 2.0),
        col_ref,
    )
    assign_single_material(obj_sd_slot, mats["metal"])

    # Conectores JST P2, P3, P4, P5 na borda inferior do PCB + plugues encaixados (simulando o espaço ocupado pelos cabos!)
    for j_idx, jx in enumerate([-6.0, 10.0, 26.0, 40.0]):
        jst_hdr = make_box(
            f"Comp_05_JST_P{j_idx+2}_Header_Plugs",
            (7.5, 11.5, 3.4),  # Header + plugue JST + curva do fio
            (jx, PCB_OFFSET_Y - PCB_H / 2.0 - 2.0, z_pcb_back - 3.4 / 2.0),
            col_ref,
        )
        assign_single_material(jst_hdr, mats["jst_branco"])

    # 5.5 10x LEDs de 5mm Comuns de Kit (cápsula Ø 5.0 mm + colarinho Ø 5.8 mm, comprimento 8.6 mm) no topo
    z_led_tip = z_visor_floor + 1.8
    z_led_center = z_led_tip - LED5MM_BODY_LEN / 2.0
    for i, (lx, ly) in enumerate(led_positions):
        if i < 4:
            lmat = mats["led_verde"]
        elif i < 7:
            lmat = mats["led_vermelho"]
        else:
            lmat = mats["led_azul"]
        led_obj = make_cylinder(
            f"Comp_06_LED5mm_{i+1:02d}",
            LED5MM_DOME_DIA / 2.0,
            LED5MM_BODY_LEN,
            (lx, ly, z_led_center),
            col_ref,
            segments=24,
        )
        assign_single_material(led_obj, lmat)

    # 5.6 Módulo Transceiver CAN SN65HVD230 (16.5 x 14.5 x 6.0 mm) encaixado no berço direito
    obj_can = make_box(
        "Comp_07_Modulo_CAN_SN65HVD230",
        (CAN_W, CAN_H, CAN_D),
        (CAN_CRADLE_X, CAN_CRADLE_Y, z_rear_floor + 1.0 + CAN_D / 2.0),
        col_ref,
    )
    assign_single_material(obj_can, mats["can_azul"])

    # 5.7 Módulo Step-Down DC-DC MP1584EN (22.0 x 17.0 x 4.5 mm) encaixado no berço esquerdo
    obj_step = make_box(
        "Comp_08_StepDown_MP1584EN",
        (STEPDOWN_W, STEPDOWN_H, STEPDOWN_D),
        (STEPDOWN_X, STEPDOWN_Y, z_rear_floor + 1.0 + STEPDOWN_D / 2.0),
        col_ref,
    )
    assign_single_material(obj_step, mats["step_verde"])

    # 5.8 Buzzer Piezo 12mm (Ø 12.0 x 7.5 mm) encaixado no berço superior
    obj_buz = make_cylinder(
        "Comp_09_Buzzer_12mm_Speak",
        BUZZER_DIA / 2.0,
        BUZZER_H,
        (BUZZER_X, BUZZER_Y, z_rear_floor + 1.0 + BUZZER_H / 2.0),
        col_ref,
        segments=28,
    )
    assign_single_material(obj_buz, mats["pcb_preto"])

    # 5.9 Corpo Interno do Conector GX16-4P (rosca M16 + terminais internos de 12.5 mm)
    obj_gx16 = make_cylinder(
        "Comp_10_Conector_GX16_4P",
        15.8 / 2.0,
        13.5,
        (0.0, REAR_BAY_Y, z_rear_back + REAR_BAY_DEPTH + 13.5 / 2.0 - 1.5),
        col_ref,
        segments=32,
    )
    assign_single_material(obj_gx16, mats["metal"])

    if len(col_tmp.objects) == 0:
        bpy.data.collections.remove(col_tmp)

    # ==========================================================================
    # 6. AUDITORIA AUTOMÁTICA DE FOLGAS E ESPAÇO INTERNO (EM MILÍMETROS)
    # ==========================================================================
    y_pcb_top_edge = PCB_OFFSET_Y + PCB_H / 2.0
    y_pcb_bot_edge = PCB_OFFSET_Y - PCB_H / 2.0
    y_led_flange_bot = SHIFT_LED_Y - LED5MM_SOCKET_DIA / 2.0
    y_inner_bot_wall = -(CASE_H / 2.0 - WALL_MIN)
    x_inner_right_wall = (CASE_W / 2.0 - WALL_MIN)
    x_pcb_right_body = PCB_W_BODY / 2.0

    gap_led_to_pcb_y = y_led_flange_bot - y_pcb_top_edge
    gap_jst_bottom_y = y_pcb_bot_edge - y_inner_bot_wall
    gap_p1_right_x = x_inner_right_wall - x_pcb_right_body
    gap_z_behind_pcb = z_pcb_back - z_rear_floor
    gap_z_can_to_pcb = z_pcb_back - (z_rear_floor + 1.0 + CAN_D)
    gap_z_step_to_pcb = z_pcb_back - (z_rear_floor + 1.0 + STEPDOWN_D)
    gap_z_gx16_to_pcb = z_pcb_back - (z_rear_back + REAR_BAY_DEPTH + 12.0)

    print("=== AUDITORIA MECÂNICA DE ESPAÇO INTERNO ===")
    print(f"1. Folga Y entre base dos LEDs 5mm e topo do PCB: {gap_led_to_pcb_y:.2f} mm (Livre de colisão!)")
    print(f"2. Espaço Y livre abaixo do PCB p/ plugues JST P2..P5: {gap_jst_bottom_y:.2f} mm (Mín. 8.0 mm)")
    print(f"3. Espaço X livre à direita do corpo do PCB p/ P1 e USB-C: {gap_p1_right_x:.2f} mm")
    print(f"4. Profundidade Z total livre atrás do PCB: {gap_z_behind_pcb:.2f} mm")
    print(f"5. Folga Z entre topo do módulo CAN SN65HVD230 e costas do PCB: {gap_z_can_to_pcb:.2f} mm")
    print(f"6. Folga Z entre topo do Step-Down MP1584EN e costas do PCB: {gap_z_step_to_pcb:.2f} mm")
    print(f"7. Folga Z entre terminais do conector GX16-4P e costas do PCB: {gap_z_gx16_to_pcb:.2f} mm")

    # ==========================================================================
    # 7. CONFIGURAÇÃO DE CÂMERA, ILUMINAÇÃO E VIEWPORT
    # ==========================================================================
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.clip_start = 1.0
                        space.clip_end = 10000.0
                        space.shading.type = 'MATERIAL'

    def add_sun(name, energy, rot_deg, color=(1.0, 0.99, 0.97)):
        ldata = bpy.data.lights.new(name=name, type='SUN')
        ldata.energy = energy
        ldata.color = color
        ldata.angle = math.radians(12.0)
        lobj = bpy.data.objects.new(name=name, object_data=ldata)
        scene.collection.objects.link(lobj)
        lobj.rotation_euler = tuple(math.radians(a) for a in rot_deg)
        return lobj

    add_sun("Key_Sun", 3.5, (35.0, -25.0, 20.0))
    add_sun("Fill_Sun", 1.8, (-40.0, 35.0, -15.0), (0.9, 0.95, 1.0))
    add_sun("Rim_Sun", 2.2, (145.0, 20.0, 160.0))

    cam_data = bpy.data.cameras.new("Camera_FT600")
    cam_data.clip_start = 1.0
    cam_data.clip_end = 10000.0
    cam_data.lens = 50.0
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    return obj_front, obj_ring, obj_rear


def set_layout_mode(mode="ASSEMBLED"):
    """
    Alterna a organização das 3 etapas na cena:
    - "ASSEMBLED": Peças fechadas na posição de montagem (0, 0, 0)
    - "EXPLODED_Z": Peças e componentes internos afastados no eixo Z para inspeção de encaixe
    - "PRINT_BED": Cada uma das 3 peças posicionada lado a lado na orientação IDEAL de impressão 3D (Z_min = 0)
    """
    front = bpy.data.objects.get("01_tampa_frontal")
    ring  = bpy.data.objects.get("02_anel_vermelho")
    rear  = bpy.data.objects.get("03_tampa_traseira")
    col_ref = bpy.data.collections.get("04_Componentes_Internos")

    if not (front and ring and rear):
        return

    # Reseta rotações e posições
    for o in (front, ring, rear):
        o.location = (0.0, 0.0, 0.0)
        o.rotation_euler = (0.0, 0.0, 0.0)

    if mode == "ASSEMBLED":
        if col_ref:
            col_ref.hide_viewport = False
            col_ref.hide_render = False
            for o in col_ref.objects:
                o.location = (0.0, 0.0, 0.0)

    elif mode == "EXPLODED_Z":
        if col_ref:
            col_ref.hide_viewport = False
            col_ref.hide_render = False
        front.location.z = 48.0
        ring.location.z  = 12.0
        rear.location.z  = -38.0
        if col_ref:
            for o in col_ref.objects:
                if "LED5mm" in o.name:
                    o.location.z = 36.0
                elif any(k in o.name for k in ("Display", "PCB", "ESP32", "MicroSD", "JST")):
                    o.location.z = 22.0
                else:
                    o.location.z = -38.0

    elif mode == "PRINT_BED":
        # Oculta componentes eletrônicos e posiciona as 3 etapas lado a lado na mesa de impressão (Z_min = 0)
        if col_ref:
            col_ref.hide_viewport = True
            col_ref.hide_render = True

        # Etapa 1 (Tampa Frontal): rotacionada 180° em X para a face frontal ficar apoiada na mesa (Z=0) e torres p/ cima (+Z)
        front.rotation_euler = (math.pi, 0.0, 0.0)
        front.location = (-170.0, 0.0, CASE_D / 2.0)

        # Etapa 2 (Anel Vermelho): apoiado plano na mesa (Z=0) no centro
        ring.location = (0.0, 0.0, -(CASE_D / 2.0 - FRONT_DEPTH - RING_THICK))

        # Etapa 3 (Tampa Traseira): apoiada com as costas/pés para baixo e cavidade/berços para cima (+Z)
        rear.location = (170.0, 0.0, CASE_D / 2.0 + REAR_FOOT_H)


def export_individual_models_for_printing(out_dir=r"c:\Users\ryhan\Documents\schutzmachine\impressao_3d"):
    """
    Exporta um modelo individual (.STL e .BLEND) para cada uma das 3 etapas na orientação ideal de impressão 3D!
    """
    os.makedirs(out_dir, exist_ok=True)
    front = bpy.data.objects.get("01_tampa_frontal")
    ring  = bpy.data.objects.get("02_anel_vermelho")
    rear  = bpy.data.objects.get("03_tampa_traseira")

    parts_config = [
        (front, "01_tampa_frontal", (math.pi, 0.0, 0.0), (0.0, 0.0, CASE_D / 2.0)),
        (ring,  "02_anel_vermelho", (0.0, 0.0, 0.0),     (0.0, 0.0, -(CASE_D / 2.0 - FRONT_DEPTH - RING_THICK))),
        (rear,  "03_tampa_traseira",(0.0, 0.0, 0.0),     (0.0, 0.0, CASE_D / 2.0 + REAR_FOOT_H)),
    ]

    exported_files = []
    for obj, fname, rot, loc in parts_config:
        if not obj:
            continue
        bpy.ops.object.select_all(action='DESELECT')
        old_rot = tuple(obj.rotation_euler)
        old_loc = tuple(obj.location)

        obj.rotation_euler = rot
        obj.location = loc
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

        stl_path = os.path.join(out_dir, f"{fname}.stl")
        bpy.ops.wm.stl_export(
            filepath=stl_path,
            export_selected_objects=True,
            global_scale=1.0,
            apply_modifiers=True,
        )
        exported_files.append(stl_path)

        obj.rotation_euler = old_rot
        obj.location = old_loc

    print("Arquivos STL individuais exportados na orientação ideal de impressão:", exported_files)
    return exported_files


if __name__ in ("__main__", "blender_mcp", "__builtin__", "builtins"):
    build_ft600_polo_case()
    set_layout_mode("ASSEMBLED")
