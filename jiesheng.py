# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
#
# jiesheng.py —— 结绳记事 · 打结记录编辑器
# Copyright (C) 2026  jiesheng contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""结绳记事 —— 打结记录编辑器  (jiesheng.py)

一条横绳（太极）在上，纵绳往下垂。纵绳四种：
    分段绳  —— 横绳上一个结 ＋ 一条超长虚线（古人省绳子，只打一个横结；
                虚线只是给眼睛看的辅助线）
    三爻绳  —— 三个阴阳结，得一个八卦
    六爻绳  —— 六个阴阳结，得一个六十四卦
    十进制绳 —— 位值制结绳（十五 ＝ 十位一结 ＋ 个位五结），1-10 兼注天干

爻序：最靠近横绳的结 ＝ 上爻，最下面的结 ＝ 初爻（取「画在纸上的样子」）。
右接：支绳一律只连右边一侧，所以一眼看得出它跟上面那组是分开的；可以一直串下去。

六十四卦名一律用自定义的「先天方图卦序」（照抄 guaxu_core.FANG_TU）。

Python 3 + tkinter，无第三方依赖。
"""

import json
import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font as tkfont

APP_NAME = "结绳记事"
APP_VER = "1.0"
FILE_EXT = ".jsg.json"

HERE = os.path.dirname(os.path.abspath(__file__))


# ══════════════════════════════════════════════════════════════════════
#  一、八卦 / 六十四卦 基础表
# ══════════════════════════════════════════════════════════════════════

# 爻一律以 (初, 二, 三) 由下往上存放，1 ＝ 阳，0 ＝ 阴。
# 顺序 ＝ 先天八卦序 乾兑离震巽坎艮坤，方图卦序就是拿这个序做 上×下 的格子。
TRIGRAMS = [
    # 名   符号  自然 五行  人伦   动物  身体  后天方位 先天方位 卦德  爻(初二三)
    ("乾", "☰", "天", "金", "父", "马", "首", "西北", "南", "健", (1, 1, 1)),
    ("兑", "☱", "泽", "金", "少女", "羊", "口", "西", "东南", "悦", (1, 1, 0)),
    ("离", "☲", "火", "火", "中女", "雉", "目", "南", "东", "丽", (1, 0, 1)),
    ("震", "☳", "雷", "木", "长男", "龙", "足", "东", "东北", "动", (1, 0, 0)),
    ("巽", "☴", "风", "木", "长女", "鸡", "股", "东南", "西南", "入", (0, 1, 1)),
    ("坎", "☵", "水", "水", "中男", "豕", "耳", "北", "西", "陷", (0, 1, 0)),
    ("艮", "☶", "山", "土", "少男", "狗", "手", "东北", "西北", "止", (0, 0, 1)),
    ("坤", "☷", "地", "土", "母", "牛", "腹", "西南", "北", "顺", (0, 0, 0)),
]

TRI_NAME = [t[0] for t in TRIGRAMS]
TRI_SYM = {t[0]: t[1] for t in TRIGRAMS}
TRI_BITS = {t[0]: t[10] for t in TRIGRAMS}
BITS_TRI = {t[10]: t[0] for t in TRIGRAMS}
TRI_IDX = {t[0]: i for i, t in enumerate(TRIGRAMS)}

# 象征特质：照「八卦代表动物／象征特质」表
TRI_TRAIT = {
    "乾": "健行不息、刚劲有力",
    "坤": "柔顺包容、任劳任怨",
    "震": "动达御空、善变威严",
    "巽": "知时善鸣、风吹知敏",
    "坎": "喜水穴居、外柔内刚",
    "离": "美丽附着、光明外露",
    "艮": "止动防卫、忠诚守卫",
    "兑": "和悦外向、温顺喜悦",
}

# 说卦传广象（取象用，写全面注解时列出）
TRI_XIANG = {
    "乾": "君、玉、金、寒、冰、大赤、良马、老马、瘠马、驳马、木果、圆、首领",
    "坤": "布、釜、吝啬、均、子母牛、大舆、文、众、柄、黑、土地、群众",
    "震": "玄黄、大涂、决躁、苍筤竹、萑苇、善鸣马、足白马、的颡马、长子、雷声",
    "巽": "木、绳直、工、白、长、高、进退、不果、臭、寡发、广颡、近利市三倍、风行",
    "坎": "沟渎、隐伏、弓轮、加忧、心病、耳痛、血卦、赤、月、盗、坚多心木、险陷",
    "离": "日、电、甲胄、戈兵、大腹、鳖、蟹、蠃、蚌、龟、科上槁木、文明、附丽",
    "艮": "径路、小石、门阙、果蓏、阍寺、指、鼠、黔喙之属、坚多节木、门径、止息",
    "兑": "巫、口舌、毁折、附决、刚卤地、妾、羊、少女、言说、喜悦",
}

# ---- 先天卦「方图」卦序：照抄 guaxu_core.FANG_TU（自定义，权威） ----
FANG_TU = [
    "乾为天", "天泽履", "天火同人", "天雷无妄", "天风姤", "天水讼", "天山遁", "天地否",
    "泽天夬", "兑为泽", "泽火革", "泽雷随", "泽风大过", "泽水困", "泽山咸", "泽地萃",
    "火天大有", "火泽睽", "离为火", "火雷噬嗑", "火风鼎", "火水未济", "火山旅", "火地晋",
    "雷天大壮", "雷泽归妹", "雷火丰", "震为雷", "雷风恒", "雷水解", "雷山小过", "雷地豫",
    "风天小畜", "风泽中孚", "风火家人", "风雷益", "巽为风", "风水涣", "风山渐", "风地观",
    "水天需", "水泽节", "水火既济", "水雷屯", "水风井", "坎为水", "水山蹇", "水地比",
    "山天大畜", "山泽损", "山火贲", "山雷颐", "山风蛊", "山水蒙", "艮为山", "山地剥",
    "地天泰", "地泽临", "地火明夷", "地雷复", "地风升", "地水师", "地山谦", "坤为地",
]

# 周易卦序：只用来取 Unicode 卦符 ䷀-䷿（该区块就是照周易序排的）
ZHOUYI_TU = [
    "乾为天", "坤为地", "水雷屯", "山水蒙", "水天需", "天水讼", "地水师", "水地比",
    "风天小畜", "天泽履", "地天泰", "天地否", "天火同人", "火天大有", "地山谦", "雷地豫",
    "泽雷随", "山风蛊", "地泽临", "风地观", "火雷噬嗑", "山火贲", "山地剥", "地雷复",
    "天雷无妄", "山天大畜", "山雷颐", "泽风大过", "坎为水", "离为火", "泽山咸", "雷风恒",
    "天山遁", "雷天大壮", "火地晋", "地火明夷", "风火家人", "火泽睽", "水山蹇", "雷水解",
    "山泽损", "风雷益", "泽天夬", "天风姤", "泽地萃", "地风升", "泽水困", "水风井",
    "泽火革", "火风鼎", "震为雷", "艮为山", "风山渐", "雷泽归妹", "雷火丰", "火山旅",
    "巽为风", "兑为泽", "风水涣", "水泽节", "风泽中孚", "雷山小过", "水火既济", "火水未济",
]

FANG_INDEX = {n: i for i, n in enumerate(FANG_TU)}
HEX_SYM = {n: chr(0x4DC0 + i) for i, n in enumerate(ZHOUYI_TU)}

GAN10 = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
ZHI12 = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未",
         "申", "酉", "戌", "亥"]
YAO_POS = ["初", "二", "三", "四", "五", "上"]
YAO_POS3 = ["初", "二", "三"]

ROLES = ["（未标）", "卦年", "卦期", "卦月", "卦日", "卦时",
         "方位·地点", "人", "事情", "数量·能量级别", "其他"]

# ── 绳子结构校验码 ──
# 栏位顺序是固定的：年月日时 → 天地人 → 事情 → 数量。
# 这个顺序本身就是校验码：从垃圾堆里捡一串绳出来，你不会把它读成
# 「1年、25年」（年没有那么小），也不会掉转过来读，更不会把 397912
# 读成数量 —— 数量在最后，而且是小数。
ROLE_RANK = {"卦年": 0, "卦期": 1, "卦月": 2, "卦日": 3, "卦时": 4,
             "方位·地点": 5, "人": 6, "事情": 7, "数量·能量级别": 8}
ROLE_RANGE = {"卦期": (1, 64), "卦月": (1, 12), "卦日": (1, 31),
              "卦时": (1, 12)}
YEAR_MIN = 13          # 年不会是 1、不会是 25 —— 比月日大，才认得出是年


def hexagram_name(bits6):
    """bits6 ＝ (初,二,三,四,五,上)，1 阳 0 阴 -> 卦名。"""
    lower = BITS_TRI[tuple(bits6[0:3])]
    upper = BITS_TRI[tuple(bits6[3:6])]
    idx = TRI_IDX[upper] * 8 + TRI_IDX[lower]      # 方图序：上卦为纲，下卦为目
    return FANG_TU[idx], idx + 1, upper, lower


def trigram_name(bits3):
    return BITS_TRI[tuple(bits3)]


YINYANG_NOTE = [
    "阳 ＝ 两股收拢绑死，闭合 —— 穿不过去（一画开天）。",
    "阴 ＝ 两股各走各的，中间留着洞 —— 穿得过去。",
    "所以全阳的乾是一串闭合的环，全阴的坤是一条通到底的道。",
    "",
    "阴也一定要打结，不能因为它是阴就空着 ——",
    "空着，别人分不出是阴，还是这一段根本还没写。",
    "跟零要打大横结是同一个道理。",
]

# 人名：卦象＝氏，数字＝名。水地比＋88 ＝ 小川88。
# 朱重八本名朱八八，父朱五四，祖朱初一，曾祖朱四九，高祖朱百六 —— 同一路数。
NAME_NOTE = "人这一栏：卦象是氏，数字是名（水地比＋88 ＝ 小川 88）"


def tri_info_lines(t):
    """一个八卦的全面注解，回传多行。"""
    i = TRI_IDX[t]
    _, sym, nat, wx, ren, ani, body, hou, xian, de, _ = TRIGRAMS[i]
    return [
        f"{sym} {t}　自然：{nat}　五行：{wx}　卦德：{de}",
        f"　人伦：{ren}　动物：{ani}　身体：{body}　"
        f"方位：后天{hou}／先天{xian}",
        f"　象征：{TRI_TRAIT[t]}",
        f"　广象：{TRI_XIANG[t]}",
    ]


ZHI_MAX = 12            # 地支就十二位：子１…亥１２
GAN_MAX = 10            # 天干就十位：甲１…癸１０


def cyc_clamp(v, n):
    """循环绳只认 1–n：一位一个结。
    十就是十个结，十二就是十二个结 —— 不是位值制，没有进位也没有零。"""
    try:
        v = int(v)
    except (TypeError, ValueError):
        v = 1
    return max(1, min(n, v))


def zhi_clamp(v):
    return cyc_clamp(v, ZHI_MAX)


def gan_clamp(v):
    return cyc_clamp(v, GAN_MAX)


def digits_of(value, places=0, base=10):
    """位值制：回传由高位到低位的数字表。places=0 自动。

    base 10 ＝ 十进制绳（天干）；base 12 ＝ 十二进制绳（地支）。
    """
    value = max(0, int(value))
    ds = []
    while value:
        ds.append(value % base)
        value //= base
    if not ds:
        ds = [0]
    ds.reverse()
    while places > len(ds):
        ds.insert(0, 0)
    return ds


CYCLES = {}             # 绳型 -> (位数, 名表, 叫法)   由下面填


def cyc_name(value, n):
    """循环绳第 value 位叫什么。n＝10 是天干，n＝12 是地支。"""
    tbl = GAN10 if n == GAN_MAX else ZHI12
    return tbl[value - 1] if 1 <= value <= n else ""


PLACE_NAMES = {10: ["个", "十", "百", "千", "万", "十万", "百万"]}


# ══════════════════════════════════════════════════════════════════════
#  二、资料模型
# ══════════════════════════════════════════════════════════════════════

KIND_FEN = "fen"      # 分段绳（横结 ＋ 超长虚线）
KIND_TRI = "tri"      # 三爻绳
KIND_HEX = "hex"      # 六爻绳
KIND_DEC = "dec"      # 十进制／天干绳
KIND_BIG = "big"      # 大横结：零（三个结那么宽）
KIND_GAN = "gan"      # 十天干绳：十位的循环，甲１…癸１０，一位一个结
KIND_DUO = "duo"      # 十二地支绳：十二位的循环，子１…亥１２
KIND_SEP = "sep"      # 分位阳结：两个结那么宽，数字与数字之间的分隔点
KIND_CUT = "cut"      # 分割：横绳上一个普通结而已

CYCLES = {}             # 填在 KIND_* 之后

KIND_LABEL = {KIND_FEN: "分段绳", KIND_TRI: "三爻绳", KIND_HEX: "六爻绳",
              KIND_DEC: "十进制绳", KIND_GAN: "十天干绳",
              KIND_DUO: "十二地支绳",
              KIND_BIG: "大横结（零）",
              KIND_SEP: "分位阳结", KIND_CUT: "分割横结"}

# 循环绳：一位一个结，十就是十个结，十二就是十二个结。
# 不是位值制 —— 没有进位，也没有零。
CYCLES[KIND_GAN] = (GAN_MAX, GAN10, "天干")
CYCLES[KIND_DUO] = (ZHI_MAX, ZHI12, "地支")
KIND_CYCLE = (KIND_GAN, KIND_DUO)
KIND_COUNT = (KIND_DEC, KIND_GAN, KIND_DUO)    # 会打计数结的绳

DEC_TALLY = "tally"   # 打几个结就是几（位值制结群）
DEC_BIN4 = "bin4"     # 每位四个阴阳结（二进制编码 0-9）


class Rope(object):
    __slots__ = ("kind", "yao", "value", "places", "dec_style",
                 "note", "role", "children",
                 "x", "y", "bbox", "knots", "head_bbox", "strands",
                 "strand_pts")

    def __init__(self, kind, yao=None, value=1, places=0,
                 dec_style=DEC_TALLY, note="", role=ROLES[0], children=None):
        self.kind = kind
        n = 3 if kind == KIND_TRI else (6 if kind == KIND_HEX else 0)
        self.yao = list(yao) if yao else [0] * n        # 预设全阴
        self.value = int(value)
        self.places = int(places)
        self.dec_style = dec_style
        self.note = note
        self.role = role
        self.children = list(children) if children else []
        # 绘图用（每次重画填）
        self.x = 0
        self.y = 0
        self.bbox = (0, 0, 0, 0)
        self.knots = []
        self.head_bbox = None      # 数字／卦名那行字的范围，点它就地编辑
        self.strands = None        # 卦绳两股的起点与终点 ((上左,上右),(下左,下右))
        self.strand_pts = None     # 两股的完整折点，验「阳结之间有没有张开」用

    # ---- 序列化 ----
    def to_dict(self):
        d = {"kind": self.kind, "note": self.note, "role": self.role,
             "children": [c.to_dict() for c in self.children]}
        if self.kind in (KIND_TRI, KIND_HEX):
            d["yao"] = list(self.yao)
        elif self.kind in KIND_COUNT:
            d["value"] = self.value
            d["places"] = self.places
            d["dec_style"] = self.dec_style
        return d

    @staticmethod
    def from_dict(d):
        r = Rope(d.get("kind", KIND_TRI),
                 yao=d.get("yao"),
                 value=d.get("value", 1),
                 places=d.get("places", 0),
                 dec_style=d.get("dec_style", DEC_TALLY),
                 note=d.get("note", ""),
                 role=d.get("role", ROLES[0]))
        r.children = [Rope.from_dict(c) for c in d.get("children", [])]
        return r

    # ---- 内容 ----
    def cycle(self):
        """循环绳回传 (位数, 名表, 叫法)；不是循环绳回传 None。"""
        return CYCLES.get(self.kind)

    def cval(self):
        cy = self.cycle()
        return cyc_clamp(self.value, cy[0]) if cy else self.value

    def runs(self):
        """一条计数绳画成几段结。

        十进制绳：位值制，由高位到低位，位间打分位阳结，零打大横结。
        地支绳：十二位的循环，亥就是十二个结，一段打完。
        """
        if self.cycle():
            return [self.cval()]
        return digits_of(self.value, self.places, 10)

    def gua(self):
        """回传 (符号, 名称, 序号说明) 或 None。"""
        if self.kind == KIND_TRI:
            t = trigram_name(self.yao)
            return TRI_SYM[t], t, f"八卦·{TRI_IDX[t] + 1}"
        if self.kind == KIND_HEX:
            name, idx, up, low = hexagram_name(self.yao)
            return HEX_SYM[name], name, f"方图 {idx}"
        return None

    def headline(self, want_gan=True):
        """绳子旁边那一行字。"""
        if self.kind == KIND_FEN:
            return "" if self.note else "分段"
        if self.kind == KIND_BIG:
            return "0"
        if self.kind == KIND_SEP:
            return "｜"
        if self.kind == KIND_CUT:
            return "分割"
        cy = self.cycle()
        if cy:
            v = self.cval()
            return f"{v}·{cy[1][v - 1]}" if want_gan else str(v)
        if self.kind == KIND_DEC:
            v = max(0, self.value)
            # 一位数的十进制绳，绳上跟同值的天干绳是同一串结（3 就是三个结），
            # 所以一并注出干名，免得同一排一个有名一个没名。
            # 两位以上不注 —— 十进制的 10 是 1｜分位｜大横结，只有三个结，
            # 跟天干的癸（十个结）不是同一串，注了反而骗人。
            single = want_gan and len(self.runs()) == 1 and 1 <= v <= 9
            nm = cyc_name(v, GAN_MAX) if single else ""
            return f"{v}·{nm}" if nm else str(v)
        g = self.gua()
        return f"{g[0]} {g[1]}"

    def n_levels(self):
        if self.kind in (KIND_TRI, KIND_HEX):
            return len(self.yao)
        if self.kind in (KIND_BIG, KIND_SEP):
            return 1
        if self.kind == KIND_CUT:
            return 0
        if self.cycle():
            return self.cval()
        if self.kind == KIND_DEC:
            ds = self.runs()
            if self.dec_style == DEC_BIN4:
                return len(ds) * 4 + (len(ds) - 1)     # 每位四结，位间空一格
            return sum(max(d, 1) for d in ds) + (len(ds) - 1)
        return 0

    def walk(self):
        yield self
        for c in self.children:
            for r in c.walk():
                yield r


class Doc(object):
    def __init__(self):
        self.ropes = []
        self.title = ""
        self.note = ""          # 我的注释：自己手写的，跟着档案一起存

    def to_dict(self):
        return {"app": APP_NAME, "ver": APP_VER, "title": self.title,
                "note": self.note,
                "ropes": [r.to_dict() for r in self.ropes]}

    @staticmethod
    def from_dict(d):
        doc = Doc()
        doc.title = d.get("title", "")
        doc.note = d.get("note", "")
        doc.ropes = [Rope.from_dict(r) for r in d.get("ropes", [])]
        return doc

    def walk(self):
        for r in self.ropes:
            for x in r.walk():
                yield x

    def parent_of(self, target):
        for r in self.walk():
            if target in r.children:
                return r
        return None

    def remove(self, target):
        p = self.parent_of(target)
        if p is not None:
            p.children.remove(target)
        elif target in self.ropes:
            self.ropes.remove(target)


# ══════════════════════════════════════════════════════════════════════
#  三、示例（照原例）
# ══════════════════════════════════════════════════════════════════════

def _tri(name, note="", role=ROLES[0], children=None):
    return Rope(KIND_TRI, yao=list(TRI_BITS[name]), note=note,
                role=role, children=children)


def _hex(name, note="", role=ROLES[0], children=None):
    """用卦名反推六爻。"""
    idx = FANG_INDEX[name]
    up = TRI_NAME[idx // 8]
    low = TRI_NAME[idx % 8]
    bits = list(TRI_BITS[low]) + list(TRI_BITS[up])
    return Rope(KIND_HEX, yao=bits, note=note, role=role, children=children)


def _dec(v, note="", role="数量·能量级别", places=0, children=None):
    return Rope(KIND_DEC, value=v, places=places, note=note,
                role=role, children=children)


def _gan(v, note="", role="数量·能量级别", children=None):
    return Rope(KIND_GAN, value=v, note=note, role=role, children=children)


def _zhi(v, note="", role="卦时", children=None):
    return Rope(KIND_DUO, value=v, note=note, role=role, children=children)


def _fen(note="", role="卦年"):
    return Rope(KIND_FEN, note=note, role=role)


def _cut(note=""):
    """横绳上一个普通结 —— 栏位与栏位之间的定界符。
    原例里每一段后面都写着「打横结」，就是这个。"""
    return Rope(KIND_CUT, note=note)


def _fields(*groups):
    """把几组绳用分割横结串起来：栏位换了就打一个横结。"""
    out = []
    for g in groups:
        if out:
            out.append(_cut())
        out.extend(g if isinstance(g, (list, tuple)) else [g])
    return out



CONVERT_TO = [(KIND_TRI, "三爻绳"), (KIND_HEX, "六爻绳"),
              (KIND_DEC, "十进制绳"), (KIND_GAN, "十天干绳"),
              (KIND_DUO, "十二地支绳"),
              (KIND_SEP, "分位阳结"),
              (KIND_BIG, "大横结（零）"), (KIND_CUT, "分割横结"),
              (KIND_FEN, "分段绳")]

ALL_SAMPLES = "★ 全部载入成一册（给智者翻）"


def sample_docs():
    s = {}

    # 例一：天气 ＋ 马死了
    d = Doc()
    d.title = "例一　卦年消息卦月：太阳好大，没下雨，马死了"
    d.ropes = _fields(
        _fen("卦年消息卦月", "卦年"),
        _tri("乾", "天（说的是天气）", "事情",
             [_tri("离", "热死了，太阳好大，都只有太阳")]),
        _tri("乾", "马", "事情",
             [_tri("坤", "没了")]),
        _hex("坤为地", "马六爻阴 —— 没了", "事情"),
        _gan(6, "天干六数 ＝ 己（六个结）", "数量·能量级别"),
    )
    s["例一　天旱马死"] = d

    # 例二：出生证明
    d = Doc()
    d.title = "例二　出生证明：某卦年卦月初三，风火家人，六六出生"
    d.ropes = _fields(
        _fen("某卦年", "卦年"),
        _fen("卦月", "卦月"),
        _dec(3, "初三", "卦日"),
        _hex("风火家人", "家里，家人旁", "方位·地点"),
        _dec(66, "六六（他的名字，如朱八八／十三哥／帝辛）", "人",
             children=[_hex("地雷复", "出生")]),
        _dec(1, "1 个人出生", "数量·能量级别"),
    )
    s["例二　出生证明"] = d

    # 例三：死亡记录
    d = Doc()
    d.title = "例三　某卦年卦月十五，风火家人，六六的爸爸死了"
    d.ropes = _fields(
        _fen("某卦年", "卦年"),
        _fen("卦月", "卦月"),
        _dec(15, "十五（月圆夜）", "卦日"),
        _hex("风火家人", "家里，家人旁", "方位·地点"),
        _dec(66, "六六", "人",
             children=[_hex("乾为天", "他爸爸（乾为父）",
                            children=[_hex("坤为地", "死了")])]),
        _dec(1, "1 个人死", "数量·能量级别"),
    )
    s["例三　死亡记录"] = d

    # 例四：战功
    d = Doc()
    d.title = "例四　东方征鬼方，胜，俘二十人"
    d.ropes = _fields(
        _fen("某卦年", "卦年"),
        _fen("卦月", "卦月"),
        _tri("震", "东方卦", "方位·地点"),
        _hex("地水师", "军队", "事情",
             [_hex("火泽睽", "鬼方／睽方／槐方",
                   children=[_hex("乾为天", "胜了")])]),
        _dec(20, "俘虏 20 人", "数量·能量级别"),
    )
    s["例四　东征鬼方"] = d

    # 例五：同一件事写成全军覆没
    d = Doc()
    d.title = "例五　东征鬼方，全军覆没，死二十人"
    d.ropes = _fields(
        _fen("某卦年（一轮六十四年，是哪一轮靠智者记得）", "卦年"),
        _fen("卦月", "卦月"),
        _tri("震", "东方卦", "方位·地点"),
        _hex("地水师", "军队", "事情",
             [_hex("火泽睽", "鬼方／睽方／槐方",
                   children=[_hex("坤为地", "六爻全阴 —— 没了，全军覆没")])]),
        _dec(20, "死了 20 人", "数量·能量级别"),
    )
    s["例五　全军覆没"] = d

    # 例六：长写法，年份整个写出来
    d = Doc()
    d.title = "例六　长写法：3979 年 7 月初三（步骤多一点，但排得出来）"
    d.ropes = _fields(
        _dec(3979, "三千九百七十九年", "卦年"),
        _dec(7, "七月", "卦月"),
        _dec(3, "初三", "卦日"),
        _hex("风火家人", "家里", "方位·地点"),
        _dec(66, "六六", "人", children=[_hex("地雷复", "出生")]),
        _dec(1, "1 个人出生", "数量·能量级别"),
    )
    s["例六　长写法 3979 年"] = d

    # 例七：登基。一个栏位可以连着好几条绳（天＋羊＝天羊国）
    d = Doc()
    d.title = "例七　3979 年 7 月初三，天羊国，辛，登基（火地晋），无人挑战"
    d.ropes = _fields(
        _dec(3979, "三千九百七十九年", "卦年"),
        _dec(7, "七月", "卦月"),
        _dec(3, "初三", "卦日"),
        [_hex("乾为天", "天朝（乾为天＝至高）", "方位·地点"),
         _hex("兑为泽", "羊（兑为羊）＝羌人的羊国", "方位·地点")],
        [_hex("乾为天", "至高的存在", "人"),
         _hex("乾为天", "神王／天王\n我们爸爸的爸爸", "人"),
         _gan(8, "8 号＝辛（八个结）", "人")],
        _hex("火地晋", "登基了（万家灯火／祭坛圣火／灯塔）", "事情"),
        _dec(1, "1 —— 没人挑战", "数量·能量级别"),
    )
    s["例七　登基"] = d

    # 例八：人名 —— 卦象是氏，数字是名
    d = Doc()
    d.title = "例八　人名：水地比＋88 ＝ 小川 88"
    d.note = ("人这一栏，两个横结之间放「卦象＋数字」：\n"
              "卦象是氏，数字是名。水地比（水在地上）＝小川，88 就是名。\n\n"
              "朱重八本名朱八八，父朱五四，祖朱初一，\n"
              "曾祖朱四九，高祖朱百六 —— 同一路数。")
    d.ropes = _fields(
        _dec(3979, "三千九百七十九年", "卦年"),
        _zhi(12, "亥时", "卦时"),
        _hex("风火家人", "家里", "方位·地点"),
        [_hex("水地比", "氏：水在地上 ＝ 小川", "人"),
         _dec(88, "名：88", "人")],
        _hex("地雷复", "出生", "事情"),
        _dec(1, "1 个人出生", "数量·能量级别"),
    )
    s["例八　人名 小川88"] = d

    return s


# ══════════════════════════════════════════════════════════════════════
#  四、绘图常数
# ══════════════════════════════════════════════════════════════════════

BG = "#FAF5E9"          # 羊皮纸底
BEAM_Y = 86             # 横绳 y
BEAM_C = "#6B4420"
ROPE_C = "#9A6B3C"
KNOT_C = "#4E3016"
DASH_C = "#B9A88C"
SEL_C = "#1B6FB3"
TXT_C = "#2E2A24"
DIM_C = "#8C8377"

LEFT_PAD = 90
KNOT_GAP = 32           # 阴阳结的层距（层层叠叠）
DEC_GAP = 15            # 计数结的层距（结绳计数本来就打得密）
FIRST_DY = 40           # 横绳到第一个结
STRAND_DX = 9           # 阴结两股的半距（两个结并排、不连在一起）

# 画布上每一层字：key, 选单文字, 预设开关
DISPLAY_OPTS = [
    ("value", "数值·天干（3·丙）", True),
    ("gan", "　└ 数值后面带干支（·丙 ·亥）", True),
    ("place", "位值注记（3（个位））", False),
    ("guaname", "卦名（乾为天）", True),
    ("fangidx", "　└ 方图序号", True),
    ("yaopos", "爻位（初二三四五上）", True),
    ("note", "旁注", True),
    ("role", "栏位标签（年／月／地点…）", False),
    ("hengjie", "「横结」二字", False),
    ("gapmark", "严谨检查的记号（!／?）", False),
]
GAP_LEVELS = [("极密", 18), ("密", 24), ("中", 32), ("疏", 44)]
DEC_GAP_LEVELS = [("极密", 11), ("密", 15), ("中", 22), ("疏", 30)]
TAIL = 20               # 绳尾
# 列距 ＝ 两条绳的「字宽」之间还要再留多少空。绳与绳的中心距离 ＝
# 左绳半个字宽 ＋ 列距 ＋ 右绳半个字宽，所以底下这个数就是真正的空档。
COL_GAP = 0             # 预设极窄（检视选单可改）
MIN_COL_W = 26          # 一条绳最少占多宽（只是不让光秃秃的绳挤成一条线）
LABEL_PAD = 8           # 字左右各留一点，免得两栏的字贴在一起
COL_GAP_LEVELS = [("极窄", 0), ("窄", 8), ("中", 18), ("宽", 32)]
ROOT_BAND = 26          # 横绳上下这一带，拖进来一律挂横绳（不会变成右接）
BRANCH_DX = 46          # 右接支绳往右偏
BRANCH_DY = 24          # 右接支绳往下落
LABEL_GAP = 16          # 绳尾到文字
FEN_BOTTOM_PAD = 60


# ══════════════════════════════════════════════════════════════════════
#  五、主程式
# ══════════════════════════════════════════════════════════════════════

def pick_font(root, prefer, size, weight="normal"):
    fams = set(tkfont.families(root))
    for f in prefer:
        if f in fams:
            return tkfont.Font(root=root, family=f, size=size, weight=weight)
    return tkfont.Font(root=root, size=size, weight=weight)


CJK_FONTS = ["Microsoft YaHei", "微软雅黑", "SimHei", "黑体",
             "Noto Sans CJK SC", "Source Han Sans SC", "PingFang SC",
             "WenQuanYi Micro Hei", "Arial Unicode MS"]
SYM_FONTS = ["Segoe UI Symbol", "Noto Sans Symbols2", "SimSun", "宋体",
             "Noto Sans CJK SC", "DejaVu Sans"]


class App(object):

    # ---------------- 建构 ----------------
    def __init__(self, root):
        self.root = root
        root.title(f"{APP_NAME} {APP_VER}")
        root.geometry("1480x940")

        self.book = [Doc()]          # 一册 ＝ 好几条横绳，每条横绳一笔记录
        self.bi = 0
        self.path = None
        self.sel = None
        self.dirty = False
        self.undo_stack = []
        self.redo_stack = []

        # 画布上每一层字，都可以打勾开关
        self.opt = {}
        for key, lab, dflt in DISPLAY_OPTS:
            self.opt[key] = tk.BooleanVar(value=dflt)
        self.show_yaopos = self.opt["yaopos"]
        self.show_role = self.opt["role"]

        self.default_dec_style = tk.StringVar(value=DEC_TALLY)
        self.gap_var = tk.IntVar(value=KNOT_GAP)          # 阴阳结距
        self.gapd_var = tk.IntVar(value=DEC_GAP)          # 计数结距
        self.colgap_var = tk.IntVar(value=COL_GAP)        # 两条绳之间的列距
        self.kg = KNOT_GAP
        self.kgd = DEC_GAP
        self.colgap = COL_GAP

        # 拖放状态
        self._sash_done = False
        self.drag = None        # dict(kind=..., rope=..., ghost=[ids])
        self.drop_target = None
        self._edit = None       # 就地改数字的输入框
        self._dec_owner = None  # 数值栏现在代表哪一条绳

        self.f_ui = pick_font(root, CJK_FONTS, 10)
        self.f_ui_b = pick_font(root, CJK_FONTS, 10, "bold")
        self.f_lab = pick_font(root, CJK_FONTS, 10)
        self.f_small = pick_font(root, CJK_FONTS, 8)
        self.f_sym = pick_font(root, SYM_FONTS, 18)
        self.f_sym_big = pick_font(root, SYM_FONTS, 34)
        self.f_mono = pick_font(root, ["Consolas", "DejaVu Sans Mono",
                                       "Courier New"] + CJK_FONTS, 10)
        self.f_note = pick_font(root, CJK_FONTS, 9)

        self._build_menu()
        self._build_body()
        self._bind_keys()

        self.new_doc(ask=False)

    # ---------------- 一册多条横绳 ----------------
    @property
    def doc(self):
        if not self.book:
            self.book = [Doc()]
        self.bi = max(0, min(self.bi, len(self.book) - 1))
        return self.book[self.bi]

    @doc.setter
    def doc(self, d):
        if not self.book:
            self.book = [d]
            self.bi = 0
        else:
            self.bi = max(0, min(self.bi, len(self.book) - 1))
            self.book[self.bi] = d

    def rec_label(self, i, d):
        return f"{i + 1}. {d.title or '（未命名记录）'}"

    def refresh_book_bar(self):
        vals = [self.rec_label(i, d) for i, d in enumerate(self.book)]
        self.cb_rec["values"] = vals
        self.cb_rec.current(self.bi)
        self.lb_cnt.config(text=f"共 {len(self.book)} 条横绳")

    def on_rec_pick(self, e=None):
        i = self.cb_rec.current()
        if 0 <= i < len(self.book) and i != self.bi:
            self.bi = i
            self.sel = None
            self.redraw()

    def rec_step(self, d):
        j = self.bi + d
        if 0 <= j < len(self.book):
            self.bi = j
            self.sel = None
            self.redraw()

    def rec_add(self):
        self.snapshot_book()
        self.book.insert(self.bi + 1, Doc())
        self.bi += 1
        self.sel = None
        self.redraw()

    def rec_del(self):
        if len(self.book) <= 1:
            messagebox.showinfo(APP_NAME, "册里只剩这一条横绳了。")
            return
        if not messagebox.askyesno(APP_NAME, "删掉这一条横绳（整笔记录）？"):
            return
        self.snapshot_book()
        del self.book[self.bi]
        self.bi = max(0, self.bi - 1)
        self.sel = None
        self.redraw()

    def rec_title(self):
        from tkinter import simpledialog
        s = simpledialog.askstring(APP_NAME, "这一条横绳记的是什么？",
                                   initialvalue=self.doc.title,
                                   parent=self.root)
        if s is not None:
            self.snapshot_book()
            self.doc.title = s
            self.redraw()

    def record_summary(self, d):
        """一条横绳压成一行，给智者翻。"""
        old_book, old_bi = self.book, self.bi
        self.book, self.bi = [d], 0
        try:
            return self.plain_sentence()
        finally:
            self.book, self.bi = old_book, old_bi

    def record_haystack(self, d):
        bits = [d.title or "", d.note or ""]
        for r in d.walk():
            bits.append(r.note or "")
            bits.append(r.role)
            if r.cycle():
                cy = r.cycle()
                v = r.cval()
                bits.append(str(v))
                bits.append(cy[1][v - 1])
                bits.append(cy[2])
            elif r.kind == KIND_DEC:
                bits.append(str(r.value))
            elif r.kind == KIND_BIG:
                bits.append("0 大横结 零")
            elif r.kind == KIND_SEP:
                bits.append("分位阳结")
            elif r.kind == KIND_CUT:
                bits.append("分割")
            elif r.kind != KIND_FEN:
                g = r.gua()
                bits.append(g[1])
                if r.kind == KIND_HEX:
                    _, _, up, low = hexagram_name(r.yao)
                    bits.append(up)
                    bits.append(low)
        return " ".join(bits)

    def open_search(self):
        SearchDialog(self.root, self)

    # ---------------- 版面 ----------------
    def _build_menu(self):
        m = tk.Menu(self.root)

        fm = tk.Menu(m, tearoff=0)
        fm.add_command(label="新建", accelerator="Ctrl+N",
                       command=lambda: self.new_doc())
        fm.add_command(label="开启…", accelerator="Ctrl+O", command=self.open_doc)
        fm.add_command(label="储存", accelerator="Ctrl+S", command=self.save_doc)
        fm.add_command(label="另存为…", command=lambda: self.save_doc(True))
        fm.add_separator()
        fm.add_command(label="汇出 SVG…", command=self.export_svg)
        fm.add_command(label="汇出释读 TXT…", command=self.export_txt)
        fm.add_separator()
        fm.add_command(label="离开", command=self.on_close)
        m.add_cascade(label="文件", menu=fm)

        em = tk.Menu(m, tearoff=0)
        em.add_command(label="复原", accelerator="Ctrl+Z", command=self.undo)
        em.add_command(label="重做", accelerator="Ctrl+Y", command=self.redo)
        em.add_separator()
        em.add_command(label="删除选中的绳", accelerator="Del",
                       command=self.del_selected)
        em.add_command(label="清空整条横绳", command=self.clear_all)
        em.add_separator()
        em.add_command(label="补上所有分割横结（栏位之间打横结）",
                       command=self.fix_all_gaps)
        em.add_command(label="只补会读错的那几处",
                       command=lambda: self.fix_all_gaps(True))
        em.add_separator()
        em.add_command(label="清掉这条横绳的所有栏位标签",
                       command=self.clear_roles)
        m.add_cascade(label="编辑", menu=em)

        vm = tk.Menu(m, tearoff=0)
        dm = tk.Menu(vm, tearoff=0)
        for key, lab, _ in DISPLAY_OPTS:
            dm.add_checkbutton(label=lab, variable=self.opt[key],
                               command=self.redraw)
        dm.add_separator()
        dm.add_command(label="全开", command=lambda: self.set_all_opts(True))
        dm.add_command(label="全关（只剩绳和结）",
                       command=lambda: self.set_all_opts(False))
        vm.add_cascade(label="显示哪些字", menu=dm)
        gm = tk.Menu(vm, tearoff=0)
        for lab, v in GAP_LEVELS:
            gm.add_radiobutton(label=f"{lab}（{v}px）", variable=self.gap_var,
                               value=v, command=self.on_gap_change)
        vm.add_cascade(label="阴阳结距", menu=gm)
        gm2 = tk.Menu(vm, tearoff=0)
        for lab, v in DEC_GAP_LEVELS:
            gm2.add_radiobutton(label=f"{lab}（{v}px）", variable=self.gapd_var,
                                value=v, command=self.on_gap_change)
        vm.add_cascade(label="计数结距（十进制绳）", menu=gm2)
        gm3 = tk.Menu(vm, tearoff=0)
        for lab, v in COL_GAP_LEVELS:
            gm3.add_radiobutton(label=f"{lab}（字与字之间再留 {v}px）",
                                variable=self.colgap_var, value=v,
                                command=self.on_gap_change)
        vm.add_cascade(label="列距（两条绳之间）", menu=gm3)
        vm.add_separator()
        vm.add_command(label="版面复位（画布被压没了按这个）",
                       command=self.reset_layout)
        m.add_cascade(label="检视", menu=vm)

        sm = tk.Menu(m, tearoff=0)
        sm.add_radiobutton(label="十进制绳预设：打几个结就是几",
                           variable=self.default_dec_style, value=DEC_TALLY)
        sm.add_radiobutton(label="十进制绳预设：每位四个阴阳结",
                           variable=self.default_dec_style, value=DEC_BIN4)
        m.add_cascade(label="设定", menu=sm)

        xm = tk.Menu(m, tearoff=0)
        xm.add_command(label=ALL_SAMPLES,
                       command=lambda: self.load_sample(ALL_SAMPLES))
        xm.add_separator()
        for name in sample_docs():
            xm.add_command(label=name,
                           command=lambda n=name: self.load_sample(n))
        m.add_cascade(label="示例", menu=xm)

        tm = tk.Menu(m, tearoff=0)
        tm.add_command(label="翻记录／检索整册…", accelerator="Ctrl+F",
                       command=self.open_search)
        tm.add_command(label="倒读验证（绳子结构校验码）…",
                       command=self.show_reverse_check)
        tm.add_command(label="卦年换算／算岁数（村里的智者）…",
                       command=self.open_guanian)
        m.add_cascade(label="工具", menu=tm)

        hm = tk.Menu(m, tearoff=0)
        hm.add_command(label="怎么用", command=self.show_help)
        m.add_cascade(label="说明", menu=hm)

        self.root.config(menu=m)

    def _build_body(self):
        self.status = ttk.Label(self.root, text="", anchor="w",
                                font=self.f_small)
        self.status.pack(fill="x", side="bottom")

        outer = ttk.PanedWindow(self.root, orient="vertical")
        outer.pack(fill="both", expand=True)
        self.outer = outer

        upper = ttk.Frame(outer)
        outer.add(upper, weight=3)

        # --- 右侧面板：装在一个可卷的画布里，面板再长也拉得到 ---
        sideout = ttk.Frame(upper, width=306)
        sideout.pack(side="right", fill="y")
        sideout.pack_propagate(False)
        self.side_canvas = tk.Canvas(sideout, highlightthickness=0,
                                     width=288, bg=BG)
        ssb = ttk.Scrollbar(sideout, orient="vertical",
                            command=self.side_canvas.yview)
        self.side_canvas.configure(yscrollcommand=ssb.set)
        ssb.pack(side="right", fill="y")
        self.side_canvas.pack(side="left", fill="both", expand=True)
        side = ttk.Frame(self.side_canvas)
        self._side_win = self.side_canvas.create_window(
            (0, 0), window=side, anchor="nw")
        side.bind("<Configure>", self._side_resize)
        self.side_canvas.bind("<Configure>", self._side_resize)
        self._build_palette(side)
        self._build_inspector(side)
        self._bind_side_wheel(side)
        self._bind_side_wheel(self.side_canvas)

        # --- 记录册工具列 ---
        left = ttk.Frame(upper)
        left.pack(side="left", fill="both", expand=True)
        bar = ttk.Frame(left)
        bar.pack(fill="x", padx=4, pady=3)
        ttk.Label(bar, text="记录册", font=self.f_ui_b).pack(side="left")
        ttk.Button(bar, text="◀", width=3,
                   command=lambda: self.rec_step(-1)).pack(side="left", padx=2)
        self.cb_rec = ttk.Combobox(bar, state="readonly", font=self.f_small,
                                   width=42)
        self.cb_rec.pack(side="left")
        self.cb_rec.bind("<<ComboboxSelected>>", self.on_rec_pick)
        ttk.Button(bar, text="▶", width=3,
                   command=lambda: self.rec_step(1)).pack(side="left", padx=2)
        ttk.Button(bar, text="改名", width=5,
                   command=self.rec_title).pack(side="left", padx=(8, 1))
        ttk.Button(bar, text="＋新横绳", width=8,
                   command=self.rec_add).pack(side="left", padx=1)
        ttk.Button(bar, text="删这条", width=7,
                   command=self.rec_del).pack(side="left", padx=1)
        ttk.Button(bar, text="翻记录 / 检索…",
                   command=self.open_search).pack(side="left", padx=(10, 1))
        self.lb_cnt = ttk.Label(bar, text="", font=self.f_small,
                                foreground=DIM_C)
        self.lb_cnt.pack(side="left", padx=6)

        # --- 画布 ---
        cframe = ttk.Frame(left)
        cframe.pack(side="left", fill="both", expand=True)
        self.canvas = tk.Canvas(cframe, bg=BG, highlightthickness=0,
                                width=900, height=520)
        hsb = ttk.Scrollbar(cframe, orient="horizontal",
                            command=self.canvas.xview)
        vsb = ttk.Scrollbar(cframe, orient="vertical",
                            command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=hsb.set, yscrollcommand=vsb.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        cframe.rowconfigure(0, weight=1)
        cframe.columnconfigure(0, weight=1)

        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<Double-Button-1>", self.on_canvas_dclick)
        self.canvas.bind("<Button-3>", self.on_canvas_rclick)
        self.canvas.bind("<MouseWheel>", self.on_wheel)
        self.canvas.bind("<Button-4>", lambda e: self.on_wheel(e, +1))
        self.canvas.bind("<Button-5>", lambda e: self.on_wheel(e, -1))
        self.canvas.bind("<Configure>", lambda e: self.redraw())

        # --- 下方注解 ---
        lower = ttk.Frame(outer)
        outer.add(lower, weight=1)
        nb = ttk.Notebook(lower)
        nb.pack(fill="both", expand=True)

        # 释读／全面注解／严谨检查 都是程式每次重画就重写的，
        # 所以设成只读 —— 不然在上面打字，下一次重画就没了。
        # 要自己写字，用「我的注释」那一页，那一页跟着档案一起存。
        f1 = ttk.Frame(nb)
        self.txt_read = tk.Text(f1, wrap="word", font=self.f_lab, height=8,
                                bg="#FFFDF7", relief="flat", padx=10, pady=8)
        sb1 = ttk.Scrollbar(f1, command=self.txt_read.yview)
        self.txt_read.configure(yscrollcommand=sb1.set)
        self.txt_read.pack(side="left", fill="both", expand=True)
        sb1.pack(side="right", fill="y")
        nb.add(f1, text="  释读  ")

        f2 = ttk.Frame(nb)
        self.txt_note = tk.Text(f2, wrap="word", font=self.f_mono, height=8,
                                bg="#FFFDF7", relief="flat", padx=10, pady=8)
        sb2 = ttk.Scrollbar(f2, command=self.txt_note.yview)
        self.txt_note.configure(yscrollcommand=sb2.set)
        self.txt_note.pack(side="left", fill="both", expand=True)
        sb2.pack(side="right", fill="y")
        nb.add(f2, text="  全面注解  ")

        f3 = ttk.Frame(nb)
        topb = ttk.Frame(f3, padding=6)
        topb.pack(fill="x")
        self.lb_chk = ttk.Label(topb, text="", font=self.f_ui_b)
        self.lb_chk.pack(side="left")
        ttk.Button(topb, text="全部补上分割横结",
                   command=self.fix_all_gaps).pack(side="right")
        ttk.Button(topb, text="倒读验证",
                   command=self.show_reverse_check).pack(side="right", padx=6)
        ttk.Button(topb, text="只补「必须」的",
                   command=lambda: self.fix_all_gaps(True)
                   ).pack(side="right", padx=6)
        self.tv_chk = ttk.Treeview(f3, columns=("lv", "pos", "why"),
                                   show="headings", selectmode="browse")
        for c, t, w in (("lv", "", 60), ("pos", "插在第", 70),
                        ("why", "为什么会读错", 900)):
            self.tv_chk.heading(c, text=t)
            self.tv_chk.column(c, width=w, anchor="w")
        self.tv_chk.configure(height=6)
        self.tv_chk.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        self.tv_chk.bind("<Double-Button-1>", self.on_chk_fix)
        self.chk_rows = []
        nb.add(f3, text="  严谨检查  ")

        f4 = ttk.Frame(nb)
        ttk.Label(f4, text="这一页是你自己写的，跟着档案一起存"
                          "（上面三页是程式算出来的，改不了）",
                  font=self.f_small, foreground=DIM_C).pack(
            anchor="w", padx=8, pady=(6, 2))
        self.txt_mine = tk.Text(f4, wrap="word", font=self.f_lab, height=8,
                                bg="#FFFEF9", relief="solid", bd=1,
                                padx=10, pady=8, undo=True)
        sb4 = ttk.Scrollbar(f4, command=self.txt_mine.yview)
        self.txt_mine.configure(yscrollcommand=sb4.set)
        self.txt_mine.pack(side="left", fill="both", expand=True,
                           padx=(8, 0), pady=(0, 8))
        sb4.pack(side="right", fill="y", pady=(0, 8))
        self.txt_mine.bind("<KeyRelease>", self.on_mine_change)
        self._mine_owner = None
        nb.add(f4, text="  我的注释  ")
        self.nb = nb

        self.outer.bind("<Configure>", self._on_outer_configure)
        self.root.after(60, self._init_sash)

    def _side_resize(self, e=None):
        try:
            self.side_canvas.configure(
                scrollregion=self.side_canvas.bbox("all"))
            self.side_canvas.itemconfig(
                self._side_win, width=self.side_canvas.winfo_width())
        except tk.TclError:
            pass

    def _side_wheel(self, e, direction=None):
        step = direction if direction is not None else (
            1 if getattr(e, "delta", 0) > 0 else -1)
        self.side_canvas.yview_scroll(-step, "units")
        return "break"

    def _bind_side_wheel(self, w):
        """面板里每个控件的滚轮都卷面板 —— Text 除外，它自己要卷。"""
        if w.winfo_class() not in ("Text", "TCombobox", "Spinbox"):
            w.bind("<MouseWheel>", self._side_wheel)
            w.bind("<Button-4>", lambda e: self._side_wheel(e, 1))
            w.bind("<Button-5>", lambda e: self._side_wheel(e, -1))
        for c in w.winfo_children():
            self._bind_side_wheel(c)

    SASH_RATIO = 0.70
    SASH_MIN_TOP = 140      # 画布再怎么样也不该比这个矮

    def _init_sash(self, force=False):
        """摆分隔条。

        陷阱：窗口刚建出来时 PanedWindow 只有 1px 高，这时候呼叫 sashpos()
        会被钳到 0 —— 画布连同右边面板整个被压没，开起来只剩下面三页。
        所以一定要等它真的长大了才设，没长大就再等一轮。
        """
        try:
            h = self.outer.winfo_height()
        except tk.TclError:
            return
        if h < 300:
            self.root.after(120, self._init_sash)
            return
        if self._sash_done and not force:
            return
        try:
            self.outer.sashpos(0, int(h * self.SASH_RATIO))
            self._sash_done = True
        except tk.TclError:
            return
        # 开机后再回头看几次。这个 bug 在 Linux 上复现不出来（ttk 会自己
        # 回弹），所以除了照最可能的成因修，还留这一层跟成因无关的兜底：
        # 只要开头两秒内画布被压扁，就摆回来。
        for ms in (300, 900, 1800):
            self.root.after(ms, self._sash_guard)

    def _sash_guard(self):
        try:
            h = self.outer.winfo_height()
            if h >= 420 and self.outer.sashpos(0) < self.SASH_MIN_TOP:
                self.outer.sashpos(0, int(h * self.SASH_RATIO))
                self.set_status("画布被压扁了，已经摆回来"
                                "（检视 → 版面复位 也可以手动摆）。")
        except tk.TclError:
            pass

    def _on_outer_configure(self, e=None):
        """窗口一变大就补设；万一画布被压没了，自己救回来。"""
        try:
            h = self.outer.winfo_height()
            if h < 300:
                return
            if not self._sash_done:
                self._init_sash()
                return
            if self.outer.sashpos(0) < 40:      # 等于没了
                self.outer.sashpos(0, int(h * self.SASH_RATIO))
        except tk.TclError:
            pass

    def reset_layout(self):
        self._sash_done = False
        self._init_sash(force=True)
        self._side_resize()
        self.redraw()

    def _build_palette(self, side):
        box = ttk.LabelFrame(side, text=" 拖放面板　按住往左边拖 ")
        box.pack(fill="x", padx=6, pady=(6, 4))

        items = [
            (KIND_FEN, "⋮", "长虚线分段绳",
             "横绳打一个结＋超长虚线\n（古人只打一个横结）"),
            (KIND_TRI, "☰", "三爻绳", "三个阴阳结＝一个八卦"),
            (KIND_HEX, "䷀", "六爻绳", "六个阴阳结＝一个六十四卦"),
            (KIND_DEC, "❻", "十进制绳",
             "位值制，十进一。\n十五＝十位1结｜阳结｜个位5结"),
            (KIND_GAN, "⑩", "十天干绳",
             "十位的循环，一位一个结。\n甲＝1 结，癸＝10 结"),
            (KIND_DUO, "⑫", "十二地支绳",
             "十二位的循环，一位一个结。\n子＝1 结，亥＝12 结"),
            (KIND_BIG, "▬", "大横结＝零", "三个结那么宽。零不留空白"),
            (KIND_SEP, "▬", "分位阳结", "两个结那么宽。\n12＝1｜阳结｜2"),
            (KIND_CUT, "•", "分割（普通横结）",
             "横绳上一个普通结而已，底下不挂东西"),
        ]
        for kind, sym, name, tip in items:
            tile = tk.Frame(box, bd=1, relief="raised", bg="#F3EADA",
                            cursor="hand2")
            tile.pack(fill="x", padx=6, pady=3)
            l1 = tk.Label(tile, text=sym, font=self.f_sym, bg="#F3EADA",
                          fg=KNOT_C, width=3)
            l1.pack(side="left")
            rr = tk.Frame(tile, bg="#F3EADA")
            rr.pack(side="left", fill="x", expand=True, pady=3)
            l2 = tk.Label(rr, text=name, font=self.f_ui_b, bg="#F3EADA",
                          fg=TXT_C, anchor="w")
            l2.pack(fill="x")
            l3 = tk.Label(rr, text=tip, font=self.f_small, bg="#F3EADA",
                          fg=DIM_C, anchor="w", justify="left")
            l3.pack(fill="x")
            for w in (tile, l1, l2, l3, rr):
                w.bind("<ButtonPress-1>",
                       lambda e, k=kind: self.palette_press(k))
                w.bind("<B1-Motion>", self.palette_motion)
                w.bind("<ButtonRelease-1>", self.palette_release)
                w.bind("<Double-Button-1>",
                       lambda e, k=kind: self.append_root(k))

        ttk.Label(box, text="拖到空白处＝挂上横绳；拖到某条绳上＝右接支绳\n"
                            "双击＝直接加到最右边",
                  font=self.f_small, foreground=DIM_C,
                  justify="left").pack(fill="x", padx=8, pady=(2, 6))

    def _build_inspector(self, side):
        box = ttk.LabelFrame(side, text=" 这条绳 ")
        box.pack(fill="both", expand=True, padx=6, pady=4)

        self.lb_sym = tk.Label(box, text="—", font=self.f_sym_big,
                               fg=KNOT_C)
        self.lb_sym.pack(pady=(6, 0))
        self.lb_name = ttk.Label(box, text="（未选）", font=self.f_ui_b,
                                 anchor="center")
        self.lb_name.pack(fill="x")
        self.lb_idx = ttk.Label(box, text="", font=self.f_small,
                                foreground=DIM_C, anchor="center")
        self.lb_idx.pack(fill="x", pady=(0, 6))

        row = ttk.Frame(box)
        row.pack(fill="x", padx=6, pady=2)
        ttk.Label(row, text="栏位", font=self.f_small, width=5).pack(side="left")
        self.cb_role = ttk.Combobox(row, values=ROLES, state="readonly",
                                    font=self.f_small, width=16)
        self.cb_role.pack(side="left", fill="x", expand=True)
        self.cb_role.bind("<<ComboboxSelected>>", self.on_role_change)

        self.dec_row = ttk.Frame(box)
        ttk.Label(self.dec_row, text="数值", font=self.f_small,
                  width=5).pack(side="left")
        self.sp_val = tk.Spinbox(self.dec_row, from_=0, to=999999, width=7,
                                 font=self.f_small, command=self.on_dec_change)
        self.sp_val.pack(side="left")
        self.sp_val.bind("<Return>", lambda e: self.on_dec_change())
        self.sp_val.bind("<FocusOut>", lambda e: self.on_dec_change())
        ttk.Label(self.dec_row, text="位数", font=self.f_small,
                  width=4).pack(side="left", padx=(6, 0))
        self.sp_pla = tk.Spinbox(self.dec_row, from_=0, to=6, width=3,
                                 font=self.f_small, command=self.on_dec_change)
        self.sp_pla.pack(side="left")

        self.dec_row2 = ttk.Frame(box)
        ttk.Label(self.dec_row2, text="结法", font=self.f_small,
                  width=5).pack(side="left")
        self.cb_dec = ttk.Combobox(self.dec_row2, state="readonly",
                                   font=self.f_small, width=16,
                                   values=["打几个结就是几", "每位四个阴阳结"])
        self.cb_dec.pack(side="left", fill="x", expand=True)
        self.cb_dec.bind("<<ComboboxSelected>>", self.on_decstyle_change)

        ttk.Label(box, text="旁注", font=self.f_small).pack(
            anchor="w", padx=6, pady=(6, 0))
        self.tx_note = tk.Text(box, height=3, wrap="word", font=self.f_note,
                               relief="solid", bd=1)
        self.tx_note.pack(fill="x", padx=6)
        self.tx_note.bind("<KeyRelease>", self.on_note_change)

        bar = ttk.Frame(box)
        bar.pack(fill="x", padx=6, pady=5)
        ttk.Button(bar, text="←", width=3,
                   command=lambda: self.move_sel(-1)).pack(side="left")
        ttk.Button(bar, text="→", width=3,
                   command=lambda: self.move_sel(1)).pack(side="left", padx=2)
        ttk.Button(bar, text="删除", width=6,
                   command=self.del_selected).pack(side="right")

        bar2 = ttk.Frame(box)
        bar2.pack(fill="x", padx=6)
        ttk.Label(bar2, text="右接：", font=self.f_small).pack(side="left")
        for kind, t in ((KIND_TRI, "三爻"), (KIND_HEX, "六爻")):
            ttk.Button(bar2, text=t, width=5,
                       command=lambda k=kind: self.add_branch(k)
                       ).pack(side="left", padx=1)

        bar3 = ttk.Frame(box)
        bar3.pack(fill="x", padx=6, pady=(4, 0))
        ttk.Label(bar3, text="换成：", font=self.f_small).pack(side="left")
        self.cb_conv = ttk.Combobox(bar3, state="readonly", width=13,
                                    font=self.f_small,
                                    values=[t for _, t in CONVERT_TO])
        self.cb_conv.pack(side="left", fill="x", expand=True)
        self.cb_conv.bind("<<ComboboxSelected>>", self.on_convert_pick)

        ttk.Label(box, text="速查", font=self.f_small).pack(
            anchor="w", padx=6, pady=(8, 0))
        self.tx_ref = tk.Text(box, height=11, wrap="word", font=self.f_small,
                              bg="#FFFDF7", relief="solid", bd=1)
        self.tx_ref.pack(fill="both", expand=True, padx=6, pady=(0, 6))

    def _bind_keys(self):
        r = self.root
        r.protocol("WM_DELETE_WINDOW", self.on_close)
        r.bind("<Control-n>", lambda e: self.new_doc())
        r.bind("<Control-o>", lambda e: self.open_doc())
        r.bind("<Control-s>", lambda e: self.save_doc())
        r.bind("<Control-z>", lambda e: self.undo())
        r.bind("<Control-y>", lambda e: self.redo())
        r.bind("<Control-f>", lambda e: self.open_search())
        r.bind("<Prior>", lambda e: self.rec_step(-1))
        r.bind("<Next>", lambda e: self.rec_step(1))
        r.bind("<Delete>", lambda e: self._del_if_not_typing())

    def _typing(self):
        w = self.root.focus_get()
        return w is not None and w.winfo_class() in (
            "Entry", "TEntry", "Text", "Spinbox", "TCombobox", "Listbox")

    def _del_if_not_typing(self):
        if not self._typing():
            self.del_selected()

    # ---------------- 复原（整册一起存，换记录也复原得回来）----------------
    def book_blob(self):
        return json.dumps({"bi": self.bi,
                           "records": [d.to_dict() for d in self.book]},
                          ensure_ascii=False)

    def snapshot(self):
        self.undo_stack.append(self.book_blob())
        del self.undo_stack[:-80]
        self.redo_stack = []
        self.dirty = True

    snapshot_book = snapshot

    def _restore(self, blob):
        o = json.loads(blob)
        self.book = [Doc.from_dict(x) for x in o["records"]] or [Doc()]
        self.bi = max(0, min(o.get("bi", 0), len(self.book) - 1))
        self.sel = None
        self.redraw()

    def undo(self):
        if not self.undo_stack:
            return
        self.redo_stack.append(self.book_blob())
        self._restore(self.undo_stack.pop())

    def redo(self):
        if not self.redo_stack:
            return
        self.undo_stack.append(self.book_blob())
        self._restore(self.redo_stack.pop())

    # ---------------- 版面计算 ----------------
    def rope_height(self, r):
        """绳身像素高（横绳／接点 到 绳尾）。"""
        if r.kind == KIND_FEN:
            return FIRST_DY
        if r.kind == KIND_CUT:
            return 8
        n = r.n_levels()
        gap = self.kgd if r.kind == KIND_DEC else self.kg
        return FIRST_DY + max(0, n - 1) * gap + TAIL

    def label_width(self, r):
        pad = LABEL_PAD * 2
        w = self.f_lab.measure(self.head_text(r)) + pad
        if self.O("note"):
            for line in (r.note or "").splitlines():
                w = max(w, self.f_note.measure(line) + pad)
        if self.O("role") and r.role != ROLES[0]:
            w = max(w, self.f_small.measure(r.role) + pad)
        if r.kind in KIND_COUNT and self.O("place"):
            w = max(w, 176)          # 位值注记贴在绳的右边，要留位
        if r.kind in (KIND_CUT, KIND_SEP, KIND_BIG):
            w = min(w, 34)           # 分隔用的结夹在中间，不占栏子
        return w

    def head_text(self, r):
        """绳尾那行字，按勾选决定给不给。"""
        if r.kind in (KIND_TRI, KIND_HEX):
            return r.headline() if self.O("guaname") else ""
        if r.kind in KIND_COUNT:
            return r.headline(self.O("gan")) if self.O("value") else ""
        return r.headline()

    def half_w(self, r):
        """绳身左右各要留多少（字是置中写的）。"""
        if r.kind in (KIND_CUT, KIND_SEP, KIND_BIG):
            return self.label_width(r) / 2.0
        return max(MIN_COL_W, self.label_width(r)) / 2.0

    def layout(self, r, x, y):
        """放好 r 与它的右接支绳；回传这一支往右伸到哪（相对 x）。"""
        r.x, r.y = x, y
        right = max(self.half_w(r),
                    136 if (r.kind in KIND_COUNT
                            and self.O("place")) else 0)
        bottom = y + self.rope_height(r)
        cy = bottom + BRANCH_DY
        cx = x + BRANCH_DX
        for c in r.children:
            cx = max(cx, x + BRANCH_DX) + self.half_w(c)
            w = self.layout(c, cx, cy)
            right = max(right, cx - x + w)
            cx = cx + w + 10
        return right

    def layout_all(self):
        right = 0.0
        for r in self.doc.ropes:
            half = self.half_w(r)
            x = max(LEFT_PAD + half, right + self.colgap + half)
            w = self.layout(r, x, BEAM_Y)
            right = x + w
        return right + 60

    def subtree_bottom(self, r):
        b = r.y + self.rope_height(r)
        for c in r.children:
            b = max(b, self.subtree_bottom(c))
        return b

    # ---------------- 绘图 ----------------
    def redraw(self):
        if self._edit:
            self._close_edit()
        c = self.canvas
        c.delete("all")
        total_w = self.layout_all()
        bottom = BEAM_Y + 200
        for r in self.doc.ropes:
            bottom = max(bottom, self.subtree_bottom(r))
        total_h = bottom + 120
        vw = max(c.winfo_width(), 10)
        vh = max(c.winfo_height(), 10)
        total_w = max(total_w, vw)
        total_h = max(total_h, vh)
        c.configure(scrollregion=(0, 0, total_w, total_h))

        # 横绳（太极）
        c.create_line(20, BEAM_Y, total_w - 20, BEAM_Y,
                      fill=BEAM_C, width=7, capstyle="round")
        c.create_line(20, BEAM_Y - 2, total_w - 20, BEAM_Y - 2,
                      fill="#8A5B2E", width=2)
        c.create_text(22, 20, text="太极 · 横绳", anchor="nw",
                      font=self.f_ui_b, fill=BEAM_C)

        self.fen_bottom = total_h - FEN_BOTTOM_PAD
        for r in self.doc.ropes:
            self.draw_rope(r, root=True)

        self.refresh_book_bar()
        self.refresh_mine()
        self.refresh_text()
        self.refresh_check()
        self.draw_gap_marks()
        self.refresh_inspector()

    # 结的尺寸阶梯，一个结 ＝ 一个单位（半宽 KNOT_U）：
    #   1 个 ＝ 一个结，也就是「半个阴爻」—— 阴爻是两个这样的结，
    #          并排、不连在一起；计数结用的也是这个
    #   2 个 ＝ 阳结 —— 两个阴爻结绑在一起（或一条绳绑两次），宽一点；
    #          十进制绳的分位结用的就是它
    #   3 个 ＝ 大横结，零，最大
    # tie 是横绳上那个普通结；分割就只是这么一个结，不是大横结。
    KNOT_U = 6
    KNOT_SIZE = {"count": (KNOT_U, 5), "yin": (KNOT_U, 5),
                 "yang": (KNOT_U * 2, 5), "big": (KNOT_U * 3, 5),
                 "tie": (8, 5)}

    def draw_gap_marks(self):
        """会读错的缝，在横绳上标出来；点一下就在那里补一个分割横结。"""
        c = self.canvas
        self.gap_marks = []
        if not self.O("gapmark"):
            return
        for d in self.check_issues():
            if d["level"] not in self.GAP_LEVELS:
                continue
            x = self.caret_x(d["idx"])
            must = d["level"] == "必须"
            col = "#C0392B" if must else "#D79A1E"
            c.create_line(x, BEAM_Y - 22, x, BEAM_Y + 22, fill=col,
                          width=2, dash=(3, 3), tags="gapmark")
            c.create_oval(x - 9, BEAM_Y - 40, x + 9, BEAM_Y - 22,
                          fill="#FFF4E0", outline=col, width=2,
                          tags="gapmark")
            c.create_text(x, BEAM_Y - 31, text="!" if must else "?",
                          font=self.f_ui_b, fill=col, tags="gapmark")
            self.gap_marks.append((x, BEAM_Y - 31, d["idx"]))

    def gap_mark_at(self, wx, wy):
        for x, y, idx in getattr(self, "gap_marks", []):
            if abs(wx - x) <= 12 and abs(wy - y) <= 12:
                return idx
        return None

    def _knot(self, x, y, style, tag, sel=False):
        """画一颗结。
        yang 合股一结 ｜ yin 分股单边 ｜ count 计数结 ｜ tie 横绳上的普通结
        big  大横结 —— 零。零不能留空白，留空白别人分不出是绳编长了还是零，
             就跟阴爻不能留空一样：两边都要打结，只是不连在一起。
        """
        c = self.canvas
        w, h = self.KNOT_SIZE[style]
        if sel:
            c.create_oval(x - w - 4, y - h - 4, x + w + 4, y + h + 4,
                          outline="", fill="#FFE9A8", tags=tag)
        if style == "big":
            # 一道横过绳身的粗结，形状跟圆结明显不同
            c.create_rectangle(x - w, y - h, x + w, y + h,
                               fill=KNOT_C, outline="#2C1A08", width=1,
                               tags=tag)
            for dx in (-w / 3.0, w / 3.0):
                c.create_line(x + dx, y - h, x + dx, y + h,
                              fill="#C8996A", width=2, tags=tag)
            c.create_line(x - w, y - h, x + w, y - h,
                          fill="#C8996A", width=2, tags=tag)
            return
        c.create_oval(x - w, y - h, x + w, y + h,
                      fill=KNOT_C, outline="#2C1A08", width=1, tags=tag)
        c.create_arc(x - w + 1, y - h - 2, x + w - 1, y + h - 1,
                     start=210, extent=120, style="arc",
                     outline="#C8996A", width=2, tags=tag)

    def _strands(self, x, pts, tag, top):
        """卦绳的底层画法：一条绳对折挂在横绳上，所以是两股。

        顶上两股、底下两股，中间每一爻 ——
            阳 ＝ 两股绑在一起（合股，一个结）
            阴 ＝ 两股各打各的（分股，两个结，不连在一起）
        绳尾两股散开，不收成一点。

        pts ＝ [(y, off)]，off 0 表示合股（阳），>0 表示分股（阴）。
        top ＝ 这条绳的起点 y（根绳是横绳，支绳是它自己的接点）。
        """
        c = self.canvas
        d = STRAND_DX
        hold = max(4.0, min(self.kg * 0.22, 9.0))   # 出结就张开，别拖泥带水
        left = [(x - d, top)]
        right = [(x + d, top)]
        self._last_strands = None
        # 两股平时是张开的；只有走到一个爻上才收拢或维持。
        #   阳 ＝ 收拢绑死 -> 闭合，穿不过去（一画开天）
        #   阴 ＝ 各走各的 -> 中间留着洞，穿得过去
        # 两个阳结之间一定要看得到张开的那个环 —— 所以结与结的中间
        # 再补一个 ±d 的点撑住，不然样条会把那一段抹成直线。
        prev_y = top
        for y, off in pts:
            mid = (prev_y + y) / 2.0
            if mid > prev_y + 1 and mid < y - hold:
                left.append((x - d, mid))
                right.append((x + d, mid))
            left.append((x - d, y - hold))
            right.append((x + d, y - hold))
            left.append((x - off, y))
            right.append((x + off, y))
            left.append((x - d, y + hold))
            right.append((x + d, y + hold))
            prev_y = y + hold
        ey = pts[-1][0] + TAIL if pts else top + TAIL
        left.append((x - d, ey))     # 结尾也是两条绳
        right.append((x + d, ey))
        self._last_strands = (((x - d, top), (x + d, top)),
                              ((x - d, ey), (x + d, ey)))
        self._last_pts = (list(left), list(right))
        flat_l = [v for p in left for v in p]
        flat_r = [v for p in right for v in p]
        c.create_line(*flat_l, fill=ROPE_C, width=3, tags=tag, smooth=True,
                      capstyle="round", joinstyle="round")
        c.create_line(*flat_r, fill=ROPE_C, width=3, tags=tag, smooth=True,
                      capstyle="round", joinstyle="round")

    def draw_rope(self, r, root=False, anchor=None):
        """anchor ＝ (ax, ay) 支绳的接点；root 绳则接在横绳上。"""
        c = self.canvas
        tag = f"rope{id(r)}"
        x = r.x
        top = r.y
        sel = (r is self.sel)
        r.knots = []

        # --- 接点：横绳上的那个结只是普通一个结，不是阳结 ---
        if root:
            self._knot(x, BEAM_Y, "tie", tag)
            if self.O("hengjie"):
                c.create_text(x, BEAM_Y - 18, text="横结", font=self.f_small,
                              fill=DIM_C, tags=tag)
        else:
            # 右接 ＝ 绳子开叉。
            # 卦绳是双股的（阴＝两股分开，阳＝两股绑一起），所以叉得开：
            # 右边那一股拉出去，就成了支绳。单股的计数绳没得叉 ——
            # 「一条绳怎样右接」，所以只有卦绳能右接。
            # 右接 ＝ 把支绳系在母绳的绳尾上，只系右边。
            # 卦绳是对折的两股，尾巴散开成两条，就系在右边那条上；
            # 计数绳是单股（天干地支那种），就系在它那一条尾巴上。
            # 母绳是什么绳都行（例三就是「六六→乾为天」），
            # 受限的是支绳自己 —— 右边接出去那条一定是卦绳。
            ax, ay = anchor
            mid = (ay + top) / 2.0
            c.create_line(ax, ay, ax + 8, ay + 8, x - 12, mid,
                          x, mid + 10, x, top,
                          fill=ROPE_C, width=3, tags=tag, smooth=True,
                          capstyle="round", joinstyle="round")
            self._knot(x, top, "count", tag)      # 系上去那个结

        pts = []        # [(y, off)] 给 _strands
        bottom = top

        if r.kind == KIND_FEN:
            # 超长虚线：古人只在横绳打一个结，虚线只是给眼睛看的
            c.create_line(x, BEAM_Y, x, self.fen_bottom, fill=DASH_C,
                          width=2, dash=(3, 5), tags=tag)
            bottom = top + FIRST_DY
        elif r.kind in (KIND_BIG, KIND_SEP):
            y = top + FIRST_DY
            c.create_line(x, top, x, y + TAIL, fill=ROPE_C, width=3, tags=tag)
            self._knot(x, y, "big" if r.kind == KIND_BIG else "yang",
                       tag, sel)
            bottom = y + TAIL
        elif r.kind == KIND_CUT:
            # 分割 ＝ 横绳上一个普通结而已，底下什么都不挂
            self._knot(x, BEAM_Y, "tie", tag, sel)
            bottom = top + 6
        elif r.kind in (KIND_TRI, KIND_HEX):
            n = len(r.yao)
            for row in range(n):
                # 最靠近横绳的是上爻 -> 由上往下 yao index 递减
                yi = n - 1 - row
                y = top + FIRST_DY + row * self.kg
                yang = r.yao[yi] == 1
                pts.append((y, 0 if yang else STRAND_DX))
                r.knots.append((x, y, ("yao", yi)))
            self._strands(x, pts, tag, top)
            r.strands = self._last_strands
            r.strand_pts = self._last_pts
            for row in range(n):
                yi = n - 1 - row
                y = top + FIRST_DY + row * self.kg
                if r.yao[yi] == 1:
                    self._knot(x, y, "yang", tag, sel)
                else:
                    self._knot(x - STRAND_DX, y, "yin", tag, sel)
                    self._knot(x + STRAND_DX, y, "yin", tag, sel)
                if self.O("yaopos"):
                    names = YAO_POS if n == 6 else YAO_POS3
                    c.create_text(x - 32, y, text=names[yi],
                                  font=self.f_small, fill=DIM_C, tags=tag)
            bottom = top + FIRST_DY + (n - 1) * self.kg + TAIL
        elif r.kind in KIND_COUNT:
            bottom = self._draw_dec(r, x, top, tag, sel)

        rx = 132 if (r.kind in KIND_COUNT
                     and self.O("place")) else 40
        r.bbox = (x - 40, top - (18 if not root else 34), x + rx, bottom + 8)

        # --- 绳旁的卦象与旁注 ---
        ty = bottom + LABEL_GAP
        if self.O("role") and r.role != ROLES[0]:
            c.create_text(x, top - (32 if root else 26), text=r.role,
                          font=self.f_small, fill="#7A5C2E", tags=tag)
        head = self.head_text(r)
        r.head_bbox = None
        if head:
            small = r.kind in (KIND_CUT, KIND_SEP)
            c.create_text(x, ty, text=head,
                          font=self.f_small if small else self.f_lab,
                          fill=SEL_C if sel else (DIM_C if small else TXT_C),
                          tags=tag)
            hw = self.f_lab.measure(head) / 2.0 + 8
            r.head_bbox = (x - hw, ty - 11, x + hw, ty + 11)
            ty += 16
        g = r.gua()
        if (g and r.kind == KIND_HEX and self.O("guaname")
                and self.O("fangidx")):
            c.create_text(x, ty, text=g[2], font=self.f_small, fill=DIM_C,
                          tags=tag)
            ty += 14
        if self.O("note"):
            for line in (r.note or "").splitlines():
                c.create_text(x, ty, text=line, font=self.f_note,
                              fill="#5B4A32", tags=tag)
                ty += 14

        if sel:
            c.create_rectangle(r.bbox[0], r.bbox[1], r.bbox[2], ty,
                               outline=SEL_C, dash=(3, 3), tags=tag)

        # --- 右接支绳 ---
        for ch in r.children:
            # 叉口开在母绳最后一个结那一层的右股上，不是绳尾底下 ——
            # 这样看得出是同一条绳分出去的。
            # 系在母绳右股的绳尾上（两股散开的那两条里，右边那条）
            fork_y = bottom if r.kind in (KIND_TRI, KIND_HEX) else bottom - 4
            fork_x = x + (STRAND_DX if r.kind in (KIND_TRI, KIND_HEX) else 8)
            self.draw_rope(ch, root=False, anchor=(fork_x, fork_y))

    def _draw_dec(self, r, x, top, tag, sel):
        """十进制绳：位值制。由上往下 高位 -> 个位。"""
        c = self.canvas
        ds = r.runs()
        g = self.kgd
        row = 0
        y = top
        place_names = PLACE_NAMES[10]

        cy = r.cycle()

        def pname(pi):
            if cy:
                return f"{cy[2]}·{cy[1][r.cval() - 1]}"
            return place_names[min(len(ds) - 1 - pi, len(place_names) - 1)]

        if r.dec_style == DEC_BIN4:
            pts = []
            for pi, d in enumerate(ds):
                for b in range(4):          # 上面是 8 位元，下面是 1 位元
                    bit = (d >> (3 - b)) & 1
                    y = top + FIRST_DY + row * g
                    pts.append((y, 0 if bit else STRAND_DX))
                    row += 1
                if pi < len(ds) - 1:
                    y = top + FIRST_DY + row * g
                    pts.append((y, 0))
                    row += 1
            self._strands(x, pts, tag, top)
            row = 0
            for pi, d in enumerate(ds):
                y0 = top + FIRST_DY + row * g
                for b in range(4):
                    bit = (d >> (3 - b)) & 1
                    y = top + FIRST_DY + row * g
                    if bit:
                        self._knot(x, y, "yang", tag, sel)
                    else:
                        self._knot(x - STRAND_DX, y, "yin", tag, sel)
                        self._knot(x + STRAND_DX, y, "yin", tag, sel)
                    row += 1
                if self.O("place"):
                    c.create_text(x + 32, (y0 + y) / 2.0,
                                  text=f"{d}（{pname(pi)}位）", anchor="w",
                                  font=self.f_small, fill="#7A5C2E", tags=tag)
                if pi < len(ds) - 1:
                    row += 1
            return top + FIRST_DY + max(0, row - 1) * g + TAIL

        # tally：每一位打几个结就是几；零打一个大横结，不留空白
        show_place = self.O("place")
        c.create_line(x, top, x, top + FIRST_DY, fill=ROPE_C, width=3,
                      tags=tag)
        for pi, d in enumerate(ds):
            y0 = top + FIRST_DY + row * g
            cnt = max(d, 1)
            y1 = top + FIRST_DY + (row + cnt - 1) * g
            c.create_line(x, y0 - g * 0.4, x, y1 + g * 0.4,
                          fill=ROPE_C, width=3, tags=tag)
            if d == 0:
                y = y0
                self._knot(x, y, "big", tag, sel)
                row += 1
                if show_place:
                    c.create_text(x + 34, y, text=f"0（{pname(pi)}位）",
                                  font=self.f_small, fill="#7A5C2E",
                                  anchor="w", tags=tag)
            else:
                for k in range(d):
                    y = top + FIRST_DY + row * g
                    self._knot(x, y, "count", tag, sel)
                    row += 1
                if show_place:
                    c.create_text(x + 20, (y0 + y1) / 2.0,
                                  text=(f"{d}（{pname(pi)}）" if cy
                                        else f"{d}（{pname(pi)}位）"),
                                  font=self.f_small, fill="#7A5C2E",
                                  anchor="w", tags=tag)
            if pi < len(ds) - 1:
                # 分位：打一个两个结宽的阳结，不留空白 —— 12 要读成 1｜2，
                # 3979 要读成 3｜9｜7｜9，中间空一段谁也分不清。
                ym = top + FIRST_DY + row * g
                c.create_line(x, ym - g * 0.5, x, ym + g * 0.5,
                              fill=ROPE_C, width=3, tags=tag)
                self._knot(x, ym, "yang", tag, sel)
                row += 1
        yend = top + FIRST_DY + max(0, row - 1) * g
        c.create_line(x, yend, x, yend + TAIL, fill=ROPE_C, width=3, tags=tag)
        return yend + TAIL

    # ---------------- 命中测试 ----------------
    def rope_at(self, wx, wy, exclude=None):
        """最深的、bbox 含住这一点的绳。"""
        best = None

        def rec(r, depth):
            nonlocal best
            if exclude is not None and r is exclude:
                return
            x0, y0, x1, y1 = r.bbox
            if x0 <= wx <= x1 and y0 <= wy <= y1:
                if best is None or depth >= best[1]:
                    best = (r, depth)
            for c in r.children:
                rec(c, depth + 1)

        for r in self.doc.ropes:
            rec(r, 0)
        return best[0] if best else None

    def knot_at(self, wx, wy):
        for r in self.doc.walk():
            for kx, ky, meta in r.knots:
                if abs(wx - kx) <= 22 and abs(wy - ky) <= 17:
                    return r, meta
        return None, None

    def _wpos(self, event=None):
        if event is not None:
            return self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        px, py = self.root.winfo_pointerxy()
        cx = px - self.canvas.winfo_rootx()
        cy = py - self.canvas.winfo_rooty()
        return self.canvas.canvasx(cx), self.canvas.canvasy(cy), cx, cy

    # ---------------- 画布互动 ----------------
    def on_canvas_click(self, e):
        if self.commit_edit():          # 点别处 ＝ 把就地输入框收掉并存进去
            return
        wx, wy = self.canvas.canvasx(e.x), self.canvas.canvasy(e.y)
        r, meta = self.knot_at(wx, wy)
        if r is not None and meta[0] == "yao":
            self.snapshot()
            r.yao[meta[1]] ^= 1
            self.sel = r
            self.redraw()
            return
        gidx = self.gap_mark_at(wx, wy)   # 点警告记号 -> 就地补分割横结
        if gidx is not None:
            self.insert_cut_at(gidx)
            return
        hit = self.dec_label_at(wx, wy)   # 点数字本身 -> 就地改数字
        if hit is not None:
            self.sel = hit
            self.redraw()
            self.start_edit_value(hit)
            return
        target = self.rope_at(wx, wy)
        self.sel = target
        if target is not None:
            self.drag = {"kind": None, "rope": target, "moved": False,
                         "ox": wx, "oy": wy}
        self.redraw()

    # ---------------- 就地改数字 ----------------
    def dec_label_at(self, wx, wy):
        """点在十进制绳那行数字上吗？"""
        for r in self.doc.walk():
            if r.kind not in KIND_COUNT or not r.head_bbox:
                continue
            x0, y0, x1, y1 = r.head_bbox
            if x0 <= wx <= x1 and y0 <= wy <= y1:
                return r
        return None

    def start_edit_value(self, r):
        """在数字原地开一个输入框。Enter 或点外面 ＝ 存；Esc ＝ 放弃。"""
        if r.kind not in KIND_COUNT or not r.head_bbox:
            return
        self.commit_edit()
        x0, y0, x1, y1 = r.head_bbox
        e = tk.Entry(self.canvas, font=self.f_lab, width=8,
                     justify="center", relief="solid", bd=1)
        e.insert(0, str(r.value))
        e.select_range(0, "end")
        win = self.canvas.create_window((x0 + x1) / 2.0, (y0 + y1) / 2.0,
                                        window=e)
        # ready：刚开框的那一瞬间可能收到一个假的 FocusOut（没有视窗管理员时
        # 特别容易），那一下要忽略，不然框会自己闪掉。
        self._edit = {"rope": r, "entry": e, "win": win, "ready": False}
        e.focus_set()
        self.root.after(250, self._edit_ready)
        e.bind("<Return>", lambda ev: self.commit_edit())
        e.bind("<KP_Enter>", lambda ev: self.commit_edit())
        e.bind("<Escape>", lambda ev: self.cancel_edit())
        e.bind("<FocusOut>", lambda ev: self._edit_focus_out())
        self.set_status("打数字，Enter 或点外面存起来；Esc 放弃。")

    def _edit_ready(self):
        if self._edit:
            self._edit["ready"] = True

    def _edit_focus_out(self):
        if self._edit and self._edit.get("ready"):
            self.commit_edit()

    def _close_edit(self):
        ed, self._edit = self._edit, None
        if ed:
            try:
                self.canvas.delete(ed["win"])
                ed["entry"].destroy()
            except tk.TclError:
                pass
        return ed

    def commit_edit(self):
        """回传 True 表示本来有编辑框、已经收掉了（这一次点击就不要再做别的）。"""
        if not self._edit:
            return False
        txt = self._edit["entry"].get().strip()
        r = self._edit["rope"]
        self._close_edit()
        try:
            v = int(txt)
        except ValueError:
            v = None
        if v is not None and v >= 0:
            cy = r.cycle()
            v = cyc_clamp(v, cy[0]) if cy else v
            if v != r.value:
                self.snapshot()
                r.value = v
                if not cy:
                    r.places = 0
        self.redraw()
        return True

    def cancel_edit(self):
        if self._edit:
            self._close_edit()
            self.redraw()

    def on_canvas_dclick(self, e):
        wx, wy = self.canvas.canvasx(e.x), self.canvas.canvasy(e.y)
        r = self.rope_at(wx, wy)
        if r is not None and r.kind in KIND_COUNT:
            self.sel = r
            self.redraw()
            self.start_edit_value(r)

    def on_canvas_drag(self, e):
        if not self.drag or self.drag.get("rope") is None:
            return
        wx, wy = self.canvas.canvasx(e.x), self.canvas.canvasy(e.y)
        if (abs(wx - self.drag["ox"]) + abs(wy - self.drag["oy"])) < 8:
            return
        self.drag["moved"] = True
        self._show_ghost(wx, wy, KIND_LABEL.get(self.drag["rope"].kind, "绳"),
                         exclude=self.drag["rope"],
                         kind=self.drag["rope"].kind)

    def on_canvas_release(self, e):
        if not self.drag:
            return
        d, self.drag = self.drag, None
        self._clear_ghost()
        if d.get("rope") is None or not d.get("moved"):
            return
        wx, wy = self.canvas.canvasx(e.x), self.canvas.canvasy(e.y)
        moving = d["rope"]
        mode, target, idx = self.drop_spot(wx, wy, exclude=moving,
                                           kind=moving.kind)
        self.snapshot()
        self.doc.remove(moving)
        if mode == "branch" and target is not None:
            target.children.append(moving)
        else:
            self._insert_root_idx(moving, idx)
        self.sel = moving
        self.redraw()

    def on_canvas_rclick(self, e):
        wx, wy = self.canvas.canvasx(e.x), self.canvas.canvasy(e.y)
        r = self.rope_at(wx, wy)
        if r is None:
            return
        self.sel = r
        self.redraw()
        m = tk.Menu(self.root, tearoff=0)
        m.add_command(label=f"—— {KIND_LABEL[r.kind]} ——", state="disabled")
        m.add_separator()
        cm = tk.Menu(m, tearoff=0)
        for k, t in CONVERT_TO:
            cm.add_command(label=t, state="disabled" if k == r.kind else "normal",
                           command=lambda kk=k, rr=r: self.convert_rope(kk, rr))
        m.add_cascade(label="换成…（旁注和支绳都留着）", menu=cm)
        bm = tk.Menu(m, tearoff=0)
        for k, t in ((KIND_TRI, "三爻绳"), (KIND_HEX, "六爻绳")):
            bm.add_command(label=t, command=lambda kk=k: self.add_branch(kk))
        m.add_cascade(label="右接一条…（只有卦象能右接）", menu=bm)
        m.add_separator()
        m.add_command(label="◀ 左边插一个分割横结",
                      command=lambda: self.insert_cut_beside(r, -1))
        m.add_command(label="右边插一个分割横结 ▶",
                      command=lambda: self.insert_cut_beside(r, 1))
        m.add_separator()
        if r.kind in (KIND_TRI, KIND_HEX):
            m.add_command(label="全部翻成阳结", command=lambda: self._fill(r, 1))
            m.add_command(label="全部翻成阴结", command=lambda: self._fill(r, 0))
            m.add_command(label="错卦（阴阳全翻）", command=lambda: self._flip(r))
        m.add_command(label="左移", command=lambda: self.move_sel(-1))
        m.add_command(label="右移", command=lambda: self.move_sel(1))
        m.add_separator()
        m.add_command(label="删除这条绳（连支绳）",
                      command=self.del_selected)
        try:
            m.tk_popup(e.x_root, e.y_root)
        finally:
            m.grab_release()

    def on_wheel(self, e, direction=None):
        # 只卷画布。滚轮不动数字 —— 不小心滚一下就改掉数值是要命的
        step = direction if direction is not None else (
            1 if getattr(e, "delta", 0) > 0 else -1)
        self.canvas.yview_scroll(-step, "units")

    def on_gap_change(self):
        self.kg = max(14, int(self.gap_var.get()))
        self.kgd = max(9, int(self.gapd_var.get()))
        self.colgap = max(0, int(self.colgap_var.get()))
        self.redraw()

    def set_all_opts(self, v):
        for key, _, _ in DISPLAY_OPTS:
            self.opt[key].set(v)
        self.redraw()

    def O(self, key):
        return bool(self.opt[key].get())

    def _fill(self, r, v):
        self.snapshot()
        r.yao = [v] * len(r.yao)
        self.redraw()

    def _flip(self, r):
        self.snapshot()
        r.yao = [1 - v for v in r.yao]
        self.redraw()

    def _is_descendant(self, node, ancestor):
        for r in ancestor.walk():
            if r is node and r is not ancestor:
                return True
        return False

    def _insert_root_at(self, rope, wx):
        pos = len(self.doc.ropes)
        for i, r in enumerate(self.doc.ropes):
            if wx < r.x:
                pos = i
                break
        self.doc.ropes.insert(pos, rope)

    # ---------------- 拖放面板 ----------------
    def palette_press(self, kind):
        self.drag = {"kind": kind, "rope": None, "moved": False}

    def palette_motion(self, e):
        if not self.drag or self.drag.get("kind") is None:
            return
        self.drag["moved"] = True
        wx, wy, cx, cy = self._wpos()
        if 0 <= cx < self.canvas.winfo_width() and \
                0 <= cy < self.canvas.winfo_height():
            self._show_ghost(wx, wy, KIND_LABEL[self.drag["kind"]],
                             kind=self.drag["kind"])
        else:
            self._clear_ghost()

    def palette_release(self, e):
        if not self.drag:
            return
        d, self.drag = self.drag, None
        self._clear_ghost()
        if d.get("kind") is None or not d.get("moved"):
            return
        wx, wy, cx, cy = self._wpos()
        if not (0 <= cx < self.canvas.winfo_width() and
                0 <= cy < self.canvas.winfo_height()):
            return
        self.snapshot()
        rope = self.new_rope(d["kind"])
        mode, target, idx = self.drop_spot(wx, wy, kind=d["kind"])
        if mode == "branch" and target is not None and d["kind"] != KIND_FEN:
            target.children.append(rope)
        else:
            self._insert_root_idx(rope, idx)
        self.sel = rope
        self.redraw()
        if rope.kind in KIND_COUNT:      # 计数绳拖过去就等着填数字
            self.start_edit_value(rope)

    def drop_spot(self, wx, wy, exclude=None, kind=None):
        """算落点。回传 (mode, target, index)。
        mode "root"   -> 挂上横绳，index 是插在第几条之前
        mode "branch" -> 右接到 target 底下
        横绳上下这一带一律算「挂横绳」，不然想插一条进去永远变成右接。"""
        if wy <= BEAM_Y + ROOT_BAND:
            return "root", None, self.root_index_at(wx, exclude)
        if kind is not None and kind not in self.BRANCHABLE:
            # 不是卦象，就没有右接这回事
            return "root", None, self.root_index_at(wx, exclude)
        r = self.rope_at(wx, wy, exclude=exclude)
        if r is None or r is exclude or (
                exclude is not None and self._is_descendant(r, exclude)):
            return "root", None, self.root_index_at(wx, exclude)
        return "branch", r, -1

    def root_index_at(self, wx, exclude=None):
        """插在横绳的第几个位置（跳过正在拖的那一条）。"""
        pos = 0
        for r in self.doc.ropes:
            if r is exclude:
                continue
            if wx < r.x:
                break
            pos += 1
        return pos

    def _insert_root_idx(self, rope, idx):
        idx = max(0, min(idx, len(self.doc.ropes)))
        self.doc.ropes.insert(idx, rope)

    def caret_x(self, idx, exclude=None):
        """插入点画在哪 —— 画在两条绳中间，看得出会挤到哪里去。"""
        others = [r for r in self.doc.ropes if r is not exclude]
        if not others:
            return LEFT_PAD
        if idx <= 0:
            return others[0].x - max(self.half_w(others[0]), 24) - 6
        if idx >= len(others):
            last = others[-1]
            return last.x + max(self.half_w(last), 24) + 6
        a, b = others[idx - 1], others[idx]
        return (a.x + max(self.half_w(a), 20)
                + b.x - max(self.half_w(b), 20)) / 2.0

    def _show_ghost(self, wx, wy, text, exclude=None, kind=None):
        self._clear_ghost()
        c = self.canvas
        mode, tgt, idx = self.drop_spot(wx, wy, exclude=exclude,
                                        kind=kind)
        if mode == "branch":
            x0, y0, x1, y1 = tgt.bbox
            c.create_rectangle(x0 - 4, y0 - 4, x1 + 4, y1 + 4,
                               outline="#E08A18", width=2, dash=(4, 3),
                               tags="ghost")
            hint = "右接到这条绳"
        else:
            cx = self.caret_x(idx, exclude)
            c.create_line(cx, BEAM_Y - 30, cx, BEAM_Y + 46,
                          fill="#E08A18", width=3, tags="ghost")
            c.create_polygon(cx - 7, BEAM_Y - 30, cx + 7, BEAM_Y - 30,
                             cx, BEAM_Y - 18, fill="#E08A18", tags="ghost")
            n = len([r for r in self.doc.ropes if r is not exclude])
            hint = f"插进横绳第 {idx + 1} 位（共 {n + 1} 条，旁边会让开）"
        ty = wy - 16 if mode == "branch" else BEAM_Y - 46
        c.create_text(wx + 12, ty, text=f"{text} → {hint}",
                      anchor="w", font=self.f_small, fill="#B3690B",
                      tags="ghost")
        self.drop_target = tgt

    def _clear_ghost(self):
        self.canvas.delete("ghost")
        self.drop_target = None

    # ---------------- 编修 ----------------
    def new_rope(self, kind):
        r = Rope(kind)
        # 栏位一律不猜：猜错比不猜更糟 —— 栏位顺序是校验码，
        # 一个猜错的标签会把整串绳判成顺序反了。
        if kind in KIND_COUNT:
            r.dec_style = self.default_dec_style.get()
            r.value = 1
        return r

    def append_root(self, kind):
        self.snapshot()
        r = self.new_rope(kind)
        self.doc.ropes.append(r)
        self.sel = r
        self.redraw()
        if r.kind in KIND_COUNT:
            self.start_edit_value(r)

    def add_branch(self, kind):
        if self.sel is None:
            messagebox.showinfo(APP_NAME, "先点一条绳，再右接。")
            return
        if kind not in self.BRANCHABLE:
            messagebox.showinfo(
                APP_NAME,
                "一条绳的结构里没有左右之分。\n"
                "右边接出去那条绳是卦象专有的象征区分 ——\n"
                "只有三爻绳、六爻绳能当支绳。")
            return
        self.snapshot()
        r = self.new_rope(kind)
        self.sel.children.append(r)
        self.sel = r
        self.redraw()

    def convert_rope(self, kind, r=None):
        """原地把这条绳换成别的绳型 —— 不必删掉再拖一条。
        旁注、栏位、右接的支绳全部留着。"""
        r = r or self.sel
        if r is None:
            messagebox.showinfo(APP_NAME, "先点一条绳。")
            return
        if r.kind == kind:
            return
        self.snapshot()
        old = list(r.yao)
        r.kind = kind
        n = 3 if kind == KIND_TRI else (6 if kind == KIND_HEX else 0)
        # 三爻<->六爻：留着的爻当下卦，不够的补阴
        r.yao = (old + [0] * n)[:n] if n else []
        self.redraw()

    def del_selected(self):
        if self.sel is None:
            return
        self.snapshot()
        self.doc.remove(self.sel)
        self.sel = None
        self.redraw()

    def move_sel(self, delta):
        if self.sel is None:
            return
        p = self.doc.parent_of(self.sel)
        lst = p.children if p is not None else self.doc.ropes
        i = lst.index(self.sel)
        j = i + delta
        if 0 <= j < len(lst):
            self.snapshot()
            lst[i], lst[j] = lst[j], lst[i]
            self.redraw()

    def clear_roles(self):
        """把栏位标签全清成「未标」。

        旧版给新绳猜过预设栏位（十进制绳猜数量、分段绳猜卦年），
        那些假标签会把顺序检查判成一堆错。清掉再自己标。
        """
        n = sum(1 for r in self.doc.walk() if r.role != ROLES[0])
        if not n:
            messagebox.showinfo(APP_NAME, "本来就没标。")
            return
        if not messagebox.askyesno(APP_NAME,
                                   f"把这条横绳上 {n} 个栏位标签清成「未标」？"):
            return
        self.snapshot()
        for r in self.doc.walk():
            r.role = ROLES[0]
        self.redraw()
        self.set_status(f"清了 {n} 个栏位标签。")

    def clear_all(self):
        if self.doc.ropes and not messagebox.askyesno(
                APP_NAME, "整条横绳清空？"):
            return
        self.snapshot()
        self.doc.ropes = []
        self.sel = None
        self.redraw()

    # ---------------- 属性面板 ----------------
    def on_role_change(self, e=None):
        if self.sel is None:
            return
        self.snapshot()
        self.sel.role = self.cb_role.get()
        self.redraw()

    def on_note_change(self, e=None):
        if self.sel is None:
            return
        self.sel.note = self.tx_note.get("1.0", "end-1c")
        self.dirty = True
        self._redraw_keep_focus()

    def on_dec_change(self, e=None):
        if self.sel is None or self.sel.kind not in KIND_COUNT:
            return
        if self._dec_owner is not self.sel:
            return                      # 数值栏还停在上一条绳，别乱写
        try:
            v = int(self.sp_val.get())
            p = int(self.sp_pla.get())
        except ValueError:
            return
        if v == self.sel.value and p == self.sel.places:
            return
        cy = self.sel.cycle()
        if cy:
            self.sel.value = cyc_clamp(v, cy[0])
        else:
            self.sel.value = max(0, v)
            self.sel.places = max(0, p)
        self.dirty = True
        self._redraw_keep_focus()

    def on_decstyle_change(self, e=None):
        if self.sel is None or self.sel.kind not in KIND_COUNT:
            return
        self.snapshot()
        self.sel.dec_style = (DEC_TALLY if self.cb_dec.current() == 0
                              else DEC_BIN4)
        self.redraw()

    def _redraw_keep_focus(self):
        w = self.root.focus_get()
        ins = None
        if isinstance(w, tk.Text):
            ins = w.index("insert")
        self.redraw()
        if w is not None:
            try:
                w.focus_set()
                if ins is not None:
                    w.mark_set("insert", ins)
            except tk.TclError:
                pass

    def on_convert_pick(self, e=None):
        i = self.cb_conv.current()
        if 0 <= i < len(CONVERT_TO) and self.sel is not None:
            self.convert_rope(CONVERT_TO[i][0])

    def refresh_inspector(self):
        r = self.sel
        if r is None:
            self.lb_sym.config(text="—")
            self.lb_name.config(text="（未选）")
            self.lb_idx.config(text="点画布上任一条绳")
            self._dec_owner = None
            self.dec_row.pack_forget()
            self.dec_row2.pack_forget()
            self.tx_note.delete("1.0", "end")
            self._set_ro(self.tx_ref,
                         "右边拖一条绳下来，或双击面板上的绳型。\n\n"
                         "点结＝阴阳互换（预设全阴）。\n"
                         "爻序：最上面那个结是上爻，最下面是初爻。")
            return

        g = r.gua()
        if g:
            self.lb_sym.config(text=g[0])
            self.lb_name.config(text=g[1])
            self.lb_idx.config(text=g[2])
        elif r.cycle():
            cy = r.cycle()
            v = r.cval()
            self.lb_sym.config(text="⑩" if cy[0] == GAN_MAX else "⑫")
            self.lb_name.config(text=f"{v}·{cy[1][v - 1]}")
            self.lb_idx.config(text=f"{cy[2]}第 {v} 位，打 {v} 个结")
        elif r.kind == KIND_DEC:
            self.lb_sym.config(text="❹")
            self.lb_name.config(text=str(r.value))
            self.lb_idx.config(text="十进制（位值制）")
        elif r.kind == KIND_BIG:
            self.lb_sym.config(text="▬")
            self.lb_name.config(text="大横结　0")
            self.lb_idx.config(text="零（三个结宽）")
        elif r.kind == KIND_SEP:
            self.lb_sym.config(text="▬")
            self.lb_name.config(text="分位阳结")
            self.lb_idx.config(text="分位（两个结宽）")
        elif r.kind == KIND_CUT:
            self.lb_sym.config(text="•")
            self.lb_name.config(text="分割")
            self.lb_idx.config(text="横绳上一个普通结")
        else:
            self.lb_sym.config(text="⋮")
            self.lb_name.config(text="分段绳")
            self.lb_idx.config(text="横绳打一个结＋超长虚线")

        self.cb_role.set(r.role)
        self.cb_conv.set(dict(CONVERT_TO).get(r.kind, ""))
        if self.tx_note.get("1.0", "end-1c") != (r.note or ""):
            self.tx_note.delete("1.0", "end")
            self.tx_note.insert("1.0", r.note or "")

        if r.kind in KIND_COUNT:
            self._dec_owner = r
            self.dec_row.pack(fill="x", padx=6, pady=2, after=self.cb_role.master)
            cy = r.cycle()
            if cy:
                self.dec_row2.pack_forget()
                self.sp_val.configure(from_=1, to=cy[0])
                self.sp_pla.configure(state="disabled")
            else:
                self.dec_row2.pack(fill="x", padx=6, pady=2, after=self.dec_row)
                self.sp_val.configure(from_=0, to=999999)
                self.sp_pla.configure(state="normal")
            if self.sp_val.get() != str(r.value):
                self.sp_val.delete(0, "end")
                self.sp_val.insert(0, str(r.value))
            if self.sp_pla.get() != str(r.places):
                self.sp_pla.delete(0, "end")
                self.sp_pla.insert(0, str(r.places))
            self.cb_dec.current(0 if r.dec_style == DEC_TALLY else 1)
        else:
            self._dec_owner = None
            self.dec_row.pack_forget()
            self.dec_row2.pack_forget()

        self._set_ro(self.tx_ref, "\n".join(self.ref_lines(r)))

    def ref_lines(self, r):
        out = []
        if r.kind == KIND_TRI:
            out += tri_info_lines(trigram_name(r.yao))
            out.append("")
            out += YINYANG_NOTE
        elif r.kind == KIND_HEX:
            name, idx, up, low = hexagram_name(r.yao)
            out.append(f"{HEX_SYM[name]} {name}　方图第 {idx} 卦")
            out.append(f"上卦 {TRI_SYM[up]}{up}　下卦 {TRI_SYM[low]}{low}")
            out.append("")
            out += tri_info_lines(up)
            if low != up:
                out.append("")
                out += tri_info_lines(low)
        elif r.cycle():
            cy = r.cycle()
            v = r.cval()
            out.append(f"{cy[2]}　{v}·{cy[1][v - 1]}")
            out.append(f"打 {v} 个结。")
            out.append("")
            out.append(f"{cy[2]}是{cy[0]}位的循环，一位一个结：")
            half = (cy[0] + 1) // 2
            out.append(" ".join(f"{nm}{i}" for i, nm in
                                enumerate(cy[1][:half], start=1)))
            out.append(" ".join(f"{nm}{i}" for i, nm in
                                enumerate(cy[1][half:], start=half + 1)))
            out.append("")
            out.append("不是位值制 —— 没有进位，也没有零。")
            out.append(f"{cy[0]} 就是 {cy[0]} 个结。")
        elif r.kind == KIND_DEC:
            ds = r.runs()
            pn = PLACE_NAMES[10]
            out.append(f"数值 {r.value}")
            for i, d in enumerate(ds):
                out.append(f"　{pn[min(len(ds)-1-i, len(pn)-1)]}位："
                           + ("大横结（零）" if d == 0 else f"{d} 结"))
            nm = cyc_name(r.value, 10)
            if nm:
                out.append(f"十天干：{nm}（第 {r.value} 位）")
            out.append("")
            out.append("结法：" + ("打几个结就是几（位值制）"
                                   if r.dec_style == DEC_TALLY
                                   else "每位四个阴阳结"))
            if r.value >= 10000:
                out.append("")
                out.append("※ 过万了 —— 绳子不够用，该造字了。")
        elif r.kind == KIND_BIG:
            out.append("大横结 ＝ 零。三个结那么宽。")
            out.append("")
            out.append("零不能留空白：留空白，别人分不出")
            out.append("是绳编长了还是零 —— 就跟阴爻不能留空")
            out.append("一样，两边都要打结，只是不连在一起。")
        elif r.kind == KIND_SEP:
            out.append("分位阳结。两个结那么宽。")
            out.append("")
            out.append("数字与数字之间的分隔点。")
            out.append("12 ＝ 1｜阳结｜2")
            out.append("3979 ＝ 3｜阳结｜9｜阳结｜7｜阳结｜9")
            out.append("")
            out.append("中间留空一段，谁也分不清是几位。")
        elif r.kind == KIND_CUT:
            out.append("分割 ＝ 横绳上一个普通结而已，")
            out.append("底下不挂东西。跟大横结不是同一个结。")
        else:
            out.append("分段绳＝横绳上一个结。")
            out.append("古人省绳子，只在横绳打结；")
            out.append("底下那条超长虚线只是给眼睛看的，")
            out.append("表示这一段时间／这一条记录的范围。")
        return out

    # ---------------- 释读与全面注解 ----------------
    def read_chain(self, r):
        parts = [self._read_one(r)]
        for c in r.children:
            parts.append("右接→ " + self.read_chain(c))
        return "　".join(parts)

    def _read_one(self, r):
        note = f"（{r.note.replace(chr(10), '／')}）" if r.note else ""
        if r.kind == KIND_FEN:
            return f"｜分段｜{note}"
        if r.kind == KIND_BIG:
            return f"0（大横结）{note}"
        if r.kind == KIND_SEP:
            return f"｜（分位阳结）{note}"
        if r.kind == KIND_CUT:
            return f"‖（分割）{note}"
        cy = r.cycle()
        if cy:
            v = r.cval()
            return f"{v}·{cy[1][v - 1]}（{cy[2]}）{note}"
        if r.kind == KIND_DEC:
            return f"{r.value}{note}"
        g = r.gua()
        extra = f"〔{g[2]}〕" if r.kind == KIND_HEX else ""
        return f"{g[0]} {g[1]}{extra}{note}"

    NUMERIC = (KIND_DEC, KIND_GAN, KIND_DUO, KIND_BIG)

    CONTENT = (KIND_DEC, KIND_GAN, KIND_DUO, KIND_BIG,
               KIND_TRI, KIND_HEX, KIND_SEP)
    # 载得了栏位的绳：计数绳、卦绳，还有分段绳（原例里「某卦年」
    # 就是一条分段绳）。分割横结／分位／大横结是纯分隔符，不占栏位。
    # 关键是：没标栏位的一律跳过 —— 早先给新绳猜预设栏位，猜错就把
    # 整串绳判成顺序反了，那是假错。
    FIELDED = (KIND_DEC, KIND_GAN, KIND_DUO, KIND_TRI, KIND_HEX, KIND_FEN)
    # 一条绳的结构里没有左右之分；右边接出去那条绳是卦象专有的象征区分。
    # 所以只有三爻绳、六爻绳能当支绳，数字／大横结／分位／分割一律挂横绳。
    BRANCHABLE = (KIND_TRI, KIND_HEX)

    def check_issues(self, ropes=None):
        """严谨检查：哪里会被读错。

        规矩是：栏位与栏位之间「打横结」。横绳上那个分割结就是
        定界符，它一打，年到哪里为止就没得争。

        必须：两条计数绳并排又没有分割 —— 3979 后面直接跟 12，
              绳上跟 39791 后面跟 2 长得一模一样。
        必须：两条三爻绳并排又没有分割 —— 三加三就是六个结，
              会被当成一个六爻卦读。
        该补：换了栏位却没打横结 —— 年跟月之间没界，别人只能猜。

        回传 [{idx, level, text}]，idx ＝ 分割该插在第几位。
        """
        out = []
        rs = self.doc.ropes if ropes is None else ropes
        content = [r for r in rs if r.kind in self.FIELDED
                   and r.role != ROLES[0]]
        unlabeled = [r for r in rs if r.kind in self.FIELDED
                     and r.role == ROLES[0]]

        # (1) 栏位顺序 —— 年月日时 天地人 事情 数量，不许倒着来
        last_rank, last_role = -1, None
        for r in content:
            k = ROLE_RANK.get(r.role)
            if k is None:
                continue
            if k < last_rank:
                out.append({"idx": rs.index(r), "level": "顺序",
                            "text": f"{last_role} 后面又出现 {r.role} —— "
                                    f"栏位顺序反了；这一串绳被掉转过来读了？"})
            last_rank, last_role = max(last_rank, k), r.role

        # (2) 值域 —— 月不会有 13，日不会有 32，年不会是 1
        for r in content:
            if r.kind not in self.NUMERIC:
                continue
            v = 0 if r.kind == KIND_BIG else r.value
            cy = r.cycle()
            if cy and not (1 <= r.value <= cy[0]):
                out.append({"idx": rs.index(r), "level": "值域",
                            "text": f"{cy[2]}绳 ＝ {r.value}，{cy[2]}"
                                    f"只有{cy[0]}位"
                                    f"（{cy[1][0]}1…{cy[1][-1]}{cy[0]}）"})
            lo, hi = ROLE_RANGE.get(r.role, (None, None))
            if lo is not None and not (lo <= v <= hi):
                out.append({"idx": rs.index(r), "level": "值域",
                            "text": f"{r.role} ＝ {v}，超出 {lo}–{hi} —— "
                                    f"这个位置不可能是这个数"})
            if r.role == "卦年" and 0 < v < YEAR_MIN:
                out.append({"idx": rs.index(r), "level": "值域",
                            "text": f"卦年 ＝ {v}，年没有那么小 —— "
                                    f"会被当成月或日"})

        # 不靠标签、光靠顺序的那一套：绳串没有正反面，全靠这个
        for t in self.positional_faults(rs):
            out.append({"idx": 0, "level": "顺序", "text": t})
        if unlabeled and not content:
            out.append({"idx": 0, "level": "提醒",
                        "text": f"{len(unlabeled)} 条绳没标栏位 —— "
                                f"标了还能多验一层；不标也还有顺序这一层"})

        # (3) 首尾 —— 第一段该是年，最后一段该是数量
        if content:
            if ROLE_RANK.get(content[0].role, 0) > 0:
                out.append({"idx": 0, "level": "顺序",
                            "text": f"开头是 {content[0].role}，不是卦年 —— "
                                    f"捡到这串绳的人分不出哪一头是头"})
            if content[-1].role not in (ROLES[0], "数量·能量级别", "其他"):
                out.append({"idx": len(rs), "level": "顺序",
                            "text": f"结尾是 {content[-1].role}，不是数量 —— "
                                    f"数量在最后，才不会被读成年"})

        # (4) 定界 —— 栏位之间要打横结
        for i in range(len(rs) - 1):
            a, b = rs[i], rs[i + 1]
            if a.kind not in self.CONTENT or b.kind not in self.CONTENT:
                continue
            # 相邻的十进制绳＝同一个数的各位，本来就该连读（3｜9｜7｜9＝3979），
            # 断在哪里靠后面那个横结，不是错。
            if a.kind == KIND_TRI and b.kind == KIND_TRI:
                nm, _, _, _ = hexagram_name(list(a.yao) + list(b.yao))
                out.append({"idx": i + 1, "level": "提醒",
                            "text": f"{a.gua()[1]}＋{b.gua()[1]} 六个结连着，"
                                    f"会连读成一个 {nm}；"
                                    f"要分开就在中间打一个横结"})
            elif (a.role != ROLES[0] and b.role != ROLES[0]
                    and a.role != b.role):
                out.append({"idx": i + 1, "level": "该补",
                            "text": f"{a.role} 换到 {b.role}，"
                                    f"中间没打横结，界在哪只能猜"})
        return out

    def ambiguity_gaps(self):
        return [(d["idx"], None, None) for d in self.check_issues()]

    def _num_text(self, r):
        if r.kind == KIND_BIG:
            return "0"
        return str(r.cval())

    def gap_warning(self, a, b):
        la, lb = self._num_text(a), self._num_text(b)
        joined = la + lb
        alt = f"{joined[:len(la) + 1]}｜{joined[len(la) + 1:]}" \
            if len(joined) > len(la) + 1 else joined
        return (f"{la}｜{lb} 跟 {alt} 在绳上长得一样 —— "
                f"中间要打一个分割横结")

    def insert_cut_at(self, idx, note=""):
        self.snapshot()
        r = Rope(KIND_CUT, note=note)
        self._insert_root_idx(r, idx)
        self.sel = r
        self.redraw()
        return r

    GAP_LEVELS = ("必须", "该补")

    def field_groups(self, ropes=None):
        """按分隔符把根绳切成一栏一栏。

        分段绳／分割横结本来是分隔符；但带了旁注或栏位的分段绳
        （原例的「某卦年」就是这种）本身就占一栏 —— 那一栏的内容是
        「没写出来」，不是不存在。
        """
        rs = self.doc.ropes if ropes is None else ropes
        groups, cur = [], []
        for r in rs:
            marker = r.kind in (KIND_FEN, KIND_CUT)
            if marker:
                if cur:
                    groups.append(cur)
                    cur = []
                if r.note or r.role != ROLES[0]:
                    groups.append([r])      # 占一栏：内容没写出来
            else:
                cur.append(r)
        if cur:
            groups.append(cur)
        return groups

    def _unwritten(self, g):
        return len(g) == 1 and g[0].kind in (KIND_FEN, KIND_CUT)

    def group_number(self, g):
        """整栏都是计数绳，就并成一个数；有卦象就不是数。"""
        if g and all(r.kind in self.NUMERIC for r in g):
            return int("".join("0" if r.kind == KIND_BIG else str(r.cval())
                               for r in g))
        return None

    def positional_faults(self, ropes=None):
        """不靠栏位标签，光靠顺序验 —— 绳串没有正反面，全靠这个。

        年月日时 → 天地人 → 事情 → 数量。所以：
          · 头一栏一定是数，而且不会小（年没有那么小）
          · 第二、三栏若是数，不会超过 12 个月、31 日
        倒过来读，头一栏就变成卦象或小数，立刻穿帮 ——
        例：正读 3908 年癸丑月，倒读就成了坤年 32 月、数量 8093。
        """
        gs = self.field_groups(ropes)
        out = []
        if not gs:
            return out
        if self._unwritten(gs[0]):
            # 年故意没写出来（「某卦年」那种），顺序这一层就验不了，
            # 也不该硬判成错。
            return out
        v0 = self.group_number(gs[0])
        if v0 is None:
            nm = gs[0][0].gua()[1] if gs[0][0].gua() else KIND_LABEL[gs[0][0].kind]
            out.append(f"头一栏是「{nm}」，不是数 —— 年一定是个数")
        elif v0 < YEAR_MIN:
            out.append(f"头一栏是 {v0} —— 年没有那么小")
        for i, hi, nm in ((1, 12, "个月"), (2, 31, "日")):
            if len(gs) > i and not self._unwritten(gs[i]):
                v = self.group_number(gs[i])
                if v is not None and v > hi:
                    out.append(f"第 {i + 1} 栏是 {v} —— 没有 {v} {nm}")
        return out

    def positional_story(self, ropes=None):
        """把各栏按固定顺序摊出来：年＝… 月＝… 日＝…，末栏＝数量。

        倒读验证拿它讲人话 —— 「倒过来读会变成：年＝坤为地，月＝32，
        数量＝8093」，一看就知道不可能。
        """
        gs = self.field_groups(ropes)
        if not gs:
            return []
        slots = ["年", "月", "日", "时"]
        out = []
        for i, g in enumerate(gs):
            v = self.group_number(g)
            if self._unwritten(g):
                txt = (g[0].note or "没写出来").replace("\n", "／")
            else:
                txt = (str(v) if v is not None else
                       "＋".join((r.gua()[1] if r.gua() else r.headline())
                                 for r in g))
            roles = [r.role for r in g if r.role != ROLES[0]]
            if roles:                      # 标了栏位就照标的读
                out.append(f"{roles[0]}＝{txt}")
            elif i < len(slots):           # 没标就照固定顺序猜
                out.append(f"{slots[i]}＝{txt}")
            elif i == len(gs) - 1:
                out.append(f"末栏（数量／事物）＝{txt}")
            else:
                out.append(f"第{i + 1}栏＝{txt}")
        return out

    def reverse_check(self):
        """倒读验证：把整串绳反过来读，看还通不通。

        通不过，才证明这串绳只有一个读法 —— 这就是绳子结构校验码。
        """
        fwd = self.check_issues()
        rev = self.check_issues(list(reversed(self.doc.ropes)))
        return fwd, rev

    def show_reverse_check(self):
        fwd, rev = self.reverse_check()
        f_hard = [d["text"] for d in fwd if d["level"] in ("顺序", "值域")]
        r_hard = [d["text"] for d in rev if d["level"] in ("顺序", "值域")]
        # 光靠顺序的那一套（不用标栏位也验得了）
        f_pos = self.positional_faults()
        r_pos = self.positional_faults(list(reversed(self.doc.ropes)))
        f_all = f_pos + f_hard
        r_all = r_pos + r_hard
        lines = ["【绳子结构校验码】",
                 "绳串没有正反面，全靠顺序定：",
                 "年月日时 → 天地人 → 事情 → 数量。", "",
                 f"正读：{'通过' if not f_all else f'{len(f_all)} 处不合'}"]
        for t in f_all[:6]:
            lines.append(f"　· {t}")
        lines.append("")
        lines.append(f"倒读：{len(r_all)} 处读不通"
                     if r_all else "倒读：也通得过（！）")
        rev_ropes = list(reversed(self.doc.ropes))
        story = self.positional_story(rev_ropes)
        if story:
            lines.append("　倒过来会读成（未标栏位的按固定顺序算）：")
            lines.append("　　" + "　".join(story[:4]))
            if len(story) > 4:
                lines.append("　　" + "　".join(story[-2:]))
        for t in r_all[:8]:
            lines.append(f"　· {t}")
        lines.append("")
        if not f_all and r_all:
            lines.append("→ 正读通、倒读不通：校验码成立，"
                         "这串绳掉转过来读不出东西。")
        elif f_all:
            lines.append("→ 正读就有问题，先把上面那几处修好。")
        else:
            lines.append("→ 两头都读得通 —— 这一串还分不出正反，"
                         "头一栏补个够大的年份就分得出了。")
        messagebox.showinfo(APP_NAME, "\n".join(lines))

    def fix_all_gaps(self, only_must=False):
        issues = [d for d in self.check_issues()
                  if d["level"] in self.GAP_LEVELS
                  and (not only_must or d["level"] == "必须")]
        if not issues:
            messagebox.showinfo(APP_NAME, "没有读得混的地方。")
            return
        self.snapshot()
        for d in reversed(issues):
            self._insert_root_idx(Rope(KIND_CUT), d["idx"])
        self.sel = None
        self.redraw()
        self.set_status(f"补了 {len(issues)} 个分割横结。")

    def insert_cut_beside(self, r, side):
        if r not in self.doc.ropes:
            messagebox.showinfo(APP_NAME, "分割横结只能打在横绳上，支绳旁边不行。")
            return
        i = self.doc.ropes.index(r)
        self.insert_cut_at(i if side < 0 else i + 1)

    def number_runs(self):
        """把连着的计数绳并成一个数：3｜9｜7｜9 ＝ 3979，1｜3 ＝ 13。

        绳上看，一条几个结的绳就是几个结 —— 十进制、天干、地支都一样。
        连着几条就是一个数的几位，断在哪里靠后面那个横结，这就是定界。
        单独一条（两边都有横结）才读成干支的那一位：12·亥 ＝ 亥时。
        大横结在数中间算作 0。
        回传 [(起, 迄, 数字字串)]，只列真的并起来的那几段。
        """
        rs, out, i = self.doc.ropes, [], 0
        num = set(KIND_COUNT) | {KIND_BIG}
        while i < len(rs):
            if rs[i].kind in num:
                j = i
                while j + 1 < len(rs) and rs[j + 1].kind in num:
                    j += 1
                if j > i:
                    txt = "".join("0" if r.kind == KIND_BIG else str(r.cval())
                                  for r in rs[i:j + 1])
                    out.append((i, j, txt))
                i = j + 1
            else:
                i += 1
        return out

    def person_reading(self, group):
        """人 这一栏怎么读：卦象是氏，数字是名。

        两个横结之间放「水地比 ＋ 88」，就是小川 88 ——
        氏取自卦象，名就是那个数。
        朱重八本名朱八八，父朱五四，祖朱初一，曾祖朱四九，高祖朱百六。
        """
        gua = [r for r in group if r.kind in (KIND_TRI, KIND_HEX)]
        num = [r for r in group if r.kind in KIND_COUNT or r.kind == KIND_BIG]
        if not (gua and num):
            return ""
        shi = gua[0].gua()[1]
        ming = "".join("0" if r.kind == KIND_BIG else str(r.cval())
                       for r in num)
        return f"氏＝{shi}　名＝{ming}"

    def role_groups(self):
        """连着好几条同栏位的根绳算同一个栏位（天＋羊＝天羊国）。"""
        groups = []
        for r in self.doc.ropes:
            if (groups and groups[-1][0] == r.role
                    and r.role != ROLES[0]):
                groups[-1][1].append(r)
            else:
                groups.append((r.role, [r]))
        return groups

    def on_chk_fix(self, e=None):
        sel = self.tv_chk.selection()
        if not sel:
            return
        i = self.tv_chk.index(sel[0])
        if 0 <= i < len(self.chk_rows):
            d = self.chk_rows[i]
            if d["level"] in self.GAP_LEVELS:
                self.insert_cut_at(d["idx"])
            else:
                messagebox.showinfo(
                    APP_NAME,
                    "这一条是结构问题，补分割横结救不了 ——\n"
                    "得改栏位顺序或那个数字本身。\n\n" + d["text"])

    def refresh_check(self):
        issues = self.check_issues()
        self.chk_rows = issues
        self.tv_chk.delete(*self.tv_chk.get_children())
        for d in issues:
            self.tv_chk.insert("", "end", values=(
                d["level"], f"{d['idx'] + 1} 位", d["text"]))
        must = sum(1 for d in issues if d["level"] == "必须")
        hard = sum(1 for d in issues if d["level"] in ("顺序", "值域"))
        if not issues:
            self.lb_chk.config(text="校验码通过：顺序、值域、定界都没问题。")
        else:
            self.lb_chk.config(
                text=f"校验码：结构不合 {hard} 处｜会读错 {must} 处｜"
                     f"该补 {len(issues) - must - hard} 处"
                     f"　（双击「必须／该补」那几行就地补一个分割横结）")

    def _set_ro(self, w, text):
        """只读框：写完就锁回去，还是选得到、复制得走。"""
        w.configure(state="normal")
        w.delete("1.0", "end")
        w.insert("1.0", text)
        w.configure(state="disabled")

    def on_mine_change(self, e=None):
        if self._mine_owner is self.doc:
            self.doc.note = self.txt_mine.get("1.0", "end-1c")
            self.dirty = True

    def refresh_mine(self):
        """只在换了记录时才重载，不然会打断正在打的字。"""
        if self._mine_owner is self.doc:
            return
        self._mine_owner = self.doc
        self.txt_mine.delete("1.0", "end")
        self.txt_mine.insert("1.0", self.doc.note or "")

    def refresh_text(self):
        # 释读
        t = self.txt_read
        t.configure(state="normal")
        t.delete("1.0", "end")
        if self.doc.title:
            t.insert("end", self.doc.title + "\n\n")
        if not self.doc.ropes:
            t.insert("end", "横绳上还没有绳。")
        for i, (role, group) in enumerate(self.role_groups(), 1):
            body = "　＋　".join(self.read_chain(r) for r in group)
            tag = "" if role == ROLES[0] else f"〔{role}〕"
            t.insert("end", f"{i}. {tag}{body}\n")
            if role == "人":
                nm = self.person_reading(group)
                if nm:
                    t.insert("end", f"　　　{nm}\n")
        t.insert("end", "\n" + "─" * 40 + "\n")
        t.insert("end", "连起来读：" + self.plain_sentence())
        if self.doc.note:
            t.insert("end", "\n\n" + "─" * 40 + "\n我的注释：\n"
                     + self.doc.note)
        t.configure(state="disabled")

        # 全面注解
        t = self.txt_note
        t.configure(state="normal")
        t.delete("1.0", "end")
        if not self.doc.ropes:
            t.insert("end", "（空）")
            t.configure(state="disabled")
            return
        for i, (role, group) in enumerate(self.role_groups(), 1):
            if len(group) > 1:
                t.insert("end", f"[{i}] {role}　—— 这一栏由 {len(group)} "
                                f"条绳合起来读\n")
            if role == "人":
                nm = self.person_reading(group)
                if nm:
                    t.insert("end", f"　　{NAME_NOTE}\n　　{nm}\n")
            for r in group:
                self._note_block(t, r, i, 0)
            t.insert("end", "\n")
        if self.doc.note:
            t.insert("end", "─" * 40 + "\n我的注释：\n" + self.doc.note + "\n")
        t.configure(state="disabled")

    def _note_block(self, t, r, num, depth):
        pad = "   " * depth
        head = f"{pad}[{num}] " if depth == 0 else f"{pad}└右接 "
        role = "" if r.role == ROLES[0] else f"{r.role} · "
        if r.kind == KIND_BIG:
            t.insert("end", f"{head}{role}大横结　0　（三个结那么宽）\n")
            t.insert("end", f"{pad}    零打一个大横结，不留空白 —— 留空白，"
                            f"别人分不出是绳编长了还是零。\n")
        elif r.kind == KIND_SEP:
            t.insert("end", f"{head}{role}分位阳结　（两个结那么宽）\n")
            t.insert("end", f"{pad}    数字与数字之间的分隔点：12 读成 1｜2，"
                            f"3979 读成 3｜9｜7｜9。\n")
        elif r.kind == KIND_CUT:
            t.insert("end", f"{head}{role}分割　（横绳上一个普通结）\n")
        elif r.kind == KIND_FEN:
            t.insert("end", f"{head}{role}分段绳（横结＋超长虚线）\n")
            if r.role == "卦年":
                t.insert("end", f"{pad}    卦年一轮六十四年；是哪一轮，"
                                f"绳上不写 —— 靠智者记得。\n")
        elif r.cycle():
            cy = r.cycle()
            v = r.cval()
            t.insert("end", f"{head}{role}{KIND_LABEL[r.kind]}　"
                            f"{v}·{cy[1][v - 1]}（{v} 个结）\n")
            t.insert("end", f"{pad}    {cy[2]}是{cy[0]}位的循环，"
                            f"一位一个结：\n")
            t.insert("end", f"{pad}    "
                     + " ".join(f"{nm}{i}" for i, nm in
                                enumerate(cy[1], start=1)) + "。\n")
            t.insert("end", f"{pad}    不是位值制 —— 没有进位，也没有零。"
                            f"{cy[0]} 就是 {cy[0]} 个结。\n")
        elif r.kind == KIND_DEC:
            ds = r.runs()
            pn = PLACE_NAMES[10]
            desc = " ＋ ".join(
                (f"{pn[min(len(ds)-1-i, len(pn)-1)]}位大横结" if d == 0
                 else f"{pn[min(len(ds)-1-i, len(pn)-1)]}位{d}结")
                for i, d in enumerate(ds))
            nm = cyc_name(r.value, 10)
            gan = f"　天干＝{nm}" if nm else ""
            t.insert("end", f"{head}{role}十进制绳　{r.value}"
                            f"（{desc}）{gan}\n")
            if r.value >= 10000:
                t.insert("end", f"{pad}    ※ 过万 —— 绳子不够用，"
                                f"该造字了。\n")
        else:
            g = r.gua()
            t.insert("end", f"{head}{role}{KIND_LABEL[r.kind]}　"
                            f"{g[0]} {g[1]}（{g[2]}）\n")
            if r.kind == KIND_HEX:
                name, idx, up, low = hexagram_name(r.yao)
                t.insert("end", f"{pad}    上卦 {TRI_SYM[up]}{up}"
                                f"·{TRIGRAMS[TRI_IDX[up]][2]}　"
                                f"下卦 {TRI_SYM[low]}{low}"
                                f"·{TRIGRAMS[TRI_IDX[low]][2]}\n")
                for tri in ((up,) if up == low else (up, low)):
                    for line in tri_info_lines(tri):
                        t.insert("end", f"{pad}    {line}\n")
            else:
                for line in tri_info_lines(trigram_name(r.yao)):
                    t.insert("end", f"{pad}    {line}\n")
            yy = "".join("阳" if v else "阴" for v in reversed(r.yao))
            t.insert("end", f"{pad}    结（由上往下，上爻→初爻）：{yy}\n")
            if r.role == "卦年" and r.kind == KIND_HEX:
                t.insert("end", f"{pad}    卦年一轮六十四年；是哪一轮，"
                                f"绳上不写 —— 靠智者记得。\n")
        if r.note:
            for line in r.note.splitlines():
                t.insert("end", f"{pad}    旁注：{line}\n")
        for c in r.children:
            self._note_block(t, c, num, depth + 1)

    def plain_sentence(self):
        merged = {}
        for a, b, txt in self.number_runs():
            merged[a] = txt
            for k in range(a + 1, b + 1):
                merged[k] = None          # 已经并进前一条了
        bits = []
        for role, group in self.role_groups():
            chain = []
            for r in group:
                idx = self.doc.ropes.index(r) if r in self.doc.ropes else -1
                if idx in merged:
                    if merged[idx] is None:
                        continue
                    if not r.note:
                        chain.append(merged[idx])
                        continue
                # 右接是修饰：天右接雷 ＝ 天的雷，读成一样东西，
                # 所以整条链用「→」串起来，不跟旁边那条绳并列。
                sub, node = [], r
                while True:
                    if node.note:
                        sub.append(node.note.replace("\n", "／"))
                    elif node.cycle():
                        v = node.cval()
                        sub.append(f"{v}·{node.cycle()[1][v - 1]}")
                    elif node.kind in KIND_COUNT:
                        sub.append(str(node.value))
                    elif node.kind == KIND_BIG:
                        sub.append("0")
                    elif node.kind in (KIND_SEP, KIND_CUT):
                        pass
                    elif node.kind != KIND_FEN:
                        sub.append(node.gua()[1])
                    if node.children:
                        node = node.children[0]
                    else:
                        break
                if sub:
                    chain.append("→".join(sub))
            if chain:
                bits.append("，".join(chain))
        return "；".join(bits) + ("。" if bits else "")

    # ---------------- 档案 ----------------
    def new_doc(self, ask=True):
        if ask and self.dirty and not messagebox.askyesno(
                APP_NAME, "还没存，要丢掉改动新建吗？"):
            return
        self.book = [Doc()]
        self.bi = 0
        self.path = None
        self.sel = None
        self.undo_stack = []
        self.redo_stack = []
        self.dirty = False
        self.redraw()
        self.set_status("新的一条横绳。右边拖绳下来。")

    def load_sample(self, name):
        if self.dirty and not messagebox.askyesno(
                APP_NAME, "还没存，要丢掉改动载入示例吗？"):
            return
        s = sample_docs()
        if name == ALL_SAMPLES:
            self.book = list(s.values())
        else:
            self.book = [s[name]]
        self.bi = 0
        self.path = None
        self.sel = None
        self.dirty = False
        self.undo_stack = []
        self.redraw()
        self.set_status(f"已载入 {name}")

    def open_doc(self):
        p = filedialog.askopenfilename(
            title="开启结绳记录", initialdir=HERE,
            filetypes=[("结绳记事", "*.json"), ("全部", "*.*")])
        if not p:
            return
        try:
            with open(p, "r", encoding="utf-8") as f:
                o = json.load(f)
            if "records" in o:                       # 一册多条横绳
                self.book = [Doc.from_dict(x) for x in o["records"]] or [Doc()]
            else:                                    # 旧的单条格式
                self.book = [Doc.from_dict(o)]
        except Exception as ex:
            messagebox.showerror(APP_NAME, f"开不了：\n{ex}")
            return
        self.bi = 0
        self.path = p
        self.sel = None
        self.dirty = False
        self.undo_stack = []
        self.redraw()
        self.set_status(f"已开启 {os.path.basename(p)}"
                        f"（{len(self.book)} 条横绳）")

    def save_doc(self, as_new=False):
        p = self.path
        if as_new or not p:
            p = filedialog.asksaveasfilename(
                title="储存结绳记录", initialdir=HERE,
                defaultextension=".json",
                filetypes=[("结绳记事", "*.json")])
            if not p:
                return
        tmp = p + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"app": APP_NAME, "ver": APP_VER,
                           "records": [d.to_dict() for d in self.book]},
                          f, ensure_ascii=False, indent=1)
            os.replace(tmp, p)
        except Exception as ex:
            messagebox.showerror(APP_NAME,
                                 f"没写进档案！改动还在画面上，但档案没存好：\n{ex}")
            return
        self.path = p
        self.dirty = False
        self.set_status(f"已存 {os.path.basename(p)}")

    def export_txt(self):
        p = filedialog.asksaveasfilename(
            title="汇出释读", initialdir=HERE, defaultextension=".txt",
            filetypes=[("文字档", "*.txt")])
        if not p:
            return
        body = (self.txt_read.get("1.0", "end-1c") + "\n\n"
                + "=" * 50 + "\n全面注解\n" + "=" * 50 + "\n"
                + self.txt_note.get("1.0", "end-1c"))
        with open(p, "w", encoding="utf-8") as f:
            f.write(body)
        self.set_status(f"已汇出 {os.path.basename(p)}")

    def export_svg(self):
        p = filedialog.asksaveasfilename(
            title="汇出 SVG", initialdir=HERE, defaultextension=".svg",
            filetypes=[("SVG", "*.svg")])
        if not p:
            return
        sr = [float(v) for v in str(self.canvas.cget("scrollregion")).split()]
        w = int(sr[2]) if len(sr) > 3 else 1200
        h = int(sr[3]) if len(sr) > 3 else 800
        parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" '
                 f'height="{h}" viewBox="0 0 {w} {h}">',
                 f'<rect width="{w}" height="{h}" fill="{BG}"/>']
        for item in self.canvas.find_all():
            if "ghost" in self.canvas.gettags(item):
                continue
            parts.append(self._svg_item(item))
        parts.append("</svg>")
        with open(p, "w", encoding="utf-8") as f:
            f.write("\n".join(x for x in parts if x))
        self.set_status(f"已汇出 {os.path.basename(p)}")

    def _svg_item(self, item):
        c = self.canvas
        t = c.type(item)
        co = c.coords(item)

        def opt(name, default=""):
            try:
                v = c.itemcget(item, name)
                return v if v else default
            except tk.TclError:
                return default

        if t == "line":
            pts = " ".join(f"{co[i]},{co[i+1]}" for i in range(0, len(co), 2))
            dash = opt("dash")
            da = ' stroke-dasharray="4,4"' if dash else ""
            return (f'<polyline points="{pts}" fill="none" '
                    f'stroke="{opt("fill", "#000")}" '
                    f'stroke-width="{opt("width", "1")}" '
                    f'stroke-linecap="round"{da}/>')
        if t == "oval":
            x0, y0, x1, y1 = co
            fill = opt("fill", "none") or "none"
            st = opt("outline", "none") or "none"
            return (f'<ellipse cx="{(x0+x1)/2}" cy="{(y0+y1)/2}" '
                    f'rx="{abs(x1-x0)/2}" ry="{abs(y1-y0)/2}" '
                    f'fill="{fill}" stroke="{st}" '
                    f'stroke-width="{opt("width", "1")}"/>')
        if t == "rectangle":
            x0, y0, x1, y1 = co
            fill = opt("fill", "none") or "none"
            st = opt("outline", "none") or "none"
            return (f'<rect x="{min(x0,x1)}" y="{min(y0,y1)}" '
                    f'width="{abs(x1-x0)}" height="{abs(y1-y0)}" '
                    f'fill="{fill}" stroke="{st}" stroke-dasharray="3,3"/>')
        if t == "text":
            x, y = co[0], co[1]
            s = (opt("text").replace("&", "&amp;").replace("<", "&lt;")
                 .replace(">", "&gt;"))
            anch = opt("anchor", "center")
            ta = {"center": "middle", "w": "start", "e": "end"}.get(anch, "middle")
            return (f'<text x="{x}" y="{y+4}" text-anchor="{ta}" '
                    f'font-family="Microsoft YaHei, sans-serif" '
                    f'font-size="12" fill="{opt("fill", "#000")}">{s}</text>')
        return ""

    # ---------------- 工具 ----------------
    def open_guanian(self):
        GuaNianDialog(self.root, self)

    def show_help(self):
        messagebox.showinfo(APP_NAME, HELP_TEXT)

    def set_status(self, s):
        self.status.config(text="  " + s)

    def on_close(self):
        if self.dirty and not messagebox.askyesno(APP_NAME, "还没存，要离开吗？"):
            return
        self.root.destroy()


HELP_TEXT = """结绳记事 —— 怎么用

