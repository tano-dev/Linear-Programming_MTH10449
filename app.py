"""
app.py — Giao diện Web cho Hệ thống Giải Quy hoạch Tuyến tính (LP Solver)
Chạy bằng lệnh: streamlit run app.py
"""

import io
import contextlib
import streamlit as st

st.set_page_config(
    page_title="LP Solver",
    page_icon="∂",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL STYLES — Academic / Scholarly aesthetic
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400&family=JetBrains+Mono:wght@400;500&family=Inter:wght@400;500;600&display=swap');

/* ── Root palette ─────────────────────────────────── */
:root {
    --ink:      #1c1c1e;
    --ink-2:    #3a3a3c;
    --ink-3:    #6e6e73;
    --rule:     #d1d1d6;
    --rule-2:   #e5e5ea;
    --paper:    #fafaf8;
    --paper-2:  #f2f2f0;
    --paper-3:  #eaeae7;
    --accent:   #0a3161;
    --accent-2: #1a5ca8;
    --accent-lt:#dce8f8;
    --green:    #14532d;
    --green-lt: #dcfce7;
    --red:      #7f1d1d;
    --red-lt:   #fee2e2;
    --amber:    #78350f;
    --amber-lt: #fef3c7;
}

/* ── Base ─────────────────────────────────────────── */
html, body, [data-testid="stAppViewContainer"] {
    background: var(--paper) !important;
    font-family: 'Inter', sans-serif;
}
[data-testid="stMainBlockContainer"] {
    padding-top: 2.5rem !important;
    max-width: 1100px !important;
}

/* ── Sidebar ──────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: var(--accent) !important;
    border-right: none !important;
}
[data-testid="stSidebar"] * { color: #e2ecf8 !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #ffffff !important;
    font-family: 'EB Garamond', Georgia, serif !important;
    font-weight: 500 !important;
}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stCheckbox span p {
    color: #b8d0ee !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.04em !important;
    text-transform: uppercase !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: #ffffff !important;
    border-color: rgba(255,255,255,0.4) !important;
    color: #1c1c1e !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] > div span,
[data-testid="stSidebar"] [data-baseweb="select"] > div div {
    color: #1c1c1e !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] svg { fill: #1c1c1e !important; }
[data-testid="stSidebar"] [data-testid="stCheckbox"] > label > div:first-child {
    border-color: rgba(255,255,255,0.35) !important;
    background: transparent !important;
}
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.15) !important; }

/* ── Page heading ─────────────────────────────────── */
.lp-masthead {
    display: flex;
    align-items: baseline;
    gap: 1rem;
    margin-bottom: 2.5rem;
    padding-bottom: 1rem;
    border-bottom: 1.5px solid var(--ink);
}
.lp-masthead .lp-title {
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 2.1rem;
    font-weight: 500;
    color: var(--ink);
    letter-spacing: -0.01em;
    margin: 0;
    line-height: 1;
}
.lp-masthead .lp-subtitle {
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    color: var(--ink-3);
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin: 0;
}

/* ── Section headers ──────────────────────────────── */
.section-label {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    font-family: 'Inter', sans-serif;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--ink-3);
    margin: 0 0 0.75rem;
}
.section-label .sn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 20px; height: 20px;
    border-radius: 50%;
    background: var(--accent);
    color: #fff;
    font-size: 0.65rem;
    font-weight: 600;
    flex-shrink: 0;
}

/* ── Cards / panels ───────────────────────────────── */
.panel {
    background: #ffffff;
    border: 1px solid var(--rule-2);
    border-radius: 6px;
    padding: 1.25rem 1.4rem;
    margin-bottom: 1.25rem;
}

/* ── Streamlit container border override ──────────── */
[data-testid="stVerticalBlock"] > [data-testid="element-container"] > div > div[style*="border"] {
    border: 1px solid var(--rule-2) !important;
    border-radius: 6px !important;
    background: #fff !important;
}

/* ── Number inputs ────────────────────────────────── */
[data-testid="stNumberInput"] input {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.92rem !important;
    text-align: center !important;
    background: #ffffff !important;
    border-color: var(--rule) !important;
    color: #1c1c1e !important;
}
[data-testid="stNumberInput"] input:focus {
    border-color: var(--accent-2) !important;
    box-shadow: 0 0 0 2px var(--accent-lt) !important;
    background: #ffffff !important;
    color: #1c1c1e !important;
}
[data-testid="stNumberInput"] input::placeholder {
    color: #9a9a9f !important;
}

/* ── Select boxes ─────────────────────────────────── */
[data-baseweb="select"] > div {
    border-color: var(--rule) !important;
    background: #ffffff !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.88rem !important;
    color: #1c1c1e !important;
}
[data-baseweb="select"] span,
[data-baseweb="select"] div {
    color: #1c1c1e !important;
}
[data-baseweb="menu"] li,
[data-baseweb="menu"] [role="option"] {
    background: #ffffff !important;
    color: #1c1c1e !important;
}
[data-baseweb="menu"] li:hover,
[data-baseweb="menu"] [role="option"]:hover {
    background: var(--accent-lt) !important;
    color: #1c1c1e !important;
}

