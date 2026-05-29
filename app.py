# To deploy backend to sever

"""
app.py — Giao diện Web cho Hệ thống Giải Quy hoạch Tuyến tính (LP Solver)
Chạy bằng lệnh: streamlit run app.py
"""

import io
import contextlib
import streamlit as st

# ──────────────────────────────────────────────────────────────────────────────
# Cấu hình trang (phải là lệnh Streamlit đầu tiên)
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="LP Solver",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# CSS tùy chỉnh — Light Theme rõ ràng, học thuật
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Nền & font chính */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #f7f9fc;
        font-family: 'Source Serif 4', 'Georgia', serif;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #1a2744;
        color: #e8edf5;
    }
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stCheckbox span,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #e8edf5 !important;
    }

    /* Tiêu đề chính */
    h1 {
        color: #1a2744;
        font-size: 2rem;
        letter-spacing: -0.5px;
        border-bottom: 3px solid #3a6bc4;
        padding-bottom: 0.4rem;
        margin-bottom: 1.5rem;
    }
    h2, h3, h4 { color: #1a2744; }
    h4 {
        border-left: 4px solid #3a6bc4;
        padding-left: 0.6rem;
        margin-bottom: 1rem;
    }

    /* Nút Solve */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #1a2744 0%, #3a6bc4 100%);
        color: #ffffff;
        border: none;
        border-radius: 8px;
        font-size: 1.05rem;
        font-weight: 700;
        padding: 0.55rem 2.5rem;
        letter-spacing: 0.5px;
        transition: opacity 0.2s;
    }
    div.stButton > button[kind="primary"]:hover { opacity: 0.88; }

    /* Kết quả */
    .result-box {
        background: #eef4ff;
        border: 1px solid #3a6bc4;
        border-radius: 10px;
        padding: 1.2rem 1.6rem;
        margin-top: 1rem;
    }
    .result-status-OPTIMAL    { color: #1a7a4a; font-weight: 800; font-size: 1.1rem; }
    .result-status-INFEASIBLE { color: #c0392b; font-weight: 800; font-size: 1.1rem; }
    .result-status-UNBOUNDED  { color: #e67e22; font-weight: 800; font-size: 1.1rem; }

    /* Bảng nghiệm */
    .sol-table { width: 100%; border-collapse: collapse; margin-top: 0.6rem; }
    .sol-table th { background: #1a2744; color: #fff; padding: 6px 12px; text-align: center; }
    .sol-table td { border: 1px solid #c5d0e0; padding: 5px 12px; text-align: center; }
    .sol-table tr:nth-child(even) td { background: #f0f4fb; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────────────────────
# Import backend (sau khi page config)
# ──────────────────────────────────────────────────────────────────────────────
try:
    from backend.models import Variable, VariableSign, Constraint, ConstraintType, Objective, ObjectiveType, Problem
    from backend.cores import LPSolver, SolverMethod
    from backend.cores.geometry import GraphicalSolver
    BACKEND_OK = True
except ImportError as e:
    BACKEND_OK = False
    BACKEND_ERR = str(e)


def var_name(i: int) -> str:
    """Trả về tên biến dạng chuỗi x1, x2, ..."""
    return f"x{i}"


def _fmt_coeff(c: float) -> str:
    """Định dạng hệ số: bỏ .0 nếu là số nguyên."""
    if c == int(c):
        return str(int(c))
    return str(c)


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
def render_sidebar(n: int) -> dict:
    st.sidebar.markdown("## ⚙️ Cài đặt thuật toán")

    method_labels = ["Auto", "Simplex", "Graphical"]
    method_map = {
        "Auto":      SolverMethod.AUTO,
        "Simplex":   SolverMethod.SIMPLEX,
        "Graphical": SolverMethod.GRAPHICAL,
    }
    chosen_label = st.sidebar.selectbox(
        "Phương pháp giải",
        options=method_labels,
        help="Auto: tự chọn giữa Simplex và Two-Phase tùy cấu trúc bài toán.",
    )
    method = method_map[chosen_label]

    if method == SolverMethod.GRAPHICAL and n != 2:
        st.sidebar.error("⚠️ Đồ thị chỉ áp dụng cho bài toán đúng 2 biến.")

    st.sidebar.markdown("---")
    bland   = st.sidebar.checkbox("Sử dụng luật Bland", value=False)
    verbose = st.sidebar.checkbox("Hiển thị các bước chi tiết", value=False)
    st.sidebar.markdown("---")
    st.sidebar.info("💡 Mẹo: Dùng phím **Tab** để chuyển nhanh giữa các ô nhập liệu.")

    return {"method": method, "bland": bland, "verbose": verbose, "method_label": chosen_label}


# ══════════════════════════════════════════════════════════════════════════════
# GIAO DIỆN NHẬP LIỆU
# ══════════════════════════════════════════════════════════════════════════════
def render_size_section() -> tuple[int, int]:
    with st.container(border=True):
        st.markdown("#### ① Kích thước bài toán")
        c1, c2, _ = st.columns([1, 1, 3])
        with c1:
            n = st.number_input("Số biến ($n$)", min_value=1, max_value=20, value=2, step=1)
        with c2:
            m = st.number_input("Số ràng buộc ($m$)", min_value=1, max_value=30, value=3, step=1)
    return int(n), int(m)


def render_variables_section(n: int) -> list[VariableSign]:
    sign_label_map = {
        "≥ 0  (không âm)":   VariableSign.NON_NEGATIVE,
        "≤ 0  (không dương)": VariableSign.NON_POSITIVE,
        "Tự do":              VariableSign.FREE,
    }
    sign_labels = list(sign_label_map.keys())

    with st.container(border=True):
        st.markdown("#### ② Điều kiện dấu của biến")
        cols_per_row = min(n, 5)
        rows = [list(range(i, min(i + cols_per_row, n))) for i in range(0, n, cols_per_row)]
        var_signs = []
        for row_indices in rows:
            cols = st.columns(len(row_indices))
            for col, idx in zip(cols, row_indices):
                with col:
                    label = st.selectbox(
                        f"$x_{{{idx + 1}}}$", options=sign_labels, index=0, key=f"var_sign_{idx}"
                    )
                    var_signs.append(sign_label_map[label])
    return var_signs


def render_objective_section(n: int) -> tuple[ObjectiveType, list[float]]:
    obj_map = {"Min": ObjectiveType.MIN, "Max": ObjectiveType.MAX}

    with st.container(border=True):
        st.markdown("#### ③ Hàm mục tiêu")
        obj_type_label = st.radio("Hướng tối ưu", options=["Min", "Max"], horizontal=True, key="obj_type")
        obj_type = obj_map[obj_type_label]

        st.markdown(f"**Hệ số hàm mục tiêu** &nbsp; ({obj_type_label} $z$)")
        cols = st.columns(n)
        coeffs = []
        for i, col in enumerate(cols):
            with col:
                st.markdown(f"<center>$x_{{{i + 1}}}$</center>", unsafe_allow_html=True)
                c_val = st.number_input(
                    label=f"c{i+1}",
                    value=None,          # Để ô trống
                    placeholder="0",     # Gợi ý số 0
                    step=1.0,            # Bước nhảy là 1 (+/-)
                    key=f"obj_c_{i}",
                    label_visibility="collapsed",
                )
                coeffs.append(float(c_val) if c_val is not None else 0.0)

        st.divider()
        _preview_objective(obj_type_label, coeffs, n)
        
    return obj_type, coeffs


def render_constraints_section(n: int, m: int) -> list[tuple[list[float], ConstraintType, float]]:
    ct_map = {"≤": ConstraintType.LE, "≥": ConstraintType.GE, "=": ConstraintType.EQ}
    ct_labels = list(ct_map.keys())

    with st.container(border=True):
        st.markdown("#### ④ Các ràng buộc")
        
        # Header
        header_cols = st.columns([*([1] * n), 0.8, 1.2])
        for i in range(n):
            header_cols[i].markdown(f"<center>$x_{{{i+1}}}$</center>", unsafe_allow_html=True)
        header_cols[n].markdown("<center>Dấu</center>", unsafe_allow_html=True)
        header_cols[n + 1].markdown("<center>Vế phải ($b$)</center>", unsafe_allow_html=True)
        
        constraints_raw = []
        for j in range(m):
            row_cols = st.columns([*([1] * n), 0.8, 1.2])
            row_coeffs = []
            for i in range(n):
                with row_cols[i]:
                    a_val = st.number_input(
                        label=f"a{j+1}{i+1}", value=None, placeholder="0", step=1.0, 
                        key=f"con_{j}_{i}", label_visibility="collapsed",
                    )
                    row_coeffs.append(float(a_val) if a_val is not None else 0.0)
            
            with row_cols[n]:
                ct_label = st.selectbox(
                    label=f"ct_type_{j}", options=ct_labels, key=f"ct_type_{j}", label_visibility="collapsed",
                )
                ct = ct_map[ct_label]
            
            with row_cols[n + 1]:
                rhs_val = st.number_input(
                    label=f"rhs_{j}", value=None, placeholder="0", step=1.0, 
                    key=f"rhs_{j}", label_visibility="collapsed",
                )
            constraints_raw.append((row_coeffs, ct, float(rhs_val) if rhs_val is not None else 0.0))

        st.divider()
        _preview_constraints(constraints_raw, n)

    return constraints_raw


# ══════════════════════════════════════════════════════════════════════════════
# PREVIEW LATEX HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def _preview_objective(obj_label: str, coeffs: list[float], n: int):
    terms = []
    for i, c in enumerate(coeffs):
        if c == 0: continue
        term = f"x_{{{i+1}}}" if c == 1 else f"-x_{{{i+1}}}" if c == -1 else f"{_fmt_coeff(c)}x_{{{i+1}}}"
        terms.append(term)

    if not terms:
        expr = "0"
    else:
        expr = terms[0]
        for t in terms[1:]:
            expr += f" - {t[1:]}" if t.startswith("-") else f" + {t}"
    st.latex(rf"\text{{{obj_label}}} \quad z = {expr}")


def _preview_constraints(constraints_raw: list, n: int):
    latex_lines = []
    for row_coeffs, ct, rhs in constraints_raw:
        terms = []
        for i, c in enumerate(row_coeffs):
            if c == 0: continue
            term = f"x_{{{i+1}}}" if c == 1 else f"-x_{{{i+1}}}" if c == -1 else f"{_fmt_coeff(c)}x_{{{i+1}}}"
            terms.append(term)
            
        if not terms:
            expr = "0"
        else:
            expr = terms[0]
            for t in terms[1:]:
                expr += f" - {t[1:]}" if t.startswith("-") else f" + {t}"
        
        ct_symbol = "\\le" if ct == ConstraintType.LE else "\\ge" if ct == ConstraintType.GE else "="
        latex_lines.append(rf"{expr} & {ct_symbol} & {_fmt_coeff(rhs)}")
        
    if latex_lines:
        joined_lines = r" \\ ".join(latex_lines)
        st.latex(rf"\begin{{align*}} {joined_lines} \end{{align*}}")
    else:
        st.info("Chưa có ràng buộc nào.")


# ══════════════════════════════════════════════════════════════════════════════
# CORE LOGIC
# ══════════════════════════════════════════════════════════════════════════════
def build_problem(n, var_signs, obj_type, obj_coeffs, constraints_raw) -> "Problem":
    variables = [Variable(name=var_name(i + 1), sign=var_signs[i]) for i in range(n)]
    obj_coeffs_dict = {var_name(i + 1): obj_coeffs[i] for i in range(n)}
    objective = Objective(objective_type=obj_type, coeffs=obj_coeffs_dict)

    constraints = []
    for row_coeffs, ct, rhs in constraints_raw:
        c_dict = {var_name(i + 1): row_coeffs[i] for i in range(n)}
        constraints.append(Constraint(coeffs=c_dict, constraint_type=ct, right_hand_side=rhs))

    return Problem(objective=objective, constraints=constraints, variables=variables)


def solve_problem(problem: "Problem", settings: dict) -> tuple[dict, str]:
    solver = LPSolver(problem=problem, method=settings["method"], bland=settings["bland"], verbose=settings["verbose"])
    stdout_buffer = io.StringIO()
    with contextlib.redirect_stdout(stdout_buffer):
        result = solver.solve()
    return result, stdout_buffer.getvalue()


def render_result(result, captured_stdout, problem, settings):
    st.markdown("---")
    st.markdown("## 📊 Kết quả")
    status = result.get("status", "UNKNOWN")

    st.markdown('<div class="result-box">', unsafe_allow_html=True)
    status_class = {"OPTIMAL": "result-status-OPTIMAL", "INFEASIBLE": "result-status-INFEASIBLE", "UNBOUNDED": "result-status-UNBOUNDED"}.get(status, "result-status-OPTIMAL")
    status_vn = {"OPTIMAL": "✅ TỐI ƯU (OPTIMAL)", "INFEASIBLE": "❌ VÔ NGHIỆM (INFEASIBLE)", "UNBOUNDED": "∞ KHÔNG BỊ CHẶN (UNBOUNDED)"}.get(status, status)

    st.markdown(f'<p class="{status_class}">{status_vn}</p>', unsafe_allow_html=True)

    if status == "OPTIMAL":
        st.markdown(f"**Giá trị tối ưu:** &nbsp; $z^* = {result.get('optimal_value', 'N/A')}$")
        solution = result.get("solution", {})
        if solution:
            st.markdown("**Nghiệm tối ưu:**")
            headers = " ".join(f"<th>{k}</th>" for k in solution)
            values  = " ".join(f"<td>{v}</td>" for v in solution.values())
            st.markdown(f'<table class="sol-table"><thead><tr>{headers}</tr></thead><tbody><tr>{values}</tr></tbody></table>', unsafe_allow_html=True)
            st.latex(r",\quad ".join([f"{k} = {v}" for k, v in solution.items()]))
    elif status == "INFEASIBLE":
        st.info("Bài toán không có miền chấp nhận được (vô nghiệm).")
    elif status == "UNBOUNDED":
        st.info("Hàm mục tiêu không bị chặn — bài toán không có nghiệm hữu hạn.")
    st.markdown("</div>", unsafe_allow_html=True)

    if settings["verbose"] and captured_stdout.strip():
        with st.expander("📋 Xem các bước chạy chi tiết (Verbose)"):
            st.code(captured_stdout, language="text")

    if settings["method"] == SolverMethod.GRAPHICAL and status == "OPTIMAL":
        st.markdown("### 📈 Đồ thị vùng khả thi")
        try:
            fig = GraphicalSolver(problem, verbose=False).plot_feasible_region(result)
            if fig is not None:
                st.pyplot(fig)
            else:
                st.warning("Hàm `plot_feasible_region` chưa được sửa để `return fig`.")
        except Exception as e:
            st.error(f"Lỗi khi vẽ đồ thị: {e}")


def main():
    st.markdown("<h1>📐 Linear Programming Solver</h1>", unsafe_allow_html=True)
    st.markdown("Nhập bài toán Quy hoạch Tuyến tính theo từng bước, sau đó nhấn **Solve** để xem kết quả.")

    if not BACKEND_OK:
        st.error(f"⚠️ Lỗi kết nối backend: `{BACKEND_ERR}`")
        return

    n, m = render_size_section()
    settings = render_sidebar(n)
    var_signs = render_variables_section(n)
    obj_type, obj_coeffs = render_objective_section(n)
    constraints_raw = render_constraints_section(n, m)

    col_btn, _ = st.columns([1, 4])
    with col_btn:
        solve_clicked = st.button("🚀 Solve", type="primary", use_container_width=True)

    if solve_clicked:
        if settings["method"] == SolverMethod.GRAPHICAL and n != 2:
            st.error(f"❌ Phương pháp đồ thị yêu cầu **đúng 2 biến** (bài toán hiện có {n}).")
            return
        with st.spinner("Đang giải bài toán..."):
            try:
                problem = build_problem(n, var_signs, obj_type, obj_coeffs, constraints_raw)
                result, captured = solve_problem(problem, settings)
                render_result(result, captured, problem, settings)
            except Exception as e:
                st.error(f"❌ Có lỗi xảy ra: {e}")


if __name__ == "__main__":
    main()