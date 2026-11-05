"""Page texts of the site in English, Chinese and German, and the translation of the text fields of codes/*.json
(construction, search method, provenance, citation). Code family names (lifted-product, two-block, pair-partition)
stay in English in every language: they are the names used in the literature and in the data."""
import re

LANGS = ("en", "zh", "de")
LANG_NAME = {"en": "English", "zh": "中文", "de": "Deutsch"}
HTML_LANG = {"en": "en", "zh": "zh-CN", "de": "de"}
# path of each language's page relative to docs/
PAGE_DIR = {"en": "", "zh": "zh/", "de": "de/"}

T = {
    "en": dict(
        brand1="qLDPC verified board", brand2="Quantum LDPC codes with checkable distances",
        title="Verified qLDPC codes",
        h1="Verified quantum LDPC codes",
        intro='Codes found by structured concept evolution (SCE, <a href="https://arxiv.org/abs/2606.24808">arXiv:2606.24808</a>) and entries of the Unitary Foundation qLDPC\nchallenge re-measured with the same search; encoding rate k/n above 0.1. Every row says what is proven about the distance and links the files to check it.',
        h_summary="Summary", h_explore="Explore", h_codes="Codes",
        card_exact_lab="best certified code, check weight %s",
        card_val_family="k d²/n = <b>%.1f</b> · %s",
        card_bound_lab="best search bound (operator published)",
        card_bound_val="k d²/n = <b>%.1f</b> · check weight %d",
        card_bound_sub="lightest operator found by the v5 search; the true distance may be smaller",
        card_board_lab="leaderboard claims re-measured",
        card_board_big="%d of %d not reproduced",
        card_board_item="%s claimed ≤%d, found %d (%s)",
        card_board_none="none",
        card_board_held="the other %d claims held under 600 s to 7200 s searches",
        f_family="family", f_all="all", f_status="status", f_origin="origin", f_weight="check weight", f_to="to",
        f_pub="published codes", f_pend="rows with a pending operator file", f_surf="3-D surface",
        f_surf_proven="proven distances", f_surf_all="incl. search bounds", f_surf_none="none",
        p1_title="k d²/n against n",
        p1_note="Circle lifted-product, diamond two-block, square pair-partition; filled exact, open search bound, triangle lower bound; black edge SCE, grey leaderboard with a dashed line from the claimed value; small light markers published codes. Hover for [[n,k,d]].",
        p2_title="Frontier in (n, w, k d²/n)",
        p2_note="Points as on the left (colour by family, SCE in dark edges). The surface is the frontier F(n, w) = largest k d²/n among the shown codes with at most n qubits and check weight at most w, from proven distances or including search bounds. Drag to rotate, scroll to zoom.",
        codes_note="Sorted by k d²/n, largest first; click a column head to sort differently. Rows with identical parameters are merged (×2 = two inequivalent codes, distinct spectra). Internal run names are in the provenance fold of each row.",
        th=("code", "n", "k", "d", "w", "k d²/n", "family", "status", "origin", "construction", "evidence", "files"),
        tag_claimed="claimed ≤%d", tag_pending="operator file pending", provenance="provenance",
        l_ops="operators", l_entry="entry",
        footer='Data and tools: <a href="https://github.com/ziduliu/qldpc-verified-board">github.com/ziduliu/qldpc-verified-board</a>. Pair-partition construction: Okada and Kasai, arXiv:2607.14091; Lee et al., arXiv:2609.30069. Leaderboard: unitaryfoundation/qldpc-challenge.',
        status={"exact": "exact", "search bound": "search bound", "lower bound": "lower bound", "bounded": "bounded"},
        origin={"SCE": "SCE", "leaderboard, re-measured": "leaderboard, re-measured"},
        ev_cert="certificate: no logical operator of weight ≤ %s on either side",
        ev_parity=", and all logical weights are even (all-ones vector in both row spaces), so d ≥ %d",
        ev_explicit="; explicit operators of weight %d",
        ev_found="; an operator of weight %d was found by the certifier (operator file pending)",
        js=dict(rows="{n} rows shown", xlab="n (data qubits)", claimed="claimed", sce="SCE", board="leaderboard, re-measured",
                pub="published", front="frontier", waxis="check weight w",
                fhover="n ≤ %{x}, w ≤ %{y}: best k d²/n %{z:.0f}"),
    ),
    "zh": dict(
        brand1="经过验证的 qLDPC 码表", brand2="码距可以核验的量子 LDPC 码",
        title="经过验证的 qLDPC 码",
        h1="经过验证的量子 LDPC 码",
        intro='由结构化概念演化（SCE，<a href="https://arxiv.org/abs/2606.24808">arXiv:2606.24808</a>）找到的码，以及用同一种搜索重新测量的 Unitary Foundation qLDPC\n挑战赛条目；只列出编码率 k/n 大于 0.1 的码。每一行都写明关于码距已经证明了什么，并链接到可以用来核验的文件。',
        h_summary="概览", h_explore="浏览", h_codes="码列表",
        card_exact_lab="最佳已认证码，校验权重 %s",
        card_val_family="k d²/n = <b>%.1f</b> · %s",
        card_bound_lab="最佳搜索上界（算符已公开）",
        card_bound_val="k d²/n = <b>%.1f</b> · 校验权重 %d",
        card_bound_sub="v5 搜索找到的最轻算符；真实码距可能更小",
        card_board_lab="重新测量的排行榜声明",
        card_board_big="%d 个未能复现（共 %d 个）",
        card_board_item="%s 声称 ≤%d，找到 %d（%s）",
        card_board_none="无",
        card_board_held="其余 %d 个声明在 600 s 到 7200 s 的搜索中没有被推翻",
        f_family="码族", f_all="全部", f_status="状态", f_origin="来源", f_weight="校验权重", f_to="到",
        f_pub="已发表的码", f_pend="显示算符文件待补的行", f_surf="三维曲面",
        f_surf_proven="已证明的码距", f_surf_all="包含搜索上界", f_surf_none="不显示",
        p1_title="k d²/n 对 n",
        p1_note="圆形为 lifted-product，菱形为 two-block，方形为 pair-partition；实心为精确值，空心为搜索上界，三角形为下界；黑边为 SCE 找到的码，灰色为排行榜条目，虚线从声称值画到我们找到的值；浅色小标记为已发表的码。鼠标停在点上显示 [[n,k,d]]。",
        p2_title="(n, w, k d²/n) 中的前沿",
        p2_note="点的画法同左图（颜色表示码族，SCE 的码为深色边）。曲面是前沿 F(n, w)：在显示的码中，量子比特数不超过 n、校验权重不超过 w 的码的最大 k d²/n，按已证明的码距计算，或包含搜索上界。拖动可以旋转，滚轮可以缩放。",
        codes_note="按 k d²/n 从大到小排序；点击列标题可以按其他列排序。参数相同的行已合并（×2 表示两个不等价的码，谱不同）。内部运行名称在每行的“来源记录”折叠栏里。",
        th=("码", "n", "k", "d", "w", "k d²/n", "码族", "状态", "来源", "构造", "证据", "文件"),
        tag_claimed="声称 ≤%d", tag_pending="算符文件待补", provenance="来源记录",
        l_ops="算符", l_entry="条目",
        footer='数据和工具：<a href="https://github.com/ziduliu/qldpc-verified-board">github.com/ziduliu/qldpc-verified-board</a>。pair-partition 构造：Okada 和 Kasai，arXiv:2607.14091；Lee 等，arXiv:2609.30069。排行榜：unitaryfoundation/qldpc-challenge。',
        status={"exact": "精确", "search bound": "搜索上界", "lower bound": "下界", "bounded": "有界"},
        origin={"SCE": "SCE", "leaderboard, re-measured": "排行榜，重新测量"},
        ev_cert="证书：两侧都没有重量 ≤ %s 的逻辑算符",
        ev_parity="，并且所有逻辑算符的重量都是偶数（两个行空间都含全 1 向量），所以 d ≥ %d",
        ev_explicit="；给出了重量为 %d 的具体算符",
        ev_found="；认证程序找到了一个重量为 %d 的算符（算符文件待补）",
        js=dict(rows="显示 {n} 行", xlab="n（数据量子比特数）", claimed="声称值", sce="SCE", board="排行榜，重新测量",
                pub="已发表", front="前沿", waxis="校验权重 w",
                fhover="n ≤ %{x}，w ≤ %{y}：最大 k d²/n %{z:.0f}"),
    ),
    "de": dict(
        brand1="Verifizierte qLDPC-Tabelle", brand2="Quanten-LDPC-Codes mit prüfbaren Distanzen",
        title="Verifizierte qLDPC-Codes",
        h1="Verifizierte Quanten-LDPC-Codes",
        intro='Codes, die mit strukturierter Konzeptevolution (SCE, <a href="https://arxiv.org/abs/2606.24808">arXiv:2606.24808</a>) gefunden wurden, und Einträge der qLDPC-Challenge\nder Unitary Foundation, mit derselben Suche neu vermessen; nur Codes mit Coderate k/n über 0.1. Jede Zeile gibt an, was über die Distanz bewiesen ist, und verlinkt die Dateien, mit denen man es prüfen kann.',
        h_summary="Übersicht", h_explore="Erkunden", h_codes="Codes",
        card_exact_lab="bester zertifizierter Code, Prüfgewicht %s",
        card_val_family="k d²/n = <b>%.1f</b> · %s",
        card_bound_lab="beste Suchschranke (Operator veröffentlicht)",
        card_bound_val="k d²/n = <b>%.1f</b> · Prüfgewicht %d",
        card_bound_sub="leichtester Operator, den die v5-Suche gefunden hat; die wahre Distanz kann kleiner sein",
        card_board_lab="neu vermessene Angaben der Bestenliste",
        card_board_big="%d von %d nicht reproduziert",
        card_board_item="%s angegeben ≤%d, gefunden %d (%s)",
        card_board_none="keine",
        card_board_held="die übrigen %d Angaben wurden von Suchen mit 600 s bis 7200 s nicht widerlegt",
        f_family="Familie", f_all="alle", f_status="Status", f_origin="Quelle", f_weight="Prüfgewicht", f_to="bis",
        f_pub="veröffentlichte Codes", f_pend="Zeilen mit ausstehender Operatordatei", f_surf="3D-Fläche",
        f_surf_proven="bewiesene Distanzen", f_surf_all="mit Suchschranken", f_surf_none="keine",
        p1_title="k d²/n gegen n",
        p1_note="Kreis lifted-product, Raute two-block, Quadrat pair-partition; gefüllt exakt, offen Suchschranke, Dreieck untere Schranke; schwarzer Rand SCE, grau Bestenliste, mit einer gestrichelten Linie vom angegebenen Wert; kleine helle Symbole veröffentlichte Codes. Mit der Maus über einem Punkt erscheint [[n,k,d]].",
        p2_title="Front in (n, w, k d²/n)",
        p2_note="Punkte wie links (Farbe nach Familie, SCE mit dunklem Rand). Die Fläche ist die Front F(n, w) = größtes k d²/n unter den angezeigten Codes mit höchstens n Qubits und Prüfgewicht höchstens w, aus bewiesenen Distanzen oder einschließlich der Suchschranken. Ziehen dreht die Ansicht, Scrollen zoomt.",
        codes_note="Nach k d²/n sortiert, größter Wert zuerst; ein Klick auf einen Spaltenkopf sortiert nach dieser Spalte. Zeilen mit gleichen Parametern sind zusammengefasst (×2 = zwei nicht äquivalente Codes, verschiedene Spektren). Interne Laufnamen stehen im aufklappbaren Feld „Herkunft“ jeder Zeile.",
        th=("Code", "n", "k", "d", "w", "k d²/n", "Familie", "Status", "Quelle", "Konstruktion", "Nachweis", "Dateien"),
        tag_claimed="angegeben ≤%d", tag_pending="Operatordatei ausstehend", provenance="Herkunft",
        l_ops="Operatoren", l_entry="Eintrag",
        footer='Daten und Werkzeuge: <a href="https://github.com/ziduliu/qldpc-verified-board">github.com/ziduliu/qldpc-verified-board</a>. Pair-Partition-Konstruktion: Okada und Kasai, arXiv:2607.14091; Lee et al., arXiv:2609.30069. Bestenliste: unitaryfoundation/qldpc-challenge.',
        status={"exact": "exakt", "search bound": "Suchschranke", "lower bound": "untere Schranke", "bounded": "beschränkt"},
        origin={"SCE": "SCE", "leaderboard, re-measured": "Bestenliste, neu vermessen"},
        ev_cert="Zertifikat: kein logischer Operator mit Gewicht ≤ %s auf einer der beiden Seiten",
        ev_parity=", und alle logischen Gewichte sind gerade (Einsvektor in beiden Zeilenräumen), also d ≥ %d",
        ev_explicit="; explizite Operatoren mit Gewicht %d",
        ev_found="; der Zertifizierer hat einen Operator mit Gewicht %d gefunden (Operatordatei ausstehend)",
        js=dict(rows="{n} Zeilen angezeigt", xlab="n (Datenqubits)", claimed="angegeben", sce="SCE", board="Bestenliste, neu vermessen",
                pub="veröffentlicht", front="Front", waxis="Prüfgewicht w",
                fhover="n ≤ %{x}, w ≤ %{y}: bestes k d²/n %{z:.0f}"),
    ),
}