/* ── Column headers ───────────────────────────────── */
.var-header {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.88rem;
    color: var(--ink-2);
    text-align: center;
    padding: 4px 0 6px;
    border-bottom: 1px solid var(--rule);
    margin-bottom: 8px;
}

/* ── LaTeX preview box ────────────────────────────── */
.preview-box {
    background: var(--paper-2);
    border: 1px solid var(--rule-2);
    border-left: 3px solid var(--accent);
    border-radius: 0 4px 4px 0;
    padding: 0.9rem 1.1rem;
    margin-top: 0.6rem;
    font-size: 0.9rem;
    color: var(--ink-2);
    overflow-x: auto;
}
.preview-label {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--ink-3);
    margin-bottom: 4px;
}

/* ── Solve button ─────────────────────────────────── */
div.stButton > button[kind="primary"] {
    background: var(--accent) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 4px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    letter-spacing: normal !important;
    text-transform: none !important;
    padding: 0.55rem 1.5rem !important;
    white-space: nowrap !important;
    min-width: 160px !important;
    width: 100% !important;
    transition: background 0.18s !important;
}
div.stButton > button[kind="primary"] p,
div.stButton > button[kind="primary"] span {
    color: #ffffff !important;
    white-space: nowrap !important;
}
div.stButton > button[kind="primary"]:hover {
    background: var(--accent-2) !important;
    color: #ffffff !important;
}

/* ── Result block ─────────────────────────────────── */
.result-wrapper {
    border-top: 1.5px solid var(--ink);
    padding-top: 1.5rem;
    margin-top: 2rem;
}
.result-heading {
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 1.5rem;
    font-weight: 500;
    color: var(--ink);
    margin: 0 0 1.2rem;
}

.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    font-family: 'Inter', sans-serif;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 5px 14px;
    border-radius: 100px;
    margin-bottom: 1.2rem;
}
.pill-optimal    { background: var(--green-lt); color: var(--green); }
.pill-infeasible { background: var(--red-lt);   color: var(--red);   }
.pill-unbounded  { background: var(--amber-lt); color: var(--amber); }

.result-card {
    background: #ffffff;
    border: 1px solid var(--rule-2);
    border-radius: 6px;
    padding: 1.25rem 1.4rem;
    margin-bottom: 1rem;
}
.result-zstar {
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 1.35rem;
    color: var(--ink);
    margin: 0 0 0.2rem;
}
.result-zstar span {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.25rem;
    color: var(--accent);
}
.result-table-wrap { margin-top: 1rem; overflow-x: auto; }
.result-table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.88rem;
}
.result-table th {
    border-bottom: 1.5px solid var(--ink);
    padding: 6px 16px;
    text-align: center;
    font-weight: 600;
    color: var(--ink-2);
    background: var(--paper-2);
}
.result-table td {
    border-bottom: 1px solid var(--rule-2);
    padding: 7px 16px;
    text-align: center;
    color: var(--ink);
}
.result-table tr:last-child td { border-bottom: none; }