一、横绳（太极）在最上面。每条纵绳都从横绳上的一个「横结」垂下来。
　　横结＝栏位分隔。一条记录读起来就是：
　　　卦年｜卦月｜日(十进制)｜方位地点｜人／事情｜数量

二、右边面板按住往左拖：
　　· 分段绳　　 横绳一个结 ＋ 超长虚线（古人省绳子，只打横结；
　　　　　　　　 虚线只是给眼睛看的）
　　· 三爻绳　　 三个阴阳结 ＝ 一个八卦
　　· 六爻绳　　 六个阴阳结 ＝ 一个六十四卦（方图卦序）
　　· 十进制绳　 位值制，十进一：十五 ＝ 十位1结｜阳结｜个位5结。
　　　　　　　　 大数用它（3979、66、20…）。
　　· 十天干绳　 十位的循环，一位一个结：甲1 乙2 丙3 丁4 戊5
　　　　　　　　 己6 庚7 辛8 壬9 癸10。十就是十个结。
　　· 十二地支绳 十二位的循环，一位一个结：子1 丑2 寅3 卯4 辰5 巳6
　　　　　　　　 午7 未8 申9 酉10 戌11 亥12。十二就是十二个结。
　　　 两种循环绳都不是位值制 —— 没有进位，也没有零。
　　　 对照：十进制的 10 是 1｜阳结｜大横结，天干绳的 10（癸）是十个结。