def _apply(s, rules):
    for pat, rep in rules:
        s = re.sub(pat, rep, s)
    return s


# ---- construction ------------------------------------------------------------------------------------------------
_CONS = {
    "zh": [
        (r" ?\(written (.+?) by the program\)", r"（程序中写作 \1）"),
        (r" ?\(order (\d+), not cyclic\)", r"（阶 \1，非循环）"),
        (r" ?\(order (\d+)\)", r"（阶 \1）"),
        (r"^leaderboard entry (\S+) \((\S+)\), matrices rebuilt from the entry's check lists$", r"排行榜条目 \1（\2），矩阵由该条目的校验列表重建"),
        (r" acting on the (\d+) points of (.+?) by affine maps (.+?), template", r"，通过仿射映射 \3 作用在 \2 的 \1 个点上，模板"),
        (r"^cyclic group ", "循环群 "),
        (r"^group ", "群 "),
        (r", protograph shapes ", "，原模图形状 "),
        (r", template ", "，模板 "),
        (r" with one row removed$", "，去掉一行"),
        (r", shortened$", "，缩短"),
    ],
    "de": [
        (r"\(written (.+?) by the program\)", r"(im Programm als \1 geschrieben)"),
        (r"\(order (\d+), not cyclic\)", r"(Ordnung \1, nicht zyklisch)"),
        (r"\(order (\d+)\)", r"(Ordnung \1)"),
        (r"^leaderboard entry (\S+) \((\S+)\), matrices rebuilt from the entry's check lists$", r"Eintrag \1 der Bestenliste (\2), Matrizen aus den Prüflisten des Eintrags neu aufgebaut"),
        (r" acting on the (\d+) points of (.+?) by affine maps (.+?), template", r", wirkt durch affine Abbildungen \3 auf den \1 Punkten von \2, Vorlage"),
        (r"^cyclic group ", "zyklische Gruppe "),
        (r"^group ", "Gruppe "),
        (r", protograph shapes ", ", Protographformen "),
        (r", template ", ", Vorlage "),
        (r" with one row removed$", " mit einer entfernten Zeile"),
        (r", shortened$", ", verkürzt"),
    ],
}

