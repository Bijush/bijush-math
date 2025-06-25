from flask import Flask, render_template, request
from sympy import symbols, Eq, solve, sympify, latex, expand, factor, simplify
from sympy.parsing.sympy_parser import parse_expr
import matplotlib.pyplot as plt
import numpy as np
import os

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    steps = ''
    expression = ''
    if request.method == 'POST':
        equations_text = request.form['equation']
        try:
            lines = [line.strip() for line in equations_text.splitlines() if line.strip()]
            eqs = []
            all_vars = set()

            for line in lines:
                if '=' in line:
                    lhs, rhs = line.split('=')
                    lhs_expr = sympify(lhs)
                    rhs_expr = sympify(rhs)
                else:
                    lhs_expr = sympify(line)
                    rhs_expr = 0
                eq = Eq(lhs_expr, rhs_expr)
                eqs.append(eq)
                all_vars.update(lhs_expr.free_symbols)
                all_vars.update(rhs_expr.free_symbols)

            all_vars = sorted(all_vars, key=lambda s: str(s))  # consistent order
            steps += "<h3>Step 1: System of Equations</h3>"
            for e in eqs:
                steps += rf"\[ {latex(e)} \]<br>"

            solutions = solve(eqs, all_vars)

            steps += "<h3>Step 2: Solving</h3>"
            if solutions:
                if isinstance(solutions, dict):
                    for var, val in solutions.items():
                        steps += rf"\[ {latex(var)} = {latex(val)} \approx {val.evalf(5)} \]<br>"
                else:
                    for sol in solutions:
                        steps += "<div>"
                        for var, val in zip(all_vars, sol):
                            steps += rf"\[ {latex(var)} = {latex(val)} \approx {val.evalf(5)} \]<br>"
                        steps += "</div>"
            else:
                steps += "No solution found."

        except Exception as e:
            steps = f"Error: {str(e)}"

    return render_template('index.html', result=steps, expression='')


@app.route('/graph', methods=['GET', 'POST'])
def graph():
    message = ''
    filename = ''
    latex_expr = ''
    exact_roots = []
    approx_roots = []

    if request.method == 'POST':
        expr = request.form['expression']
        try:
            y_expr = sympify(expr)
            latex_expr = latex(y_expr)

            x = list(y_expr.free_symbols)
            if not x:
                message = "No variable to plot."
                return render_template('graph.html', image=None, message=message)

            x = x[0]
            f = lambda val: float(y_expr.evalf(subs={x: val}))
            x_vals = np.linspace(-10, 10, 400)
            y_vals = [f(val) for val in x_vals]

            eq = Eq(y_expr, 0)
            roots = solve(eq, x)

            for r in roots:
                if r.is_real:
                    exact_roots.append(rf"\[ x = {latex(r)} \]")
                    approx_roots.append(rf"\[ x \approx {r.evalf(5)} \]")

            # Plotting
            plt.clf()
            plt.figure(figsize=(8, 5))
            plt.plot(x_vals, y_vals, label=f"$y = {latex_expr}$")
            plt.axhline(0, color='black', linewidth=0.5)
            plt.axvline(0, color='black', linewidth=0.5)
            plt.xlabel('x')
            plt.ylabel('y')
            plt.title('Graph of the Expression')
            plt.grid(True)

            for r in roots:
                if r.is_real:
                    plt.plot(float(r), 0, 'ro')

            plt.legend()
            os.makedirs('static', exist_ok=True)
            filename = 'static/graph.png'
            plt.savefig(filename)
            plt.close()

        except Exception as e:
            message = f"Graph Error: {str(e)}"

    return render_template('graph.html',
                           image=filename,
                           message=message,
                           expression_latex=latex_expr,
                           exact_roots=exact_roots,
                           approx_roots=approx_roots)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