　　落点规则：**横绳上下这一带一律挂横绳**（会画一个插入箭头，
　　告诉你插进第几位，旁边的绳自动让开）；要右接，就拖到绳身中段。
　　空白处也是挂横绳。双击面板上的绳型 ＝ 直接加到最右边。
　　现成的绳也能拖：拖回横绳一带就脱钩变根绳，拖到别条绳身上就变它的支绳。

三之二、要换绳型不必删掉重拖：右键 →「换成…」，或右边属性栏的「换成」，
　　旁注、栏位、右接的支绳全部留着。三爻↔六爻时留着的爻当下卦。

三、右接支绳「只连右边一侧」，所以一眼看得出它跟上面那组是分开的。
　　支绳可以一直串下去：六六 → (乾为天)爸爸 → (坤为地)死了。

四、点结＝阴阳互换。预设全是阴结。
　　爻序：最靠近横绳的结是「上爻」，最下面是「初爻」。
　　横绳上那个结只是普通一个结，不是阳结。

五、十进制绳改数字：**点绳尾那个数字**（例如「9·壬」），就地跳出输入框，
　　打新数字，Enter 或点外面存起来，Esc 放弃。双击绳身也开。
　　右边属性栏也可以直接输入。
　　结本身点了不会改数字，滚轮也不会 —— 免得手一滑就改掉。