/* ── Verbose expander ─────────────────────────────── */
[data-testid="stExpander"] {
    border: 1px solid var(--rule-2) !important;
    border-radius: 4px !important;
    background: #ffffff !important;
}
[data-testid="stExpander"] > div {
    background: #ffffff !important;
}
[data-testid="stExpander"] summary {
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.05em !important;
    color: var(--ink-2) !important;
    background: #ffffff !important;
}
[data-testid="stExpander"] summary:hover {
    background: var(--paper-2) !important;
}
[data-testid="stCodeBlock"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.8rem !important;
}
/* Force LaTeX (MathJax) text to dark color inside expander */
[data-testid="stExpander"] .katex,
[data-testid="stExpander"] .katex *,
[data-testid="stExpander"] mjx-container,
[data-testid="stExpander"] mjx-container * {
    color: #1c1c1e !important;
}
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] {
    background: #ffffff !important;
}
/* General LaTeX text fix */
.katex { color: #1c1c1e !important; }
mjx-container { color: #1c1c1e !important; }

/* ── Sidebar logo / brand ─────────────────────────── */
.sidebar-brand {
    padding: 1.5rem 1rem 1rem;
    margin-bottom: 0.5rem;
}
.sidebar-brand .sb-greek {
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 2.6rem;
    color: rgba(255,255,255,0.25);
    line-height: 1;
    margin-bottom: 0.25rem;
}
.sidebar-brand .sb-name {
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 1.15rem;
    font-weight: 500;
    color: #ffffff;
    letter-spacing: 0.02em;
}
.sidebar-brand .sb-desc {
    font-size: 0.72rem;
    color: rgba(255,255,255,0.45);
    margin-top: 3px;
    letter-spacing: 0.04em;
}

/* ── Info / warning boxes ─────────────────────────── */
.info-box {
    background: var(--accent-lt);
    border-left: 3px solid var(--accent-2);
    border-radius: 0 4px 4px 0;
    padding: 0.65rem 1rem;
    font-size: 0.84rem;
    color: var(--accent);
    margin-bottom: 0.75rem;
}

/* ── Constraint row counter ───────────────────────── */
.con-idx {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: var(--ink-3);
    text-align: center;
    padding-top: 10px;
}

/* ── Streamlit default overrides ──────────────────── */
h1, h2, h3, h4 { color: var(--ink) !important; }
p, li { color: var(--ink-2); }
[data-testid="stMarkdownContainer"] p { color: var(--ink-2); }
.stRadio label p { color: var(--ink-2) !important; }
.stAlert { border-radius: 4px !important; }
div[data-testid="stHorizontalBlock"] { gap: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Backend import
# ─────────────────────────────────────────────────────────────────────────────
try:
    from backend.models import (
        Variable, VariableSign, Constraint, ConstraintType,
        Objective, ObjectiveType, Problem
    )
    from backend.cores import LPSolver, SolverMethod
    from backend.cores.geometry import GraphicalSolver
    BACKEND_OK = True
except ImportError as e:
    BACKEND_OK = False
    BACKEND_ERR = str(e)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def vname(i: int) -> str:
    return f"x{i}"

def fmt_c(c: float) -> str:
    return str(int(c)) if c == int(c) else str(c)


def _latex_expr(coeffs_dict: dict, var_names: list[str]) -> str:
    """Build a LaTeX expression string from coefficients dict, ordered by var_names."""
    terms, first = [], True
    for vn in var_names:
        c = coeffs_dict.get(vn, 0.0)
        if c == 0:
            continue
        idx = var_names.index(vn)
        subscript = str(idx + 1)
        var_tex = f"x_{{{subscript}}}"
        abs_c = abs(c)
        if abs_c == 1:
            coef_str = ""
        else:
            cf = int(abs_c) if abs_c == int(abs_c) else abs_c
            coef_str = str(cf)
        term = f"{coef_str}{var_tex}"
        if first:
            terms.append(f"-{term}" if c < 0 else term)
            first = False
        else:
            terms.append(f"- {term}" if c < 0 else f"+ {term}")
    return " ".join(terms) if terms else "0"


def _preview_problem(obj_label, obj_coeffs, var_names, constraints_raw):
    """Render a clean LaTeX preview of the full LP problem."""
    obj_expr = _latex_expr(
        {var_names[i]: obj_coeffs[i] for i in range(len(var_names))},
        var_names
    )
    ct_tex = {"≤": r"\leq", "≥": r"\geq", "=": "="}

    lines = [rf"\text{{{obj_label}}} \quad z = {obj_expr} \\[4pt]"]
    lines.append(r"\text{s.t.} \quad \begin{cases}")
    for row, ct, rhs in constraints_raw:
        lhs = _latex_expr({var_names[i]: row[i] for i in range(len(var_names))}, var_names)
        r = int(rhs) if rhs == int(rhs) else rhs
        lines.append(rf"  {lhs} {ct_tex[ct]} {r} \\")
    # sign constraints
    nn = ", ".join([f"x_{{{i+1}}}" for i in range(len(var_names))])
    lines.append(rf"  {nn} \geq 0")
    lines.append(r"\end{cases}")
    st.latex("\n".join(lines))


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
def render_sidebar(n: int) -> dict:
    st.sidebar.markdown("""
    <div class="sidebar-brand">
        <div class="sb-greek">∂</div>
        <div class="sb-name">LP Solver</div>
        <div class="sb-desc">Quy hoạch tuyến tính</div>
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    <p style="font-size:0.7rem;letter-spacing:0.1em;text-transform:uppercase;
              color:rgba(255,255,255,0.45);margin:0 0 0.5rem;">Phương pháp giải</p>
    """, unsafe_allow_html=True)

    method_labels = ["Auto", "Simplex", "Đồ thị (Graphical)"]
    method_map = {
        "Auto":                 SolverMethod.AUTO,
        "Simplex":              SolverMethod.SIMPLEX,
        "Đồ thị (Graphical)":  SolverMethod.GRAPHICAL,
    }
    chosen = st.sidebar.selectbox(
        "method", options=method_labels, label_visibility="collapsed"
    )
    method = method_map[chosen]

    if method == SolverMethod.GRAPHICAL and n != 2:
        st.sidebar.markdown(
            '<div style="background:rgba(255,80,80,0.15);border-left:3px solid #ff6b6b;'
            'padding:0.5rem 0.75rem;border-radius:0 4px 4px 0;font-size:0.78rem;'
            'color:#ffb3b3;margin-top:0.5rem;">Đồ thị chỉ áp dụng cho bài toán 2 biến</div>',
            unsafe_allow_html=True
        )

    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    <p style="font-size:0.7rem;letter-spacing:0.1em;text-transform:uppercase;
              color:rgba(255,255,255,0.45);margin:0 0 0.5rem;">Tùy chọn thuật toán</p>
    """, unsafe_allow_html=True)
    bland   = st.sidebar.checkbox("Luật Bland (anti-cycling)", value=False)
    verbose = st.sidebar.checkbox("Hiển thị các bước (verbose)", value=False)

    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    <div style="font-size:0.72rem;color:rgba(255,255,255,0.35);line-height:1.6;padding:0 0.25rem;">
        Hỗ trợ: Simplex, Two-Phase, Đồ thị.<br>
        Biến tự do, ràng buộc hỗn hợp (≤ / ≥ / =),<br>
        bài toán min &amp; max.
    </div>
    """, unsafe_allow_html=True)

    return {"method": method, "bland": bland, "verbose": verbose, "method_label": chosen}


# ─────────────────────────────────────────────────────────────────────────────
# Input sections
# ─────────────────────────────────────────────────────────────────────────────
def section_label(num: str, text: str):
    st.markdown(f"""
    <div class="section-label">
        <span class="sn">{num}</span>{text}
    </div>""", unsafe_allow_html=True)


def render_size_section() -> tuple[int, int]:
    with st.container(border=True):
        section_label("①", "Kích thước bài toán")
        c1, c2, _ = st.columns([1, 1, 4])
        with c1:
            n = st.number_input("Số biến n", min_value=1, max_value=20, value=2, step=1,
                                help="Số lượng biến quyết định (x₁, x₂, ...)")
        with c2:
            m = st.number_input("Số ràng buộc m", min_value=1, max_value=30, value=3, step=1,
                                help="Số lượng ràng buộc (chưa kể điều kiện dấu)")
    return int(n), int(m)


def render_variables_section(n: int) -> list:
    sign_map = {
        "≥ 0": VariableSign.NON_NEGATIVE,
        "≤ 0": VariableSign.NON_POSITIVE,
        "tự do": VariableSign.FREE,
    }
    sign_labels = list(sign_map.keys())

    with st.container(border=True):
        section_label("②", "Điều kiện dấu của biến")
        cols_per_row = min(n, 6)
        rows = [list(range(i, min(i + cols_per_row, n))) for i in range(0, n, cols_per_row)]
        var_signs = []
        for row_indices in rows:
            cols = st.columns(len(row_indices))
            for col, idx in zip(cols, row_indices):
                with col:
                    st.markdown(
                        f'<div class="var-header">x<sub>{idx+1}</sub></div>',
                        unsafe_allow_html=True
                    )
                    lbl = st.selectbox(
                        f"sign_{idx}", options=sign_labels, index=0,
                        key=f"var_sign_{idx}", label_visibility="collapsed"
                    )
                    var_signs.append(sign_map[lbl])
    return var_signs


def render_objective_section(n: int, var_names: list[str]) -> tuple:
    obj_map = {"Min": ObjectiveType.MIN, "Max": ObjectiveType.MAX}

    with st.container(border=True):
        section_label("③", "Hàm mục tiêu")
        obj_label = st.radio(
            "Hướng tối ưu", options=["Min", "Max"],
            horizontal=True, key="obj_type",
            label_visibility="collapsed"
        )
        obj_type = obj_map[obj_label]

        st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)

        cols = st.columns(n)
        coeffs = []
        for i, col in enumerate(cols):
            with col:
                st.markdown(
                    f'<div class="var-header">x<sub>{i+1}</sub></div>',
                    unsafe_allow_html=True
                )
                v = st.number_input(
                    f"c{i}", value=None, placeholder="0", step=1.0,
                    key=f"obj_c_{i}", label_visibility="collapsed"
                )
                coeffs.append(float(v) if v is not None else 0.0)

        # LaTeX preview
        st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
        obj_dict = {var_names[i]: coeffs[i] for i in range(n)}
        expr = _latex_expr(obj_dict, var_names)
        st.markdown('<div class="preview-label">Xem trước</div>', unsafe_allow_html=True)
        st.latex(rf"\{obj_label.lower()} \quad z = {expr}")

    return obj_type, coeffs


def render_constraints_section(n: int, m: int, var_names: list[str]) -> list:
    ct_map = {"≤": ConstraintType.LE, "≥": ConstraintType.GE, "=": ConstraintType.EQ}
    ct_labels = list(ct_map.keys())
    ct_tex = {"≤": r"\leq", "≥": r"\geq", "=": "="}

    with st.container(border=True):
        section_label("④", "Các ràng buộc")

        # Column headers
        header_cols = st.columns([0.35, *([1] * n), 0.7, 1.1])
        header_cols[0].markdown('<div class="con-idx">No.</div>', unsafe_allow_html=True)
        for i in range(n):
            header_cols[i + 1].markdown(
                f'<div class="var-header">x<sub>{i+1}</sub></div>',
                unsafe_allow_html=True
            )
        header_cols[n + 1].markdown('<div class="var-header">Dấu</div>', unsafe_allow_html=True)
        header_cols[n + 2].markdown('<div class="var-header">Vế phải b</div>', unsafe_allow_html=True)

        constraints_raw = []
        for j in range(m):
            row_cols = st.columns([0.35, *([1] * n), 0.7, 1.1])
            row_cols[0].markdown(
                f'<div class="con-idx" style="padding-top:14px">({j+1})</div>',
                unsafe_allow_html=True
            )
            row_coeffs = []
            for i in range(n):
                with row_cols[i + 1]:
                    a = st.number_input(
                        f"a{j}{i}", value=None, placeholder="0", step=1.0,
                        key=f"con_{j}_{i}", label_visibility="collapsed"
                    )
                    row_coeffs.append(float(a) if a is not None else 0.0)
            with row_cols[n + 1]:
                ct_lbl = st.selectbox(
                    f"ct{j}", options=ct_labels, key=f"ct_type_{j}",
                    label_visibility="collapsed"
                )
                ct = ct_map[ct_lbl]
            with row_cols[n + 2]:
                rhs = st.number_input(
                    f"rhs{j}", value=None, placeholder="0", step=1.0,
                    key=f"rhs_{j}", label_visibility="collapsed"
                )
            constraints_raw.append((row_coeffs, ct_lbl, float(rhs) if rhs is not None else 0.0))

        # LaTeX preview of all constraints
        if any(any(r[0]) or r[2] != 0 for r in constraints_raw):
            st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)
            st.markdown('<div class="preview-label">Xem trước hệ ràng buộc</div>', unsafe_allow_html=True)
            lines = []
            for row, ct_l, rhs in constraints_raw:
                lhs = _latex_expr({var_names[i]: row[i] for i in range(n)}, var_names)
                r = int(rhs) if rhs == int(rhs) else rhs
                lines.append(rf"  {lhs} &{ct_tex[ct_l]}& {r}")
            joined_lines = r" \\\\ ".join(lines)
            st.latex(rf"\begin{{array}}{{rcl}} {joined_lines} \end{{array}}")

    return constraints_raw