# ---- search method (evidence of search-bound rows) ------------------------------------------------------------------
_METH = {
    "zh": [
        (r"^our GPU directed BP\+OSD search \(v5\)", "我们的 GPU 定向 BP+OSD 搜索（v5）"),
        (r"^GPU directed BP\+OSD search \(v5\)", "GPU 定向 BP+OSD 搜索（v5）"),
        (r"; the claimed distance held$", "；没有找到比声称值更轻的算符"),
        (r"; lighter operators than the claim exist, see the operator file$", "；存在比声称值更轻的算符，见算符文件"),
        (r"lightest (\d+) \(earlier run, operator not saved\); the stored operators have weight (\d+)", r"最轻 \1（较早的一次运行，算符没有保存）；保存下来的算符重量为 \2"),
        (r"(\d+) in all six$", r"六次都是 \1"),
        (r"(\d+) in all four$", r"四次都是 \1"),
        (r" seed ", " 种子 "),
        (r" and ", " 和 "),
        (r" \(v5\): ", "（v5）："),
        (r": ", "："),
        (r"; ", "；"),
    ],
    "de": [
        (r"^our GPU directed BP\+OSD search \(v5\)", "unsere gerichtete BP+OSD-Suche auf der GPU (v5)"),
        (r"^GPU directed BP\+OSD search \(v5\)", "gerichtete BP+OSD-Suche auf der GPU (v5)"),
        (r"; the claimed distance held$", "; kein leichterer Operator als angegeben gefunden"),
        (r"; lighter operators than the claim exist, see the operator file$", "; es gibt leichtere Operatoren als angegeben, siehe Operatordatei"),
        (r"lightest (\d+) \(earlier run, operator not saved\); the stored operators have weight (\d+)", r"leichtester \1 (frühere Suche, Operator nicht gespeichert); die gespeicherten Operatoren haben Gewicht \2"),
        (r"(\d+) in all six$", r"\1 in allen sechs"),
        (r"(\d+) in all four$", r"\1 in allen vier"),
        (r" seed ", " Seed "),
        (r" and ", " und "),
    ],
}