　　★ 结的尺寸阶梯 —— 三种宽度，三种意思，不会混：
　　　 一个结　＝ 半个阴爻。阴爻就是两个这样的结，并排、不连在一起。
　　　　　　　　　计数结用的也是这个。
　　　 两个结　＝ 阳结（两个阴爻结绑在一起，或一条绳绑两次），宽一点。
　　　　　　　　　十进制绳的分位结就是它：12 ＝ 1｜阳结｜2，
　　　　　　　　　3979 ＝ 3｜阳结｜9｜阳结｜7｜阳结｜9。位间绝不留空。
　　　 三个结　＝ 大横结 ＝ 零，最大。留空白别人分不出是绳编长了还是零。
　　　 分割　　＝ 横绳上一个普通结而已，底下不挂东西。跟大横结不是同一个结。
　　　 分位阳结、大横结、分割 三个都能从右边面板拖出来单用。

五之三、【绳子结构校验码】栏位顺序是固定的：
　　　年 月 日 时 → 天（方位）地（地点）人 → 事情 → 数量。
　　这个顺序本身就是校验码。从垃圾堆里捡一串绳出来：
　　· 年没有那么小，不会读成「1 年、25 年」；
　　· 掉转过来读，顺序就全反了，读不通；
　　· 数量在最后而且是小数，不会被读成 397912。
　　栏位与栏位之间「打横结」（分割横结），年到哪里为止就没得争 ——
　　没有它，3979｜12 跟 39791｜2 在绳上长得一模一样。
　　下面第三页「严谨检查」把会读错的地方全列出来，双击一行就地补一个；
　　工具 →「倒读验证」把整串绳反过来读给你看，证明它只有一个读法。