# ══════════════════════════════════════════════════════════════════════════════
# LATEX EXPORT
# ══════════════════════════════════════════════════════════════════════════════
def _build_objective_latex(obj_type: ObjectiveType, obj_coeffs: list[float], n: int) -> str:
    """Build LaTeX string for objective function."""
    direction = "\\max" if obj_type == ObjectiveType.MAX else "\\min"
    terms = []
    for i, c in enumerate(obj_coeffs):
        if c == 0:
            continue
        v = abs(c); coeff_str = "" if v == 1 else (str(int(v)) if float(v).is_integer() else str(round(v, 3)))
        term = f"{coeff_str}x_{{{i+1}}}"
        terms.append((c, term))
 
    if not terms:
        expr = "0"
    else:
        expr = ("-" if terms[0][0] < 0 else "") + terms[0][1]
        for c, t in terms[1:]:
            expr += f" - {t}" if c < 0 else f" + {t}"
    return f"  {direction} \\quad z &= {expr}"
 
 
def _build_constraints_latex(constraints_raw: list, n: int) -> list[str]:
    """Build LaTeX lines for constraints."""
    lines = []
    for row_coeffs, ct, rhs in constraints_raw:
        terms = []
        for i, c in enumerate(row_coeffs):
            if c == 0:
                continue
            v = abs(c); coeff_str = "" if v == 1 else (str(int(v)) if float(v).is_integer() else str(round(v, 3)))
            term = f"{coeff_str}x_{{{i+1}}}"
            terms.append((c, term))
 
        if not terms:
            expr = "0"
        else:
            expr = ("-" if terms[0][0] < 0 else "") + terms[0][1]
            for c, t in terms[1:]:
                expr += f" - {t}" if c < 0 else f" + {t}"
 
        sign = "\\leq" if ct == ConstraintType.LE else "\\geq" if ct == ConstraintType.GE else "="
        rhs_str = str(int(rhs)) if float(rhs).is_integer() else str(round(rhs, 3))
        lines.append(f"    & {expr} {sign} {rhs_str}")
    return lines
 
 
