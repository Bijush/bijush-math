from flask import Flask, render_template, request
from sympy import symbols, Eq, solve, sympify, latex, simplify, solveset, S
import matplotlib.pyplot as plt
import numpy as np
import os
import re

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
            inequalities = []
            all_vars = set()

            for line in lines:
                # Inequality detection
                if any(op in line for op in ['<', '>', '<=', '>=']):
                    inequalities.append(line)
                    continue

                if '=' in line:
                    lhs, rhs = line.split('=')
                    lhs_expr = sympify(lhs)
                    rhs_expr = sympify(rhs)
                else:
                    lhs_expr = sympify(line)
                    rhs_expr = 0
                eq = Eq(lhs_expr, rhs_expr)
                eqs.append(eq)
                all_vars |= lhs_expr.free_symbols | rhs_expr.free_symbols

            all_vars = sorted(all_vars, key=lambda s: str(s))

            steps += "<h3>Step 1: Parsed Input</h3>"
            for e in eqs:
                steps += rf"\[ {latex(e)} \]<br>"
            for ineq in inequalities:
                steps += rf"\[ {latex(sympify(ineq))} \] (inequality)<br>"

            steps += "<h3>Step 2: Solving</h3>"

            if inequalities:
                # Handle only one variable inequality
                var = symbols('x')  # Basic assumption for now
                for ineq in inequalities:
                    sol = solveset(sympify(ineq), var, domain=S.Reals)
                    steps += rf"\[ \text{{Solution to }} {ineq}: {latex(sol)} \]<br>"
            elif len(eqs) == 1 and len(all_vars) == 1:
                var = list(all_vars)[0]
                factored = eqs[0].lhs.factor()
                steps += rf"Factored: \[ {latex(eqs[0].lhs)} = {latex(factored)} \]<br>"
                sols = solve(eqs[0], var)
                for sol in sols:
                    steps += rf"\[ {latex(var)} = {latex(sol)} \approx {sol.evalf(5)} \]<br>"
            else:
                sols = solve(eqs, all_vars)
                if isinstance(sols, dict):
                    for var, val in sols.items():
                        steps += rf"\[ {latex(var)} = {latex(val)} \approx {val.evalf(5)} \]<br>"
                elif sols:
                    for sol in sols:
                        steps += "<div>"
                        for var, val in zip(all_vars, sol):
                            steps += rf"\[ {latex(var)} = {latex(val)} \approx {val.evalf(5)} \]<br>"
                        steps += "</div>"
                else:
                    steps += "No solution found."

        except Exception as e:
            steps = f"<b>Error:</b> {str(e)}"

    return render_template('index.html', result=steps, expression='')

@app.route('/graph', methods=['GET', 'POST'])
def graph():
    message = ''
    filename = ''
    expressions = []

    if request.method == 'POST':
        expr_input = request.form['expression']
        try:
            lines = [line.strip() for line in expr_input.splitlines() if line.strip()]
            x, y = symbols('x y')
            x_vals = np.linspace(-10, 10, 400)

            plt.clf()
            plt.figure(figsize=(8, 5))

            for line in lines:
                if '=' not in line:
                    continue
                lhs, rhs = line.split('=')
                lhs_expr = sympify(lhs)
                rhs_expr = sympify(rhs)
                y_expr = solve(Eq(lhs_expr, rhs_expr), y)
                if y_expr:
                    f = lambda val: float(y_expr[0].evalf(subs={x: val}))
                    y_vals = [f(val) for val in x_vals]
                    plt.plot(x_vals, y_vals, label=f"${latex(lhs_expr)} = {latex(rhs_expr)}$")

            plt.axhline(0, color='black', linewidth=0.5)
            plt.axvline(0, color='black', linewidth=0.5)
            plt.xlabel('x')
            plt.ylabel('y')
            plt.title('Graph of Equation(s)')
            plt.grid(True)
            plt.legend()

            os.makedirs('static', exist_ok=True)
            filename = 'static/graph.png'
            plt.savefig(filename)
            plt.close()
        except Exception as e:
            message = f"Graph Error: {str(e)}"

    return render_template('graph.html', image=filename, message=message)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