五之四、一条绳的结构里没有左右之分。右边接出去那条绳是**卦象专有**的
　　象征区分 —— 只有三爻绳、六爻绳能当支绳；数字、大横结、分位阳结、
　　分割横结一律挂在横绳上。

五之二、画布上每一层字都可以打勾开关：检视 → 显示哪些字。
　　预设只留「3·丙」这类数值、卦名、爻位和旁注；栏位标签与位值注记预设关掉。
　　结距分三套，各四档：阴阳结距、计数结距、列距（两条绳之间）。
　　列距预设「极窄」＝ 两栏的字之间不再多留空；嫌挤就往上调。
　　画布上那些 !／? 检查记号预设关掉（嫌难看），要看就在这里勾回来 ——
　　检查本身照跑，结果都在下面第三页。

六、下面四页：
　　·「释读」　　 一句话读法（相邻的十进制绳会自动并成一个数）
　　·「全面注解」 逐条列卦象、上下卦、说卦的人伦／动物／身体／方位／
　　　　　　　　 五行与广象，以及你的旁注
　　·「严谨检查」 校验码，会读错的地方都在这里
　　·「我的注释」 ★ 这一页是你自己写的，**跟着档案一起存**
　　前三页是程式每次重画就重写的，所以设成只读 —— 在那上面打字，
　　下一次重画就没了。要自己写字，写在「我的注释」。
　　每条绳旁边还有「旁注」（右边属性栏那格），那个也是存得住的。