# ---- provenance (collapsed fold) ------------------------------------------------------------------------------------
_PROV = {
    "zh": [
        (r"^Unitary Foundation qLDPC challenge, snapshot (\w+) \(([\d-]+)\), entry (\S+)$", r"Unitary Foundation qLDPC 挑战赛，快照 \1（\2），条目 \3"),
        (r"^run (\S+) \((\S+), (FOM|CLER) objective\), rate cell (\d+); ", r"运行 \1（\2，目标为 \3），码率区间 \4；"),
        (r"^level-(\d+) refinement run of the (\d+)th child of the weight-(\d+) run \((\S+)\), replicate (\d+), child (\d+); ",
         r"对权重 \3 运行的第 \2 个子程序做的 \1 级细化运行（\4），第 \5 次重复，第 \6 个子程序；"),
        (r"^evolution run (\S+) \((.+?) proposer\), program (\w+), candidate (\d+)$", r"演化运行 \1（提议模型 \2），程序 \3，候选 \4"),
        (r"^evolution line (\S+) \((\S+), ([\d-]+)\), ", r"演化线 \1（\2，\3），"),
        (r"first-generation child (\w+)", r"第一代子程序 \1"),
        (r"step (\d+), second generation from the seed; construction record (\S+) of the run", r"第 \1 步，种子程序之后的第二代；该运行的构造记录 \2"),
        (r"; one of two inequivalent codes with these parameters \(distinct spectra\)", "；参数相同的两个不等价码之一（谱不同）"),
        (r"; inequivalent to the other code with these parameters \(distinct spectra\)", "；与参数相同的另一个码不等价（谱不同）"),
        (r"program (\w+)", r"程序 \1"),
        (r"archive (\w+)", r"存档 \1"),
        (r", ", "，"),
    ],
    "de": [
        (r"^Unitary Foundation qLDPC challenge, snapshot (\w+) \(([\d-]+)\), entry (\S+)$", r"qLDPC-Challenge der Unitary Foundation, Stand \1 (\2), Eintrag \3"),
        (r"^run (\S+) \((\S+), (FOM|CLER) objective\), rate cell (\d+); ", r"Lauf \1 (\2, Zielgröße \3), Ratenintervall \4; "),
        (r"^level-(\d+) refinement run of the (\d+)th child of the weight-(\d+) run \((\S+)\), replicate (\d+), child (\d+); ",
         r"Verfeinerungslauf der Stufe \1 zum \2. Kind des Laufs mit Gewicht \3 (\4), Wiederholung \5, Kind \6; "),
        (r"^evolution run (\S+) \((.+?) proposer\), program (\w+), candidate (\d+)$", r"Evolutionslauf \1 (vorschlagendes Modell \2), Programm \3, Kandidat \4"),
        (r"^evolution line (\S+) \((\S+), ([\d-]+)\), ", r"Evolutionslinie \1 (\2, \3), "),
        (r"first-generation child (\w+)", r"Kind der ersten Generation \1"),
        (r"step (\d+), second generation from the seed; construction record (\S+) of the run", r"Schritt \1, zweite Generation nach dem Startprogramm; Konstruktionsprotokoll \2 des Laufs"),
        (r"; one of two inequivalent codes with these parameters \(distinct spectra\)", "; einer von zwei nicht äquivalenten Codes mit diesen Parametern (verschiedene Spektren)"),
        (r"; inequivalent to the other code with these parameters \(distinct spectra\)", "; nicht äquivalent zum anderen Code mit diesen Parametern (verschiedene Spektren)"),
        (r"program (\w+)", r"Programm \1"),
        (r"archive (\w+)", r"Archiv \1"),
    ],
}

# ---- citation (collapsed fold) --------------------------------------------------------------------------------------
_CITE = {
    "zh": [
        (r"^pair-partition construction \(Okada and Kasai, (\S+); Lee et al\., (\S+)\)", r"pair-partition 构造（Okada 和 Kasai，\1；Lee 等，\2）"),
        (r"; affine-permutation lifts \(APM\) as in (\S+) Sec\. (\S+)$", r"；仿射置换提升（APM），同 \1 第 \2 节"),
    ],
    "de": [
        (r"^pair-partition construction \(Okada and Kasai, (\S+); Lee et al\., (\S+)\)", r"Pair-Partition-Konstruktion (Okada und Kasai, \1; Lee et al., \2)"),
        (r"; affine-permutation lifts \(APM\) as in (\S+) Sec\. (\S+)$", r"; affine Permutations-Lifts (APM) wie in \1, Abschnitt \2"),
    ],
}


def construction(s, lang):
    return s if lang == "en" else _apply(s, _CONS[lang])


def method(s, lang):
    return s if lang == "en" else _apply(s, _METH[lang])


def provenance(s, lang):
    return s if lang == "en" else _apply(s, _PROV[lang])


def citation(s, lang):
    return s if lang == "en" else _apply(s, _CITE[lang])