def _build_variable_signs_latex(var_signs: list[VariableSign], n: int) -> str:
    """Build LaTeX for variable sign conditions."""
    nn = [f"x_{{{i+1}}}" for i, s in enumerate(var_signs) if s == VariableSign.NON_NEGATIVE]
    np_ = [f"x_{{{i+1}}}" for i, s in enumerate(var_signs) if s == VariableSign.NON_POSITIVE]
    fr = [f"x_{{{i+1}}}" for i, s in enumerate(var_signs) if s == VariableSign.FREE]
 
    parts = []
    if nn:
        parts.append(", ".join(nn) + " \\geq 0")
    if np_:
        parts.append(", ".join(np_) + " \\leq 0")
    if fr:
        parts.append(", ".join(fr) + " \\text{ tự do}")
    return " \\quad " + ", \\quad ".join(parts) if parts else ""
 
 
def _parse_verbose_to_latex(verbose_text: str) -> str:
    """
    Convert captured verbose stdout (simplex dictionary steps) into LaTeX.
    Each dictionary block is wrapped in a verbatim environment for readability.
    """
    if not verbose_text.strip():
        return ""
 
    lines = verbose_text.split("\n")
    latex_blocks = []
    current_block = []
 
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("---") or stripped.startswith(">>>"):
            if current_block:
                latex_blocks.append("\n".join(current_block))
                current_block = []
            # Section header
            clean = stripped.replace("---", "").strip()
            if clean:
                latex_blocks.append(f"HEADER:{clean}")
        else:
            current_block.append(line)
 
    if current_block:
        latex_blocks.append("\n".join(current_block))
 
    result_parts = []
    for block in latex_blocks:
        if block.startswith("HEADER:"):
            title = block[7:]
            result_parts.append(f"\n\\subsubsection*{{{_escape_latex(title)}}}\n")
        elif block.strip():
            result_parts.append(
                "\\begin{verbatim}\n" + block + "\n\\end{verbatim}\n"
            )
 
    return "\n".join(result_parts)
 
 
