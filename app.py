from flask import Flask, render_template, request
from sympy import symbols, Eq, solve, sympify, latex, expand, factor
import matplotlib.pyplot as plt
import numpy as np
import os

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    steps = ''
    expression = ''
    if request.method == 'POST':
        raw_equation = request.form['equation']
        equation = raw_equation.replace('√', 'sqrt')  # internal conversion
        x, y = symbols('x y')
        try:
            if '=' in equation:
                parts = equation.split('=')
                if equation.count('=') == 1:
                    lhs, rhs = parts
                    lhs_expr = sympify(lhs)
                    rhs_expr = sympify(rhs)
                    eq = Eq(lhs_expr, rhs_expr)

                    steps += "<h3>Step 1: Given Equation</h3>"
                    steps += rf"\[ {latex(sympify(raw_equation))} \]<br>"

                    combined_expr = lhs_expr - rhs_expr
                    expanded_expr = expand(combined_expr)
                    steps += "<h3>Step 2: Simplify Equation</h3>"
                    steps += rf"\[ {latex(combined_expr)} = 0 \Rightarrow {latex(expanded_expr)} = 0 \]<br>"

                    factored_expr = factor(expanded_expr)
                    if factored_expr != expanded_expr:
                        steps += "<h3>Step 3: Factor the Expression</h3>"
                        steps += rf"\[ {latex(expanded_expr)} = {latex(factored_expr)} \]<br>"

                    steps += "<h3>Step 4: Solve</h3>"
                    x_solutions = solve(Eq(factored_expr, 0), x)
                    if x_solutions:
                        for sol in x_solutions:
                            steps += rf"\[ x = {latex(sol)} \approx {sol.evalf(5)} \]<br>"
                    else:
                        steps += "No real solution found."
                    expression = str(lhs_expr)
                else:
                    # Handle system of equations like "x + y = 2, x - y = 1"
                    eqs = [Eq(sympify(p.split('=')[0]), sympify(p.split('=')[1])) for p in raw_equation.split(',')]
                    sol = solve(eqs)
                    steps += "<h3>Solving system of equations:</h3>"
                    for eqn in eqs:
                        steps += rf"\[ {latex(eqn)} \]<br>"
                    steps += "<h3>Solution:</h3>"
                    for var, val in sol.items():
                        steps += rf"\[ {latex(var)} = {latex(val)} \approx {val.evalf(5)} \]<br>"
                    expression = ''  # no single expression for graph
            else:
                expr = sympify(equation)
                steps += "<h3>Simplified Expression:</h3>"
                steps += rf"\[ {latex(expr)} \]<br>"
                sol = solve(expr)
                steps += "<h3>Solution:</h3>"
                for s in sol:
                    steps += rf"\[ x = {latex(s)} \approx {s.evalf(5)} \]<br>"
                expression = str(expr)
        except Exception as e:
            steps = f"Error: {str(e)}"
    return render_template('index.html', result=steps, expression=expression)

@app.route('/graph', methods=['GET', 'POST'])
def graph():
    message = ''
    filename = ''
    latex_expr = ''
    exact_roots = []
    approx_roots = []

    if request.method == 'POST':
        raw_expr = request.form['expression']
        expr = raw_expr.replace('√', 'sqrt')
        x = symbols('x')
        try:
            y_expr = sympify(expr)
            latex_expr = latex(sympify(raw_expr))  # Display LaTeX using original √

            f = lambda val: float(y_expr.evalf(subs={x: val}))
            x_vals = np.linspace(-10, 10, 400)
            y_vals = [f(val) for val in x_vals]

            eq = Eq(y_expr, 0)
            roots = solve(eq, x)

            for r in roots:
                if r.is_real:
                    exact_roots.append(rf"\[ x = {latex(r)} \]")
                    approx_roots.append(rf"\[ x \approx {r.evalf(5)} \]")

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
            filename = 'static/graph.png'
            os.makedirs('static', exist_ok=True)
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
