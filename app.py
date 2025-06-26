from flask import Flask, render_template, request, send_file
from sympy import symbols, Eq, solve, sympify, latex, expand, factor, Poly, simplify
import matplotlib.pyplot as plt
import numpy as np
import io
import re

app = Flask(__name__)

def preprocess_expression(expr):
    expr = expr.replace('√', 'sqrt')
    expr = re.sub(r'(\d)([a-zA-Z\(])', r'\1*\2', expr)
    expr = re.sub(r'(\))(\w)', r'\1*\2', expr)
    expr = re.sub(r'(\d)(sqrt)', r'\1*sqrt', expr)
    expr = re.sub(r'sqrt(\d+)', r'sqrt(\1)', expr)
    return expr

@app.route('/', methods=['GET', 'POST'])
def index():
    steps = ''
    expression = ''
    show_decimal = False

    if request.method == 'POST':
        expression = request.form['equation']
        show_decimal = 'show_decimal' in request.form

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

                all_symbols.update(getattr(lhs_expr, 'free_symbols', set()))
                all_symbols.update(getattr(rhs_expr, 'free_symbols', set()))
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

                poly = Poly(expanded, var)
                degree = poly.degree()

                if degree == 2:
                    steps += "<h3>Step 3: Quadratic Formula Steps</h3>"
                    a, b, c = poly.all_coeffs()
                    a, b, c = sympify(a), sympify(b), sympify(c)
                    D = simplify(b**2 - 4*a*c)
                    sqrt_D = simplify(D**0.5)
                    x1 = simplify((-b + sqrt_D) / (2*a))
                    x2 = simplify((-b - sqrt_D) / (2*a))

                    steps += rf"<div>Standard form: \[ ax^2 + bx + c = 0 \]</div>"
                    steps += rf"<div>\[a = {latex(a)},\ b = {latex(b)},\ c = {latex(c)}\]</div>"
                    steps += rf"<div>\[x = \frac{{-b \pm \sqrt{{b^2 - 4ac}}}}{{2a}} \]</div>"
                    steps += rf"<div>\[x = \frac{{-{latex(b)} \pm \sqrt{{{latex(D)}}}}}{{2 \cdot {latex(a)}}} = \frac{{{latex(-b)} \pm {latex(sqrt_D)}}}{{{latex(2*a)}}} \]</div>"
                    steps += rf"<div>\[x_1 = {latex(x1)};\quad x_2 = {latex(x2)}\]</div>"

                    if show_decimal:
                        steps += "<h4>Step 4: Decimal Approximations</h4>"
                        try:
                            steps += rf"<div>\[x_1 \approx {x1.evalf():.5f},\quad x_2 \approx {x2.evalf():.5f}\]</div>"
                        except:
                            steps += "<div>Could not evaluate decimal roots</div>"
                else:
                    steps += "<h3>Step 3: Solve (Exact Roots)</h3>"
                    sols = solve(Eq(factored, 0), var)
                    for s in sols:
                        steps += rf"<div>\[{latex(var)} = {latex(s)}\]</div>"
                        if show_decimal:
                            try:
                                val = float(s.evalf())
                                steps += rf"<div>\[\approx {val:.5f}\]</div>"
                            except:
                                pass

                steps += "<h3>Numeric Roots</h3>"
                for r in poly.nroots():
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
                            steps += rf"<div>\[{latex(var)} = {latex(val)}\]</div>"
                            if show_decimal:
                                try:
                                    valf = float(val.evalf())
                                    steps += rf"<div>\[\approx {valf:.5f}\]</div>"
                                except:
                                    pass
                elif isinstance(sol, dict):
                    for var, val in sol.items():
                        steps += rf"<div>\[{latex(var)} = {latex(val)}\]</div>"
                        if show_decimal:
                            try:
                                valf = float(val.evalf())
                                steps += rf"<div>\[\approx {valf:.5f}\]</div>"
                            except:
                                pass
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
        exact_roots.append(rf"\[x = {latex(r)}\]")
        try:
            val = float(r.evalf())
            exact_roots.append(rf"\[\approx {val:.5f}\]")
        except:
            continue

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
    f = lambda v: float(y_expr.evalf(subs={x: v}))
    ys = [f(v) for v in xs]

    plt.figure(figsize=(6, 4))
    plt.plot(xs, ys, label=rf"$y = {latex(y_expr)}$")
    plt.axhline(0, color='black', lw=0.5)
    plt.axvline(0, color='black', lw=0.5)
    plt.grid(True)
    plt.legend()

    sols = solve(Eq(y_expr, 0), x)
    for r in sols:
        try:
            val = float(r.evalf())
            plt.plot(val, 0, 'ro')
        except:
            continue

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

if __name__ == '__main__':
    import matplotlib
    matplotlib.use('Agg')
    app.run(host='0.0.0.0', port=10000, debug=True)