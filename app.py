from flask import Flask, render_template, request, send_file
from sympy import symbols, Eq, solve, sympify, latex, expand, factor, Poly, nsimplify
from sympy.core.expr import Expr
import matplotlib.pyplot as plt
import numpy as np
import io
import re

app = Flask(__name__)

# Auto-correct and support √x notation and implicit multiplication
def preprocess_expression(expr):
    expr = expr.replace('√', 'sqrt')                    # √ → sqrt
    expr = re.sub(r'(\d)([a-zA-Z\(])', r'\1*\2', expr)  # 2x → 2*x
    expr = re.sub(r'(\))(\w)', r'\1*\2', expr)          # )x → )*x
    expr = re.sub(r'(\d)(sqrt)', r'\1*sqrt', expr)      # 2sqrt → 2*sqrt
    expr = re.sub(r'sqrt(\d+)', r'sqrt(\1)', expr)      # sqrt3 → sqrt(3)
    return expr

@app.route('/', methods=['GET', 'POST'])
def index():
    steps = ''
    expression = ''
    if request.method == 'POST':
        expression = request.form['equation']
        try:
            exprs = [preprocess_expression(e.strip()) for e in expression.split(',')]
            equations = []
            all_symbols = set()

            for e in exprs:
                if '=' in e:
                    lhs, rhs = e.split('=', 1)
                    lhs_expr, rhs_expr = sympify(lhs), sympify(rhs)
                    eq = Eq(lhs_expr, rhs_expr)
                else:
                    lhs_expr, rhs_expr = sympify(e), 0
                    eq = Eq(lhs_expr, rhs_expr)

                if isinstance(lhs_expr, Expr):
                    all_symbols.update(lhs_expr.free_symbols)
                if isinstance(rhs_expr, Expr):
                    all_symbols.update(rhs_expr.free_symbols)

                equations.append(eq)

            steps += "<h3>Step 1: Given Equation(s)</h3>"
            for eq in equations:
                steps += rf"<div>\[{latex(eq)}\]</div>"

            if len(equations) == 1 and len(all_symbols) == 1:
                var = next(iter(all_symbols))
                combined = equations[0].lhs - equations[0].rhs
                expanded = expand(combined)
                factored = factor(expanded)

                steps += "<h3>Step 2: Simplify & Factor</h3>"
                steps += rf"<div>\[{latex(combined)} = 0 \Rightarrow {latex(expanded)} = 0\]</div>"
                if factored != expanded:
                    steps += rf"<div>\[{latex(expanded)} = {latex(factored)}\]</div>"

                steps += "<h3>Step 3: Solve (Symbolic Roots)</h3>"
                sols = solve(Eq(factored, 0), var)
                for s in sols:
                    simp = nsimplify(s, rational=True)
                    if simp == int(simp):
                        steps += rf"<div>\[{latex(var)} = {int(simp)}\]</div>"
                    else:
                        steps += rf"<div>\[{latex(var)} = {latex(simp)}\]</div>"

                poly = Poly(expanded, var)
                num_roots = poly.nroots()
                steps += "<h3>Numeric Roots</h3>"
                for r in num_roots:
                    r = complex(r)
                    if abs(r.imag) < 1e-8:
                        steps += rf"<div>\[x \approx {r.real:.5f}\]</div>"
                    else:
                        sign = '+' if r.imag >= 0 else '-'
                        steps += rf"<div>\[x \approx {r.real:.5f} {sign} {abs(r.imag):.5f}i\]</div>"

            else:
                steps += "<h3>Step 2: Solving System of Equations</h3>"
                sol = solve(equations)
                if isinstance(sol, list):
                    for soln in sol:
                        for var, val in soln.items():
                            simp = nsimplify(val, rational=True)
                            steps += rf"<div>\[{latex(var)} = {latex(simp)}\]</div>"
                elif isinstance(sol, dict):
                    for var, val in sol.items():
                        simp = nsimplify(val, rational=True)
                        steps += rf"<div>\[{latex(var)} = {latex(simp)}\]</div>"
                else:
                    steps += f"<div>Solution: {sol}</div>"

        except Exception as e:
            steps = f"<div style='color:red'>Error: {e}</div>"

    return render_template('index.html', result=steps, expression=expression)

@app.route('/graph', methods=['POST'])
def graph():
    expr = request.form.get('expression', '')
    expr_proc = preprocess_expression(expr)
    y_expr = sympify(expr_proc)
    expr_latex = latex(y_expr)

    x = symbols('x')
    sols = solve(Eq(y_expr, 0), x)
    exact_roots = []

    for r in sols:
        if getattr(r, 'is_real', True):
            simp = nsimplify(r, rational=True)
            if simp == int(simp):
                exact_roots.append(rf"\[x = {int(simp)}\]")
            else:
                exact_roots.append(rf"\[x = {latex(simp)}\]")

    return render_template('graph.html',
                           expression=expr,
                           expression_latex=expr_latex,
                           exact_roots=exact_roots)

@app.route('/plot.png')
def plot_png():
    expr = request.args.get('expr', '')
    expr_proc = preprocess_expression(expr)
    y_expr = sympify(expr_proc)
    x = symbols('x')

    xs = np.linspace(-10, 10, 400)
    if y_expr.free_symbols:
        f = lambda v: float(y_expr.evalf(subs={x: v}))
        ys = [f(v) for v in xs]
    else:
        ys = [float(y_expr)] * len(xs)

    plt.figure(figsize=(6, 4))
    plt.plot(xs, ys, label=rf"$y = {latex(y_expr)}$")
    plt.axhline(0, color='black', lw=0.5)
    plt.axvline(0, color='black', lw=0.5)
    plt.grid(True)
    plt.legend()

    # Plot real roots as red dots
    sols = solve(Eq(y_expr, 0), x)
    for r in sols:
        if getattr(r, 'is_real', True):
            plt.plot(float(r.evalf()), 0, 'ro')

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

if __name__ == '__main__':
    import matplotlib
    matplotlib.use('Agg')  # Disable GUI backend
    app.run(host='0.0.0.0', port=10000, debug=True)