def _escape_latex(text: str) -> str:
    """Escape special LaTeX characters."""
    replacements = [
        ("\\", "\\textbackslash{}"),
        ("&", "\\&"), ("%", "\\%"), ("$", "\\$"),
        ("#", "\\#"), ("_", "\\_"), ("{", "\\{"),
        ("}", "\\}"), ("~", "\\textasciitilde{}"),
        ("^", "\\textasciicircum{}"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text
 
 
def generate_latex_document(
    n: int,
    var_signs: list,
    obj_type: ObjectiveType,
    obj_coeffs: list[float],
    constraints_raw: list,
    result: dict,
    verbose_text: str,
    method_label: str,
) -> str:
    """
    Generate a complete LaTeX document with:
    - Problem formulation
    - Solution steps (from verbose output)
    - Optimal solution
    """
    obj_line = _build_objective_latex(obj_type, obj_coeffs, n)
    constraint_lines = _build_constraints_latex(constraints_raw, n)
    sign_line = _build_variable_signs_latex(var_signs, n)
 
    constraints_tex = " \\\\\n".join(constraint_lines)
    if sign_line:
        constraints_tex += " \\\\\n    & " + sign_line.strip()
 
    status = result.get("status", "UNKNOWN")
    status_vn = {
        "OPTIMAL": "Tối ưu (Optimal)",
        "INFEASIBLE": "Vô nghiệm (Infeasible)",
        "UNBOUNDED": "Không bị chặn (Unbounded)",
    }.get(status, status)
 
    # Build result section
    result_tex = ""
    if status == "OPTIMAL":
        opt_val = result.get("optimal_value", "N/A")
        solution = result.get("solution", {})
        sol_items = ", \\quad ".join([f"x_{{{k[1:]}}} = {v}" if k.startswith("x") else f"{_escape_latex(k)} = {v}"
                                      for k, v in solution.items()])
        result_tex = f"""
\\subsection*{{Nghiệm tối ưu}}
 
Giá trị tối ưu:
\\[
  z^* = {opt_val}
\\]
 
Nghiệm:
\\[
  {sol_items}
\\]
"""
    elif status == "INFEASIBLE":
        result_tex = "\n\\subsection*{Kết quả}\nBài toán vô nghiệm — miền chấp nhận được rỗng.\n"
    elif status == "UNBOUNDED":
        result_tex = "\n\\subsection*{Kết quả}\nHàm mục tiêu không bị chặn — bài toán không có nghiệm hữu hạn.\n"
 
    # Build steps section from verbose output
    steps_tex = ""
    parsed_steps = _parse_verbose_to_latex(verbose_text)
    if parsed_steps:
        steps_tex = f"""
\\subsection*{{Các bước giải chi tiết}}
 
{parsed_steps}
"""
    else:
        steps_tex = """
\\subsection*{Các bước giải chi tiết}
 
\\textit{Bật tùy chọn "Hiển thị các bước chi tiết" (Verbose) trên giao diện để xem từng bước của thuật toán.}
"""
 
    doc = rf"""\documentclass[12pt, a4paper]{{article}}
 
% ── Packages ──────────────────────────────────────────────────────────────
\usepackage[utf8]{{inputenc}}
\usepackage[T5]{{fontenc}}
\usepackage[vietnamese]{{babel}}
\usepackage{{amsmath, amssymb}}
\usepackage{{geometry}}
\usepackage{{booktabs}}
\usepackage{{xcolor}}
\usepackage{{fancyhdr}}
\usepackage{{titlesec}}
\usepackage{{parskip}}
 
\geometry{{margin=2.5cm}}
 
% ── Header / Footer ───────────────────────────────────────────────────────
\pagestyle{{fancy}}
\fancyhf{{}}
\rhead{{LP Solver}}
\lhead{{Quy hoạch tuyến tính}}
\cfoot{{\thepage}}
 
% ── Title style ───────────────────────────────────────────────────────────
\titleformat{{\section}}{{\large\bfseries\color{{blue!60!black}}}}{{}}{{0em}}{{}}[\titlerule]
 
\begin{{document}}
 
% ── Title ─────────────────────────────────────────────────────────────────
\begin{{center}}
  {{\Large\bfseries Bài toán Quy hoạch Tuyến tính}} \\[6pt]
  {{\normalsize Phương pháp: {method_label}}} \\[4pt]
  {{\small\color{{gray}} Trạng thái: {status_vn}}}
\end{{center}}
 
\vspace{{1em}}
\hrule
\vspace{{1.5em}}
 
% ── Problem Formulation ───────────────────────────────────────────────────
\section*{{Đề bài}}
 
\begin{{alignat*}}{{2}}
{obj_line} \\
  \text{{s.t.}} \quad
{constraints_tex}
\end{{alignat*}}
 
% ── Steps ─────────────────────────────────────────────────────────────────
\section*{{Lời giải}}
{steps_tex}
 
% ── Result ────────────────────────────────────────────────────────────────
\section*{{Kết quả}}
{result_tex}
 
\end{{document}}
"""
    return doc
# ─────────────────────────────────────────────────────────────────────────────
# Problem builder & solver
# ─────────────────────────────────────────────────────────────────────────────
def build_problem(n, var_signs, obj_type, obj_coeffs, constraints_raw) -> "Problem":
    variables = [Variable(name=vname(i + 1), sign=var_signs[i]) for i in range(n)]
    obj_dict  = {vname(i + 1): obj_coeffs[i] for i in range(n)}
    objective = Objective(objective_type=obj_type, coeffs=obj_dict)

    constraints = []
    ct_map2 = {"≤": ConstraintType.LE, "≥": ConstraintType.GE, "=": ConstraintType.EQ}
    for row_coeffs, ct_lbl, rhs in constraints_raw:
        c_dict = {vname(i + 1): row_coeffs[i] for i in range(n)}
        constraints.append(Constraint(coeffs=c_dict, constraint_type=ct_map2[ct_lbl], right_hand_side=rhs))

    return Problem(objective=objective, constraints=constraints, variables=variables)


def solve_problem(problem, settings) -> tuple[dict, str]:
    solver = LPSolver(
        problem=problem,
        method=settings["method"],
        bland=settings["bland"],
        verbose=settings["verbose"]
    )
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        result = solver.solve()
    return result, buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# Result rendering
# ─────────────────────────────────────────────────────────────────────────────
def render_result(result, captured_stdout, problem, settings,
                  n, var_signs, obj_type, obj_coeffs, constraints_raw):
    st.markdown("---")
    st.markdown("## 📊 Kết quả")
    status = result.get("status", "UNKNOWN")

    # ── Status badge ──────────────────────────────────────────────────────────
    if status == "OPTIMAL":
        st.success("✅ TỐI ƯU (OPTIMAL)")
    elif status == "INFEASIBLE":
        st.error("❌ VÔ NGHIỆM (INFEASIBLE)")
    elif status == "UNBOUNDED":
        st.warning("∞ KHÔNG BỊ CHẶN (UNBOUNDED)")
    else:
        st.info(f"Trạng thái: {status}")

    # ── Optimal result ────────────────────────────────────────────────────────
    if status == "OPTIMAL":
        opt_val = result.get("optimal_value", "N/A")
        solution = result.get("solution", {})
        col_val, col_sol = st.columns([1, 2])
        with col_val:
            st.markdown("**Giá trị tối ưu**")
            st.latex(rf"z^* = {opt_val}")
        with col_sol:
            if solution:
                st.markdown("**NGHIỆM TỐI ƯU**")
                headers = " ".join(f"<th>{k}</th>" for k in solution)
                values = " ".join(f"<td>{v}</td>" for v in solution.values())
                st.markdown(
                    f'<table class="sol-table"><thead><tr>{headers}</tr></thead>'
                    f'<tbody><tr>{values}</tr></tbody></table>',
                    unsafe_allow_html=True,
                )
                st.latex(r",\quad ".join([f"{k} = {v}" for k, v in solution.items()]))
    elif status == "INFEASIBLE":
        st.info("Bài toán không có miền chấp nhận được (vô nghiệm).")
    elif status == "UNBOUNDED":
        st.info("Hàm mục tiêu không bị chặn — bài toán không có nghiệm hữu hạn.")

    # ── Full problem LaTeX preview ─────────────────────────────────────────────
    with st.expander("📄 Xem toàn bộ bài toán (LaTeX)"):
        obj_line = _build_objective_latex(obj_type, obj_coeffs, n)
        constraint_lines = _build_constraints_latex(constraints_raw, n)
        sign_line = _build_variable_signs_latex(var_signs, n)
        constraints_tex = " \\\\\n".join(constraint_lines)
        sign_part = rf"\\ & {sign_line.strip()}" if sign_line else ""
        full_latex = (
            rf"\begin{{alignat*}}{{2}}"
            + "\n" + obj_line + r" \\"
            + "\n" + r"  \text{s.t.} \quad"
            + "\n" + constraints_tex
            + "\n" + sign_part
            + "\n" + r"\end{alignat*}"
        )
        st.latex(full_latex)

    # ── Verbose steps ─────────────────────────────────────────────────────────
    if settings["verbose"] and captured_stdout.strip():
        with st.expander("📋 Xem các bước chạy chi tiết (Verbose)"):
            st.code(captured_stdout, language="text")

    # ── Graph (Graphical method) ───────────────────────────────────────────────
    if settings["method"] == SolverMethod.GRAPHICAL and status == "OPTIMAL":
        st.markdown("### 📈 Đồ thị vùng khả thi")
        try:
            fig = GraphicalSolver(problem, verbose=False).plot_feasible_region(result)
            if fig is not None:
                st.pyplot(fig)
        except Exception as e:
            st.error(f"Lỗi khi vẽ đồ thị: {e}")

    # ── LaTeX Export ──────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📥 Xuất file LaTeX")

    # Nếu verbose chưa bật, chạy lại với verbose=True để lấy steps
    if not captured_stdout.strip():
        try:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                LPSolver(problem=problem, method=settings["method"],
                         bland=settings["bland"], verbose=True).solve()
            verbose_for_export = buf.getvalue()
        except Exception:
            verbose_for_export = ""
    else:
        verbose_for_export = captured_stdout

    latex_doc = generate_latex_document(
        n=n, var_signs=var_signs, obj_type=obj_type, obj_coeffs=obj_coeffs,
        constraints_raw=constraints_raw, result=result,
        verbose_text=verbose_for_export, method_label=settings["method_label"],
    )
    st.download_button(
        label="⬇️ Tải file .tex",
        data=latex_doc.encode("utf-8"),
        file_name="lp_solution.tex",
        mime="text/plain",
        type="primary",
    )
    with st.expander("👁 Xem nội dung file .tex"):
        st.code(latex_doc, language="latex")

# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main():
    # Masthead
    st.markdown("""
    <div class="lp-masthead">
        <h1 class="lp-title">LP Solver</h1>
        <p class="lp-subtitle">Quy hoạch tuyến tính &mdash; Linear Programming Solver</p>
    </div>
    """, unsafe_allow_html=True)

    if not BACKEND_OK:
        st.error(f"Lỗi kết nối backend: `{BACKEND_ERR}`")
        return

    # ① Size
    n, m = render_size_section()
    var_names = [vname(i + 1) for i in range(n)]

    # Sidebar (needs n for validation)
    settings = render_sidebar(n)

    # ② Variables
    var_signs = render_variables_section(n)

    # ③ Objective
    obj_type, obj_coeffs = render_objective_section(n, var_names)

    # ④ Constraints
    constraints_raw = render_constraints_section(n, m, var_names)

    # ─── Full-problem preview ──────────────────────────────────────────────
    with st.expander("Xem toàn bộ bài toán (LaTeX)", expanded=False):
        obj_label = "Max" if obj_type == ObjectiveType.MAX else "Min"
        obj_dict = {var_names[i]: obj_coeffs[i] for i in range(n)}
        obj_expr = _latex_expr(obj_dict, var_names)
        ct_tex = {"≤": r"\leq", "≥": r"\geq", "=": "="}

        constraint_lines = []
        for row, ct_l, rhs in constraints_raw:
            lhs = _latex_expr({var_names[i]: row[i] for i in range(n)}, var_names)
            r = int(rhs) if rhs == int(rhs) else rhs
            constraint_lines.append(rf"    {lhs} & {ct_tex[ct_l]} & {r}")

        sign_parts = []
        for i, sg in enumerate(var_signs):
            vn = f"x_{{{i+1}}}"
            if sg == VariableSign.NON_NEGATIVE:
                sign_parts.append(f"{vn} \\geq 0")
            elif sg == VariableSign.NON_POSITIVE:
                sign_parts.append(f"{vn} \\leq 0")
            else:
                sign_parts.append(f"{vn} \\text{{ tự do}}")
        sign_line = ", \\quad ".join(sign_parts)

        all_lines = constraint_lines + [rf"    {sign_line}"]
        body = " \\\\\n".join(all_lines)

        full_tex = (
            rf"\{obj_label.lower()} \quad z = {obj_expr} \\"
            rf"\text{{s.t.}} \quad \begin{{array}}{{rcl}}"
            + "\n" + body + "\n"
            + r"\end{array}"
        )
        st.latex(full_tex)

    st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)

    # ─── Solve button ──────────────────────────────────────────────────────
    col_btn, _ = st.columns([1, 5])
    with col_btn:
        solve_clicked = st.button("Giải bài toán", type="primary", use_container_width=True)

    if solve_clicked:
        if settings["method"] == SolverMethod.GRAPHICAL and n != 2:
            st.error(f"Phương pháp đồ thị yêu cầu đúng 2 biến (hiện có {n}).")
            return

        with st.spinner("Đang giải..."):
            try:
                problem = build_problem(n, var_signs, obj_type, obj_coeffs, constraints_raw)
                result, captured = solve_problem(problem, settings)
                render_result(result, captured, problem, settings,
                  n, var_signs, obj_type, obj_coeffs, constraints_raw)

            except Exception as e:
                st.error(f"Lỗi: {e}")
                import traceback
                with st.expander("Chi tiết lỗi"):
                    st.code(traceback.format_exc())


if __name__ == "__main__":
    main()