七、一册可以有很多条横绳（上面那排「记录册」）：
　　＋新横绳＝再记一笔；◀ ▶ 或 PageUp/PageDown 翻；
　　「翻记录／检索」（Ctrl+F）把整册压成一行一行，打字就筛 ——
　　卦名、上下卦、数字、天干、栏位、旁注都能找。
　　这就是智者翻记录那一段：老智者死了，二十几岁的新智者
　　只要知道原理，四十年前的绳子照样读得懂。

八、工具 → 卦年换算：接上 guaxu_core.py 就能算「现在是这个卦年，
　　我今年几岁」。

── 原理（读绳的人只要记住这几条）──
　结在横绳上 ＝ 换栏位。栏位顺序由左到右，自己排。
　一股一结 ＝ 阳；分两股两结 ＝ 阴。最上是上爻，最下是初爻。
　三结成一卦，六结成一重卦，卦名照先天方图卦序。
　计数绳由上而下是高位到低位，一位打几结就是几，空档＝零。
　支绳只从右边接出去，一层一层往下串，读作「这个的那个」。
　卦年一轮六十四年；哪一轮不写在绳上，靠人记得。
　超过一万，绳子不够用 —— 该造字了。
"""


# ══════════════════════════════════════════════════════════════════════
#  六、卦年换算（选配：接 guaxu_core）
# ══════════════════════════════════════════════════════════════════════

def find_guaxu_core():
    cands = [HERE,
             os.path.join(HERE, "..", "xuan", "sizhuguaxu"),
             os.path.join(HERE, "xuan", "sizhuguaxu"),
             os.path.join(os.path.dirname(HERE), "xuan", "sizhuguaxu"),
             os.environ.get("GUAXU_CORE_DIR", "")]
    for d in cands:
        if d and os.path.isfile(os.path.join(d, "guaxu_core.py")):
            return os.path.abspath(d)
    return None


class SearchDialog(tk.Toplevel):
    """翻记录：整册压成一行一行，打字就筛。

    ——「智者死后，年轻的智者二十多岁，还能翻看四十年前的记录，
    　　只要他知道原理。」这一页就是那本册子。
    """

    def __init__(self, master, app):
        tk.Toplevel.__init__(self, master)
        self.app = app
        self.title("翻记录 · 整册检索")
        self.geometry("1000x560")

        top = ttk.Frame(self, padding=8)
        top.pack(fill="x")
        ttk.Label(top, text="找", font=app.f_ui_b).pack(side="left")
        self.e = ttk.Entry(top, font=app.f_ui, width=36)
        self.e.pack(side="left", padx=6)
        self.e.bind("<KeyRelease>", lambda ev: self.refresh())
        ttk.Label(top, text="卦名 · 上下卦 · 数字 · 天干 · 栏位 · 旁注 都能找；"
                            "空白＝全部列出",
                  font=app.f_small, foreground=DIM_C).pack(side="left")
        self.lb_n = ttk.Label(top, text="", font=app.f_small)
        self.lb_n.pack(side="right")

        mid = ttk.Frame(self)
        mid.pack(fill="both", expand=True, padx=8, pady=(0, 4))
        cols = ("no", "title", "read")
        self.tv = ttk.Treeview(mid, columns=cols, show="headings",
                               selectmode="browse")
        for c, t, w in (("no", "第", 46), ("title", "这条横绳", 240),
                        ("read", "连起来读", 660)):
            self.tv.heading(c, text=t)
            self.tv.column(c, width=w, anchor="w")
        sb = ttk.Scrollbar(mid, command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.tv.bind("<Double-Button-1>", lambda ev: self.go())
        self.tv.bind("<Return>", lambda ev: self.go())

        bot = ttk.Frame(self, padding=(8, 0, 8, 8))
        bot.pack(fill="x")
        ttk.Button(bot, text="跳到这条横绳", command=self.go).pack(side="left")
        ttk.Button(bot, text="关闭", command=self.destroy).pack(side="right")

        self.rows = []
        self.refresh()
        self.e.focus_set()

    def refresh(self):
        q = self.e.get().strip()
        self.tv.delete(*self.tv.get_children())
        self.rows = []
        for i, d in enumerate(self.app.book):
            hay = self.app.record_haystack(d)
            if q and q not in hay:
                continue
            self.rows.append(i)
            self.tv.insert("", "end", values=(
                i + 1, d.title or "（未命名）", self.app.record_summary(d)))
        self.lb_n.config(text=f"{len(self.rows)} / {len(self.app.book)} 条")

    def go(self):
        sel = self.tv.selection()
        if not sel:
            return
        i = self.tv.index(sel[0])
        if 0 <= i < len(self.rows):
            self.app.bi = self.rows[i]
            self.app.sel = None
            self.app.redraw()


class GuaNianDialog(tk.Toplevel):
    def __init__(self, master, app):
        tk.Toplevel.__init__(self, master)
        self.app = app
        self.title("卦年换算 · 村里的智者")
        self.resizable(False, False)
        f = app.f_ui

        box = ttk.Frame(self, padding=10)
        box.pack(fill="both", expand=True)

        ttk.Label(box, text="出生那天（公历）", font=app.f_ui_b).grid(
            row=0, column=0, columnspan=6, sticky="w")
        self.e_b = self._date_row(box, 1, -1953, 2, 27)
        ttk.Label(box, text="现在（公历）", font=app.f_ui_b).grid(
            row=2, column=0, columnspan=6, sticky="w", pady=(8, 0))
        self.e_n = self._date_row(box, 3, 2026, 9, 13)

        ttk.Button(box, text="算", command=self.go).grid(
            row=4, column=0, columnspan=6, pady=8, sticky="ew")
        self.out = tk.Text(box, width=54, height=11, font=app.f_mono,
                           wrap="word", relief="solid", bd=1)
        self.out.grid(row=5, column=0, columnspan=6, sticky="nsew")

        d = find_guaxu_core()
        self.out.insert("1.0",
                        f"找到 guaxu_core：{d}\n按「算」开始。"
                        if d else
                        "找不到 guaxu_core.py。\n\n"
                        "放一份到本程式同目录，或把资料夹路径\n"
                        "设成环境变数 GUAXU_CORE_DIR，就能算卦年。\n"
                        "（不接也不影响记录与注解。）")

    def _date_row(self, box, row, y, m, d):
        es = []
        for i, (lab, val, w) in enumerate(
                (("年", y, 7), ("月", m, 4), ("日", d, 4))):
            ttk.Label(box, text=lab, font=self.app.f_small).grid(
                row=row, column=i * 2, sticky="e", padx=(4, 1))
            e = ttk.Entry(box, width=w, font=self.app.f_small)
            e.insert(0, str(val))
            e.grid(row=row, column=i * 2 + 1, sticky="w")
            es.append(e)
        return es

    def go(self):
        d = find_guaxu_core()
        if not d:
            return
        if d not in sys.path:
            sys.path.insert(0, d)
        self.out.delete("1.0", "end")
        self.out.insert("end", "算中…（第一次要载星历，慢一点）\n")
        self.update_idletasks()
        try:
            import guaxu_core as G
        except Exception as ex:
            self.out.insert("end", f"\n载不进 guaxu_core：\n{ex}\n"
                                   "（多半是 swisseph／ephem 没装。）")
            return
        try:
            def rd(es):
                return (int(es[0].get()), int(es[1].get()), int(es[2].get()))
            by, bm, bd = rd(self.e_b)
            ny, nm, nd = rd(self.e_n)
            rb = G.compute_all(by, bm, bd, 12, 0)
            rn = G.compute_all(ny, nm, nd, 12, 0)
            sb = rb["套"]["甲"]
            sn = rn["套"]["甲"]
            jb = G.jd_from(by, bm, bd, 12.0) - 8 / 24.0
            jn = G.jd_from(ny, nm, nd, 12.0) - 8 / 24.0
            age = G.sui_index(jn) - G.sui_index(jb)
            self.out.delete("1.0", "end")
            self.out.insert("end",
                            f"出生　卦年 {sb['卦年']['方']}"
                            f"（序 {sb['序号']['卦年']}）　四柱 "
                            f"{sb.get('四柱', '')}\n")
            self.out.insert("end",
                            f"现在　卦年 {sn['卦年']['方']}"
                            f"（序 {sn['序号']['卦年']}）　四柱 "
                            f"{sn.get('四柱', '')}\n\n")
            self.out.insert("end", f"智者说：过了 {age} 个岁首，"
                                   f"你今年 {age} 岁（虚岁 {age + 1}）。\n")
        except Exception as ex:
            self.out.insert("end", f"\n算不了：{ex}")


# ══════════════════════════════════════════════════════════════════════
#  七、自检
# ══════════════════════════════════════════════════════════════════════

def self_test(verbose=True):
    fails = []
    count = [0]

    def ck(name, cond):
        count[0] += 1
        if not cond:
            fails.append(name)

    # A. 表格完整
    ck("A1 八卦八个", len(TRIGRAMS) == 8)
    ck("A2 八卦爻不重复", len(set(t[10] for t in TRIGRAMS)) == 8)
    ck("A3 方图 64 不重复", len(FANG_TU) == 64 == len(set(FANG_TU)))
    ck("A4 周易 64 不重复", len(ZHOUYI_TU) == 64 == len(set(ZHOUYI_TU)))
    ck("A5 两表同一套卦", set(FANG_TU) == set(ZHOUYI_TU))

    # B. 方图序 ＝ 上卦为纲、下卦为目，两者都走先天序 乾兑离震巽坎艮坤
    for ui, u in enumerate(TRI_NAME):
        for li, l in enumerate(TRI_NAME):
            bits = list(TRI_BITS[l]) + list(TRI_BITS[u])
            name, idx, up, low = hexagram_name(bits)
            ck(f"B {u}上{l}下 序号", idx == ui * 8 + li + 1)
            ck(f"B {u}上{l}下 名称", name == FANG_TU[ui * 8 + li])
            ck(f"B {u}上{l}下 上卦", up == u and low == l)

    # C. 已知卦逐个核对
    for nm, up, low, idx in (("乾为天", "乾", "乾", 1),
                             ("天地否", "乾", "坤", 8),
                             ("火泽睽", "离", "兑", 18),
                             ("风火家人", "巽", "离", 35),
                             ("地雷复", "坤", "震", 60),
                             ("地水师", "坤", "坎", 62),
                             ("坤为地", "坤", "坤", 64)):
        bits = list(TRI_BITS[low]) + list(TRI_BITS[up])
        n2, i2, u2, l2 = hexagram_name(bits)
        ck(f"C {nm}", (n2, i2, u2, l2) == (nm, idx, up, low))

    # D. 卦符对得上周易序
    ck("D1 乾符", HEX_SYM["乾为天"] == "䷀")
    ck("D2 坤符", HEX_SYM["坤为地"] == "䷁")
    ck("D3 未济符", HEX_SYM["火水未济"] == chr(0x4DC0 + 63))
    ck("D4 六十四个符不重复", len(set(HEX_SYM.values())) == 64)

    # E. 爻位方向：上爻在上、初爻在下
    r = Rope(KIND_HEX, yao=[1, 1, 1, 0, 0, 0])      # 下乾 上坤 = 地天泰
    ck("E1 地天泰", r.gua()[1] == "地天泰")
    r2 = Rope(KIND_TRI, yao=[1, 0, 1])              # 初阳 二阴 三阳 = 离
    ck("E2 离", r2.gua()[1] == "离")
    ck("E3 预设全阴", Rope(KIND_HEX).gua()[1] == "坤为地")
    ck("E4 三爻预设坤", Rope(KIND_TRI).gua()[1] == "坤")

    # F. 十进制位值
    ck("F1 十五", digits_of(15) == [1, 5])
    ck("F2 初三", digits_of(3) == [3])
    ck("F3 六六", digits_of(66) == [6, 6])
    ck("F4 二十", digits_of(20) == [2, 0])
    ck("F5 补位", digits_of(3, 3) == [0, 0, 3])
    ck("F6 结数 15", Rope(KIND_DEC, value=15).n_levels() == 1 + 5 + 1)
    ck("F7 结数 20", Rope(KIND_DEC, value=20).n_levels() == 2 + 1 + 1)

    # G. 存读往返
    for name, doc in sample_docs().items():
        blob = json.dumps(doc.to_dict(), ensure_ascii=False)
        back = Doc.from_dict(json.loads(blob))
        ck(f"G 往返 {name}",
           json.dumps(back.to_dict(), ensure_ascii=False) == blob)

    # H. 示例内容对得上原例
    s = sample_docs()

    def content(doc):
        """跳过分割横结，只留有内容的根绳。"""
        return [r for r in doc.ropes if r.kind != KIND_CUT]

    def cuts_between_fields(doc):
        """每一对相邻的内容绳（栏位不同时）中间都要有分割横结。"""
        rs = doc.ropes
        for i in range(len(rs) - 1):
            a, b = rs[i], rs[i + 1]
            if a.kind == KIND_CUT or b.kind == KIND_CUT:
                continue
            if a.role != ROLES[0] and b.role != ROLES[0] and a.role != b.role:
                return False
        return True
    d3 = s["例三　死亡记录"]
    ck("H1 例三 第3条是15", content(d3)[2].value == 15)
    ck("H2 例三 风火家人", content(d3)[3].gua()[1] == "风火家人")
    ck("H3 例三 六六", content(d3)[4].value == 66)
    ck("H4 例三 右接乾为天", content(d3)[4].children[0].gua()[1] == "乾为天")
    ck("H5 例三 再右接坤为地",
       content(d3)[4].children[0].children[0].gua()[1] == "坤为地")
    ck("H6 例三 死1人", content(d3)[5].value == 1)
    d2 = s["例二　出生证明"]
    ck("H7 例二 初三", content(d2)[2].value == 3)
    ck("H8 例二 地雷复", content(d2)[4].children[0].gua()[1] == "地雷复")
    d4 = s["例四　东征鬼方"]
    ck("H9 例四 震为东", content(d4)[2].gua()[1] == "震")
    ck("H10 例四 地水师", content(d4)[3].gua()[1] == "地水师")
    ck("H11 例四 火泽睽", content(d4)[3].children[0].gua()[1] == "火泽睽")
    ck("H12 例四 乾为天胜",
       content(d4)[3].children[0].children[0].gua()[1] == "乾为天")
    ck("H13 例四 俘20", content(d4)[4].value == 20)
    d1 = s["例一　天旱马死"]
    ck("H14 例一 乾天", content(d1)[1].gua()[1] == "乾")
    ck("H15 例一 右接离", content(d1)[1].children[0].gua()[1] == "离")
    ck("H16 例一 天干6", content(d1)[4].value == 6)
    ck("H16b 例一 天干6 用的是天干绳",
       content(d1)[4].kind == KIND_GAN)
    ck("H16c 例一 天干6 打六个结", content(d1)[4].n_levels() == 6)

    # I. 后天方位（地点栏用得到）
    for t, p in (("坎", "北"), ("离", "南"), ("震", "东"), ("兑", "西"),
                 ("乾", "西北"), ("坤", "西南"), ("艮", "东北"), ("巽", "东南")):
        ck(f"I {t}{p}", TRIGRAMS[TRI_IDX[t]][7] == p)

    # J. 说卦动物（照「八卦代表动物」表）
    for t, a in (("乾", "马"), ("坤", "牛"), ("震", "龙"), ("巽", "鸡"),
                 ("坎", "豕"), ("离", "雉"), ("艮", "狗"), ("兑", "羊")):
        ck(f"J {t}为{a}", TRIGRAMS[TRI_IDX[t]][5] == a)

    # K. 例五／例六（后来补的两个说法）
    d5 = s["例五　全军覆没"]
    ck("K1 例五 地水师", content(d5)[3].gua()[1] == "地水师")
    ck("K2 例五 坤为地没了",
       content(d5)[3].children[0].children[0].gua()[1] == "坤为地")
    ck("K3 例五 六爻全阴",
       content(d5)[3].children[0].children[0].yao == [0] * 6)
    ck("K4 例五 死20", content(d5)[4].value == 20)
    d6 = s["例六　长写法 3979 年"]
    ck("K5 例六 3979", content(d6)[0].value == 3979)
    ck("K6 例六 3979 位值", digits_of(3979) == [3, 9, 7, 9])
    ck("K7 例六 3979 结数",
       content(d6)[0].n_levels() == 3 + 9 + 7 + 9 + 3)
    ck("K8 例六 年后面接分割横结", d6.ropes[1].kind == KIND_CUT)
    ck("K9 例六 七月", content(d6)[1].value == 7)
    ck("K9b 例六 初三", content(d6)[2].value == 3)

    # K2. 例七 登基：一个栏位好几条绳
    d7 = s["例七　登基"]
    ck("K10 例七 3979", content(d7)[0].value == 3979)
    ck("K11 例七 地点两条", [r.role for r in content(d7)[3:5]]
       == ["方位·地点"] * 2)
    ck("K12 例七 天", content(d7)[3].gua()[1] == "乾为天")
    ck("K13 例七 羊", content(d7)[4].gua()[1] == "兑为泽")
    ck("K14 例七 兑为羊", TRIGRAMS[TRI_IDX["兑"]][5] == "羊")
    ck("K15 例七 八号辛", content(d7)[7].value == 8
       and GAN10[7] == "辛")
    ck("K15b 例七 八号辛 是天干绳打八个结",
       content(d7)[7].kind == KIND_GAN
       and content(d7)[7].n_levels() == 8)
    ck("K16 例七 火地晋", content(d7)[8].gua()[1] == "火地晋")
    ck("K17 例七 火地晋是离上坤下",
       hexagram_name(content(d7)[8].yao)[2:] == ("离", "坤"))
    ck("K18 例七 无人挑战 1", content(d7)[9].value == 1)

    # M. 大横结：零不能留空
    b = Rope(KIND_BIG)
    ck("M1 大横结一层", b.n_levels() == 1)
    ck("M2 大横结读作0", b.headline() == "0")
    ck("M3 大横结无卦", b.gua() is None)
    ck("M4 大横结存读", Rope.from_dict(b.to_dict()).kind == KIND_BIG)
    ck("M5 二十＝2结＋大横结", digits_of(20) == [2, 0])
    ck("M6 二十共4层", Rope(KIND_DEC, value=20).n_levels() == 4)
    ck("M7 一百零五", digits_of(105) == [1, 0, 5])
    ck("M8 一百零五共8层",
       Rope(KIND_DEC, value=105).n_levels() == 1 + 1 + 5 + 2)
    ck("M9 零本身也是一个大横结", digits_of(0) == [0])
    ck("M10 零一层", Rope(KIND_DEC, value=0).n_levels() == 1)
    ck("M11 大横结样式有自己的尺寸", "big" in App.KNOT_SIZE)
    ck("M12 大横结比阳结宽",
       App.KNOT_SIZE["big"][0] > App.KNOT_SIZE["yang"][0])
    ck("M13 横绳上的结是普通结不是阳结", "tie" in App.KNOT_SIZE
       and App.KNOT_SIZE["tie"][0] < App.KNOT_SIZE["yang"][0])

    # M2. 结的尺寸阶梯 1 : 2 : 3（计数结 ／ 分位阳结 ／ 零）
    u = App.KNOT_SIZE["count"][0]
    ck("M14 阳结＝两个结宽", App.KNOT_SIZE["yang"][0] == u * 2)
    ck("M15 大横结＝三个结宽", App.KNOT_SIZE["big"][0] == u * 3)
    ck("M14b 一个结就是半个阴爻（阴结＝计数结＝一个单位）",
       App.KNOT_SIZE["yin"][0] == u == App.KNOT_SIZE["count"][0])
    ck("M14c 阴爻两个结不连在一起",
       STRAND_DX > App.KNOT_SIZE["yin"][0])
    ck("M16 三种宽度互不相同",
       len({App.KNOT_SIZE[k][0] for k in ("count", "yang", "big")}) == 3)
    ck("M17 分割是普通结，不是大横结",
       App.KNOT_SIZE["tie"][0] < App.KNOT_SIZE["big"][0])

    # M3. 分位阳结与分割横结
    sep = Rope(KIND_SEP)
    cut = Rope(KIND_CUT)
    ck("M18 分位阳结占一层", sep.n_levels() == 1)
    ck("M19 分割不占层", cut.n_levels() == 0)
    ck("M20 两者都不是卦", sep.gua() is None and cut.gua() is None)
    ck("M21 分位阳结存读", Rope.from_dict(sep.to_dict()).kind == KIND_SEP)
    ck("M22 分割存读", Rope.from_dict(cut.to_dict()).kind == KIND_CUT)
    ck("M23 三种分隔用的绳型各自独立",
       len({KIND_BIG, KIND_SEP, KIND_CUT}) == 3)

    # M5. 十二进制（地支）绳
    ck("P1 十二地支十二个", len(ZHI12) == 12)
    ck("P2 子丑寅卯", ZHI12[:4] == ["子", "丑", "寅", "卯"])
    ck("P3 亥在最后", ZHI12[-1] == "亥")
    # 地支是十二位的循环，不是位值制：亥就是十二个结
    d12 = Rope(KIND_DUO, value=12)
    ck("P4 亥＝12 个结", d12.n_levels() == 12)
    ck("P5 亥只有一段，不进位", d12.runs() == [12])
    ck("P6 子＝1 个结", Rope(KIND_DUO, value=1).n_levels() == 1)
    for v, nm in enumerate(ZHI12, start=1):
        r = Rope(KIND_DUO, value=v)
        ck(f"P7 {nm}＝{v} 个结", r.n_levels() == v and r.runs() == [v])
        ck(f"P8 {nm} 标题", r.headline() == f"{v}·{nm}")
    ck("P9 超过十二夹回亥", Rope(KIND_DUO, value=13).n_levels() == 12)
    ck("P10 零夹回子", Rope(KIND_DUO, value=0).n_levels() == 1)
    ck("P11 负数夹回子", zhi_clamp(-5) == 1)
    ck("P12 乱字夹回子", zhi_clamp("x") == 1)
    ck("P13 地支绳里没有零、没有大横结",
       all(d > 0 for d in Rope(KIND_DUO, value=12).runs()))
    ck("P14 十进绳照旧是位值制", Rope(KIND_DEC, value=3979).runs()
       == [3, 9, 7, 9])
    ck("P15 十进 12 还是 1｜2 四层",
       Rope(KIND_DEC, value=12).n_levels() == 1 + 1 + 2)
    ck("P16 同样是 12，地支绳 12 层、十进绳 4 层",
       Rope(KIND_DUO, value=12).n_levels() == 12
       and Rope(KIND_DEC, value=12).n_levels() == 4)
    ck("P17 地支名 1＝子", cyc_name(1, 12) == "子")
    ck("P18 地支名 12＝亥", cyc_name(12, 12) == "亥")
    ck("P19 地支名 13 没有", cyc_name(13, 12) == "")
    ck("P20 天干名 8＝辛", cyc_name(8, 10) == "辛")
    ck("P21 天干名 11 没有", cyc_name(11, 10) == "")
    ck("P22 地支绳标题带地支", d12.headline() == "12·亥")
    ck("P22b 地支绳不带位值写法", "₁₂" not in d12.headline())
    ck("P23 存读往返", Rope.from_dict(d12.to_dict()).kind == KIND_DUO)
    ck("P24 存读留住数值", Rope.from_dict(d12.to_dict()).value == 12)
    ck("P25 地支绳没有卦", d12.gua() is None)
    ck("P26 地支上限十二", ZHI_MAX == 12 == len(ZHI12))
    ck("P27 天干上限十", GAN_MAX == 10 == len(GAN10))

    # 天干绳：跟地支同一套规矩 —— 十就是十个结
    for v, nm in enumerate(GAN10, start=1):
        r = Rope(KIND_GAN, value=v)
        ck(f"P28 {nm}＝{v} 个结", r.n_levels() == v and r.runs() == [v])
        ck(f"P29 {nm} 标题", r.headline() == f"{v}·{nm}")
    ck("P30 癸＝10 个结（如同亥＝12 个结）",
       Rope(KIND_GAN, value=10).n_levels() == 10)
    ck("P31 天干超过十夹回癸",
       Rope(KIND_GAN, value=11).n_levels() == 10)
    ck("P32 天干绳只有一段，不进位",
       Rope(KIND_GAN, value=10).runs() == [10])
    ck("P33 天干绳里没有零", all(d > 0 for d in Rope(KIND_GAN, value=10).runs()))
    ck("P34 同样是 10：天干绳 10 层、十进绳 3 层（1｜分位｜大横结）",
       Rope(KIND_GAN, value=10).n_levels() == 10
       and Rope(KIND_DEC, value=10).n_levels() == 3)
    # 一位数的十进制绳跟同值的天干绳在绳上是同一串结，所以一并注干名；
    # 两位以上不注 —— 十进制的 10 只有三个结，跟癸的十个结不是一回事。
    ck("P35a 一位数的十进制绳也注干名",
       Rope(KIND_DEC, value=3).headline() == "3·丙")
    ck("P35b 一位数十进制与同值天干绳，绳上同一串结",
       Rope(KIND_DEC, value=3).n_levels()
       == Rope(KIND_GAN, value=3).n_levels() == 3)
    ck("P35c 十进制 10 不注癸（只有三个结）",
       Rope(KIND_DEC, value=10).headline() == "10")
    ck("P35d 十进制 10 跟天干癸不是同一串",
       Rope(KIND_DEC, value=10).n_levels() == 3
       and Rope(KIND_GAN, value=10).n_levels() == 10)
    ck("P35e 大数不注干名",
       Rope(KIND_DEC, value=3979).headline() == "3979")
    ck("P35f 循环绳 cval 夹得住",
       Rope(KIND_GAN, value=99).cval() == 10
       and Rope(KIND_DUO, value=99).cval() == 12)
    ck("P36 两种循环绳都登记了", set(CYCLES) == {KIND_GAN, KIND_DUO})
    ck("P37 循环绳位数对", CYCLES[KIND_GAN][0] == 10
       and CYCLES[KIND_DUO][0] == 12)
    ck("P38 存读留住绳型",
       Rope.from_dict(Rope(KIND_GAN, value=6).to_dict()).kind == KIND_GAN)
    ck("P39 天干绳没有卦", Rope(KIND_GAN, value=6).gua() is None)
    ck("P40 夹边界：0 与负数都回甲",
       cyc_clamp(0, 10) == 1 and cyc_clamp(-3, 10) == 1)

    # M4. 12 要读成 1｜2；3979 要读成 3｜9｜7｜9（位间一定有一个分位阳结）
    for v, want in ((12, [1, 2]), (3979, [3, 9, 7, 9]), (105, [1, 0, 5])):
        ds = digits_of(v)
        ck(f"M24 {v} 的位", ds == want)
        # 层数 ＝ 每位的结数（零算一个大横结）＋ 位间的分位阳结
        ck(f"M25 {v} 的层数含分位结",
           Rope(KIND_DEC, value=v).n_levels()
           == sum(max(d, 1) for d in ds) + len(ds) - 1)
    ck("M26 12 共四层（1 ＋分位＋ 2）",
       Rope(KIND_DEC, value=12).n_levels() == 1 + 1 + 2)
    ck("M27 3979 共三十一层",
       Rope(KIND_DEC, value=3979).n_levels() == 3 + 9 + 7 + 9 + 3)

    # N. 勾选项
    keys = [k for k, _, _ in DISPLAY_OPTS]
    ck("N1 勾选项不重复", len(keys) == len(set(keys)))
    for k in ("value", "gan", "place", "guaname", "fangidx",
              "yaopos", "note", "role", "hengjie"):
        ck(f"N {k} 在勾选表里", k in keys)
    dflt = {k: d for k, _, d in DISPLAY_OPTS}
    ck("N2 栏位标签预设关", dflt["role"] is False)
    ck("N3 位值注记预设关", dflt["place"] is False)
    ck("N4 数值天干预设开", dflt["value"] and dflt["gan"])
    ck("N5 结距可选四档", len(GAP_LEVELS) == 4 == len(DEC_GAP_LEVELS))
    ck("N6 计数结距比阴阳结距密",
       DEC_GAP_LEVELS[0][1] < GAP_LEVELS[0][1]
       and DEC_GAP_LEVELS[-1][1] < GAP_LEVELS[-1][1])
    ck("N7 预设计数结距在表里",
       DEC_GAP in [v for _, v in DEC_GAP_LEVELS])
    ck("N8 预设阴阳结距在表里",
       KNOT_GAP in [v for _, v in GAP_LEVELS])

    # Q. 完备性：阴一定要打结，不能空着
    for name in TRI_NAME:
        bits = TRI_BITS[name]
        r = Rope(KIND_TRI, yao=list(bits))
        ck(f"Q1 {name} 三爻都在", r.n_levels() == 3)
        for i, b in enumerate(bits):
            ck(f"Q2 {name} 第{i+1}爻不是空的", b in (0, 1))
    ck("Q3 全阴的坤照样三层，不是空绳",
       Rope(KIND_TRI, yao=[0, 0, 0]).n_levels() == 3)
    ck("Q4 全阴的坤为地照样六层",
       Rope(KIND_HEX, yao=[0] * 6).n_levels() == 6)
    ck("Q5 六十四卦每一卦都是六层，没有一卦会缩水",
       all(Rope(KIND_HEX, yao=[(i >> k) & 1 for k in range(6)]).n_levels() == 6
           for i in range(64)))
    ck("Q6 六十四卦互不重复（完备）",
       len({hexagram_name([(i >> k) & 1 for k in range(6)])[0]
            for i in range(64)}) == 64)
    ck("Q7 六十四卦刚好盖满方图",
       {hexagram_name([(i >> k) & 1 for k in range(6)])[0]
        for i in range(64)} == set(FANG_TU))
    ck("Q8 零也一定打结（大横结），不留空",
       Rope(KIND_DEC, value=20).n_levels() == 4
       and Rope(KIND_DEC, value=0).n_levels() == 1)

    # R. 人名：卦象是氏，数字是名
    d8 = s["例八　人名 小川88"]
    ck("R1 例八 水地比", content(d8)[3].gua()[1] == "水地比")
    ck("R2 例八 名是 88", content(d8)[4].value == 88)
    ck("R3 例八 两条都在人这一栏",
       [r.role for r in content(d8)[3:5]] == ["人", "人"])
    ck("R4 例八 注释存得住", "小川" in d8.note)

    # L. 释读／注解跑得起来且不漏内容
    for name, doc in s.items():
        txt = " ".join(_read_plain(doc))
        for r in doc.walk():
            if r.note:
                ck(f"L {name} 旁注进释读",
                   r.note.splitlines()[0] in txt)

    total = count[0]
    if verbose:
        print(f"自检 {total - len(fails)}/{total} 通过")
        for f in fails:
            print("  X", f)
    return fails


def _read_plain(doc):
    """不开 GUI 也能产生释读文字（自检用）。"""
    out = []

    def one(r, depth):
        tag = "" if r.role == ROLES[0] else f"〔{r.role}〕"
        note = f"（{r.note})" if r.note else ""
        if r.kind == KIND_FEN:
            out.append(f"{tag}｜分段｜{note}")
        elif r.kind in (KIND_BIG, KIND_SEP, KIND_CUT):
            out.append(f"{tag}{r.headline()}{note}")
        elif r.kind in KIND_COUNT:
            out.append(f"{tag}{r.value}{note}")
        else:
            out.append(f"{tag}{r.gua()[1]}{note}")
        for c in r.children:
            one(c, depth + 1)

    for r in doc.ropes:
        one(r, 0)
    return out


# ══════════════════════════════════════════════════════════════════════

def main():
    if "--selftest" in sys.argv:
        sys.exit(1 if self_test() else 0)
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
