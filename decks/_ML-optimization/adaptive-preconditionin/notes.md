# Lecture 12: Adaptive Learning Rates (AdaGrad and ADAM)

## Introduction: A Second Look at Preconditioning

In Lecture 12, we have seen how preconditioning the gradient with the inverse of the Hessian at the current point can significantly improve convergence, at least in the vicinity of a minimum with strong curvature. One of the effects of preconditioning with the Hessian was to make the descent direction invariant to linear transformations of the variables.

The affine-invariance property of Hessian preconditioning is extremely desirable. For example, consider the case of an optimization problem in which we have variables with physical meaning: maybe we are trying to design a bridge, and we have variables that denote lengths, wind strengths, weights, et cetera. In our modeling of the problem, we might have decided all length variables are in meters. If we now were to change our mind and decide to use centimeters instead, we would like the optimization algorithm to be invariant to this change, that is, produce the same sequence of iterates regardless of the units we use. While this would be guaranteed by the Hessian preconditioner, the same cannot be said for gradient descent.

Indeed, let us consider what would happen if we were to move all of our length variables from meters to centimeters. Since a centimeter is a tenth of a meter, the objective is now 10 times less sensitive to a change in length. This means that the gradient of the objective with respect to the new parameterization of lengths would now be $10$ times smaller than before. And yet, all values of the length variables would be $10$ times larger than before, producing a net effect of slowing down the gradient descent update on each of the variables by a factor of $100$ if using the same learning rate! Adjusting the learning rate might compensate for this, at the expense of now affecting the speed of change of all other variables, even if they had been left untouched by the "meter $\rightarrow$ centimeter" reparameterization.

**Example.** As a small numerical example, consider the objective function (say, parameterized in meters) $f(x, y)=\frac{1}{2} x^2+\frac{1}{2} y^2$. After a change of units of $x$, consider now the reparameterized objective:

$$
g\left(x^{\prime}, y\right)=f\left(\frac{x^{\prime}}{\sqrt{2}}, y\right)=\frac{1}{4} x^{\prime 2}+\frac{1}{2} y^2
$$

If you were to plot contour lines for the respective objectives, together with an identical initial point (up to reparameterization), it becomes clear that the gradient descent direction at the initial point shifts. After one step of gradient descent, the two points will no longer be equivalent.

### Today's Lecture

In this lecture, we look at preconditioning algorithms that are *not* based on using the Hessian. Rather, they are based on the idea of adapting the learning rate for each parameter based on historical gradients. Compared to the Hessian preconditioner, the approach in this lecture is significantly more scalable, and it is particularly useful for large-scale optimization problems.

In fact, the algorithms we will discuss today currently include the most-used first-order optimization algorithm in machine learning: **ADAM**.

---

## 1. The AdaGrad Algorithm

The AdaGrad algorithm—introduced by Duchi, Hazan, and Singer \cite{DHS11}—is a gradient-based optimization algorithm that adapts the learning rate for each variable based on the historical gradients.^[The "ada" in AdaGrad is short for "adaptive": the learning rate of each coordinate adapts to the variability of its past gradients.]

The main idea behind AdaGrad is to scale the learning rate of each variable based on the sum of the squared gradients accumulated over time. This allows AdaGrad to give smaller learning rates to frequently updated variables and larger learning rates to variables with infrequent updates. Going back to the example of the bridge design, this means that if we were to change the units of the length variables, AdaGrad would automatically adjust the learning rates to compensate for the change in scale.

In particular, at each iteration $t$, AdaGrad keeps a tally of the sum of the squared gradients up to time $t$ for each variable. This is done by maintaining a vector $s_t$ of components:

$$
\left[s_t\right]_i:=\sqrt{\sum_{\tau=0}^t\left[\nabla f\left(x_\tau\right)\right]_i^2},
$$

where $\left[\nabla f\left(x_t\right)\right]_i$ is the $i$-th component of the gradient at time $t$. The update rule for AdaGrad is then:

$$
x_{t+1}=x_t-\eta M_t^{-1} \nabla f\left(x_t\right), \quad \text{where } M_t:=\operatorname{diag}\left(\left[s_t\right]_i:=\sqrt{\sum_{\tau=0}^t\left[\nabla f\left(x_\tau\right)\right]_i^2}: i=1, \ldots, n\right) \tag{AdaGrad}
$$

We assume that $\left[\nabla f\left(x_0\right)\right]_i \neq 0$ for all $i$, so that $M_t$ is invertible at all times $t=0,1,2, \ldots$.

**Remark 1.1.** The same algorithm can be used in the stochastic setting, where as usual the gradient is replaced by a stochastic gradient:

$$
x_{t+1}=x_t-\eta M_t^{-1} \tilde{\nabla} f\left(x_t\right), \quad \text{where } M_t:=\operatorname{diag}\left(\left[s_t\right]_i:=\sqrt{\sum_{\tau=0}^t\left[\tilde{\nabla} f\left(x_\tau\right)\right]_i^2}: i=1, \ldots, n\right)
$$

It can also be used in the projected setting, where the update is projected onto a feasible set. For simplicity, in this lecture, we will focus on the deterministic, unconstrained setting for our analysis.

---

## 2. ADAM: AdaGrad with Momentum

In practice, people often use a variant of AdaGrad called **ADAM**, introduced by Kingma and Ba \cite{KB15}. ADAM combines the adaptive learning rate of AdaGrad with the idea of momentum we already saw in Lecture 8.^[See [slide:1] for the high-level intuition behind combining momentum with per-coordinate scaling.]

In particular, at each iteration $t$, ADAM keeps track of the momentum (discounted sum of past gradients):

$$
g_t=\gamma g_{t-1}+(1-\gamma) \nabla f\left(x_t\right); \quad g_{-1}:=0.
$$

The scaling factors $s_t$ are also accumulated with a discount rate $\beta$ as:

$$
\left[s_t\right]_i^2=\beta\left[s_{t-1}\right]_i^2+(1-\beta)\left[\nabla f\left(x_t\right)\right]_i^2 \quad i=1, \ldots, n ; \quad s_{-1}:=0.
$$

Finally, ADAM updates the iterate as follows:

$$
x_{t+1}=x_t-\eta M_t^{-1} g_t, \quad \text{where } M_t:=\operatorname{diag}\left(s_t\right) \tag{ADAM}
$$

The hyperparameters $\eta, \gamma$, and $\beta$ in ADAM are typically set to $0.001, 0.9$, and $0.999$ respectively (this is PyTorch's default behavior).

**Remark 2.1.** The ADAM algorithm is widely used in practice and is known to work well for a wide range of optimization problems. It is particularly useful for training deep neural networks. However, ADAM does not have theoretical guarantees like AdaGrad. It is even known to diverge in some cases, even with convex objectives \cite{RKK18}.

---

## 3. Analysis of AdaGrad

In this section, we will analyze the AdaGrad algorithm. For simplicity, we will focus on the non-stochastic version, though the analysis in the presence of stochastic gradients is analogous.

The main result we will prove is that AdaGrad is competitive with the best possible preconditioner in hindsight, as we make precise in the next theorem.

**Theorem 3.1.** Let $f: \mathbb{R}^n \rightarrow \mathbb{R}$ be a convex and differentiable function. AdaGrad is competitive with the best preconditioner in hindsight. More precisely, for any choice of coefficients $\lambda_i \geq 0, i= 1, \ldots, n$, the AdaGrad algorithm with stepsize $\eta=D / \sqrt{2}$ satisfies:

$$
\frac{1}{T} \sum_{t=0}^{T-1} f\left(x_t\right) \leq f\left(x_{\star}\right)+\frac{\sqrt{2 n} D}{T} \sqrt{\min _{\lambda \in \mathbb{R}_{\geq 0}^n,\|\lambda\|_1=n} \sum_{t=0}^{T-1} \nabla f\left(x_t\right)^{\top} \operatorname{diag}(\lambda)^{-1} \nabla f\left(x_t\right)},
$$

where $D:=\max_{t=0}^T\left\|x_t-x_{\star}\right\|_{\infty}$ is the maximum distance from the optimal solution at all times $T$.

In the rest of this section, we prove the above result.

### 3.1 AdaGrad as an Instance of Mirror Descent

The main idea behind the proof is to show that AdaGrad is a form of mirror descent algorithm (Lecture 9), with the twist that the distance-generating function is time-dependent. In particular, we will use as our distance-generating function the (strongly convex) function:

$$
\varphi_t(x):=\frac{1}{2} x^{\top} M_t x
$$

The induced Bregman divergence is:

$$
\mathrm{D}_{\varphi_t}(x \| y)=\varphi_t(x)-\varphi_t(y)-\left\langle\nabla \varphi_t(y), x-y\right\rangle=\frac{1}{2}(x-y)^{\top} M_t(x-y)
$$

We make the connection formal in the following lemma.

**Theorem 3.2.** The AdaGrad update rule is equivalent to the mirror descent update rule with the distance-generating function $\varphi_t(x)=\frac{1}{2} x^{\top} M_t x$, where $M_t:=\operatorname{diag}\left(s_t\right)$.

**Proof.** Remember that the mirror descent update rule is:

$$
\begin{aligned}
x_{t+1} & =\underset{x \in \mathbb{R}^n}{\arg \min }\left\{\eta\left\langle\nabla f\left(x_t\right), x\right\rangle+\mathrm{D}_{\varphi_t}\left(x \| x_t\right)\right\} \\
& =\underset{x \in \mathbb{R}^n}{\arg \min }\left\{\eta\left\langle\nabla f\left(x_t\right), x\right\rangle+\frac{1}{2}\left(x-x_t\right)^{\top} M_t\left(x-x_t\right)\right\}
\end{aligned}
$$

Setting the gradient of the above objective to zero and solving for $x$ yields:

$$
\eta \nabla f\left(x_t\right)+M_t\left(x-x_t\right)=0 \quad \Longrightarrow \quad x=x_t-\eta M_t^{-1} \nabla f\left(x_t\right),
$$

which is exactly the AdaGrad update rule. $\blacksquare$

From the mirror descent lemma we saw in Lecture 9, we can write:

$$
f\left(x_t\right) \leq f\left(x_{\star}\right)+\frac{1}{\eta}\left(\mathrm{D}_{\varphi_t}\left(x_{\star} \| x_t\right)-\mathrm{D}_{\varphi_t}\left(x_{\star} \| x_{t+1}\right)+\mathrm{D}_{\varphi_t}\left(x_t \| x_{t+1}\right)\right).
$$

Summing the above inequalities over $t=0,1, \ldots, T-1$ and using the fact that $M_0=0$ yields:

$$
\sum_{t=0}^{T-1} f\left(x_t\right) \leq T f\left(x_{\star}\right)+\frac{1}{\eta}\left(\underbrace{\sum_{t=0}^{T-2}\left(\mathrm{D}_{\varphi_{t+1}}\left(x_{\star} \| x_{t+1}\right)-\mathrm{D}_{\varphi_t}\left(x_{\star} \| x_{t+1}\right)\right)}_{\text {(A) }}+\underbrace{\sum_{t=0}^{T-1} \mathrm{D}_{\varphi_t}\left(x_t \| x_{t+1}\right)}_{\text {(B) }}\right).
$$

We will now proceed, in the next two subsections, to bound the two summations (A) and (B) separately.

### 3.2 Bounding the "Almost-Telescopic" Terms (A)

**Theorem 3.3.** Let $T$ be arbitrary and assume that $D:=\max _{t=0}^T\left\|x_t-x_{\star}\right\|_{\infty}$ is finite. Then, at all times $T$, the sum (A) satisfies the inequality:

$$
\sum_{t=0}^{T-2}\left(\mathrm{D}_{\varphi_{t+1}}\left(x_{\star} \| x_{t+1}\right)-\mathrm{D}_{\varphi_t}\left(x_{\star} \| x_{t+1}\right)\right) \leq \frac{D^2}{2}\left\|s_{T-1}\right\|_1.
$$

**Proof.** It is easy to see that:

$$
\mathrm{D}_{\varphi_{t+1}}\left(x_{\star} \| x_{t+1}\right)-\mathrm{D}_{\varphi_t}\left(x_{\star} \| x_{t+1}\right)=\frac{1}{2}\left(x_{t+1}-x_{\star}\right)^{\top}\left(M_{t+1}-M_t\right)\left(x_{t+1}-x_{\star}\right).
$$

*(The above is a generalization of the result we saw in Lecture 9, which established that the Bregman divergence induced by the squared Euclidean norm is the squared Euclidean distance.)*

Using now the definition of $D$ together with the Cauchy-Schwarz inequality, we can write:

$$
\begin{aligned}
\frac{1}{2}\left(x_{t+1}-x_{\star}\right)^{\top}\left(M_{t+1}-M_t\right)\left(x_{t+1}-x_{\star}\right) & \leq \frac{1}{2}\left\|x_{t+1}-x_{\star}\right\|_{\infty}^2\left\|s_{t+1}-s_t\right\|_1 \\
& \leq \frac{D^2}{2}\left\|s_{t+1}-s_t\right\|_1
\end{aligned}
$$

On the other hand, since $s_{t+1} \geq s_t \geq 0$ componentwise at all times $t$, then $\left\|s_{t+1}-s_t\right\|_1=\left\|s_{t+1}\right\|_1- \left\|s_t\right\|_1$ and we can write:

$$
\begin{aligned}
\sum_{t=0}^{T-2}\left(\mathrm{D}_{\varphi_{t+1}}\left(x_{\star} \| x_{t+1}\right)-\mathrm{D}_{\varphi_t}\left(x_{\star} \| x_{t+1}\right)\right) & \leq \frac{D^2}{2} \sum_{t=0}^{T-2}\left(\left\|s_{t+1}\right\|_1-\left\|s_t\right\|_1\right) \\
& =\frac{D^2}{2}\left(\left\|s_{T-1}\right\|_1-\left\|s_0\right\|_1\right) \\
& \leq \frac{D^2}{2}\left\|s_{T-1}\right\|_1
\end{aligned}
$$

which is the statement. $\blacksquare$

### 3.3 Bounding the Summation (B)

We now shift our attention to the summation in (B), where we will establish the following bound.

**Theorem 3.4.** At all times $T$, the sum (B) satisfies the inequality:

$$
\sum_{t=0}^{T-1} \mathrm{D}_{\varphi_t}\left(x_t \| x_{t+1}\right) \leq \eta^2\left\|s_{T-1}\right\|_1
$$

**Proof.** Expanding the expression for the Bregman divergence $\mathrm{D}_{\varphi_t}(x \| y)=\frac{1}{2}(x-y)^{\top} M_t(x-y)$, we have:

$$
\mathrm{D}_{\varphi_t}\left(x_t \| x_{t+1}\right)=\frac{1}{2}\left(x_{t+1}-x_t\right)^{\top} M_t\left(x_{t+1}-x_t\right)=\frac{\eta^2}{2} \nabla f\left(x_t\right)^{\top} M_t^{-1} \nabla f\left(x_t\right)
$$

Using the definition of $M_t:=\operatorname{diag}\left(s_t\right)$ where $\left[s_t\right]_i:=\sqrt{\sum_{\tau=0}^t\left[\nabla f\left(x_\tau\right)\right]_i^2}$, we can then write:

$$
\begin{aligned}
\nabla f\left(x_t\right)^{\top} M_t^{-1} \nabla f\left(x_t\right) & =\sum_{i=1}^n \frac{\left[\nabla f\left(x_t\right)\right]_i^2}{\left[s_t\right]_i} \\
& =\sum_{i=1}^n \frac{\left[s_t\right]_i^2-\left[s_{t-1}\right]_i^2}{\left[s_t\right]_i} \\
& \leq 2 \sum_{i=1}^n \frac{\left[s_t\right]_i^2-\left[s_{t-1}\right]_i^2}{\left[s_t\right]_i+\left[s_{t-1}\right]_i}=2 \sum_{i=1}^n\left(\left[s_t\right]_i-\left[s_{t-1}\right]_i\right)=2\left(\left\|s_t\right\|_1-\left\|s_{t-1}\right\|_1\right)
\end{aligned}
$$

Summing over $t=0,1, \ldots, T-1$ yields the result. $\blacksquare$

### 3.4 Finale: Bounding the Norm of the Scaling Factors

The two bounds above show that:

$$
\frac{1}{T} \sum_{t=0}^{T-1} f\left(x_t\right) \leq f\left(x_{\star}\right)+\frac{1}{T}\left(\frac{D^2}{2 \eta}+\eta\right) \left\| s_{T-1} \right\|_1
$$

Hence, setting $\eta=D / \sqrt{2}$ yields:

$$
\frac{1}{T} \sum_{t=0}^{T-1} f\left(x_t\right) \leq f\left(x_{\star}\right)+\frac{D \sqrt{2}}{T}\left\|s_{T-1}\right\|_1 . \tag{3}
$$

So, to complete the proof, we only need to provide a bound on the norm of the scaling factors $s_{T-1}$. This is the content of the following theorem.

**Theorem 3.5.** The norm of the scaling factors $s_{T-1}$ satisfies the inequality:

$$
\left\|s_{T-1}\right\|_1 \leq \sqrt{n} \cdot \sqrt{\min _{\lambda \in \mathbb{R}_{\geq 0}^n,\|\lambda\|_1=n} \sum_{t=0}^{T-1} \nabla f\left(x_t\right)^{\top} \operatorname{diag}(\lambda)^{-1} \nabla f\left(x_t\right)} .
$$

**Proof.** Pick any $\lambda \in \mathbb{R}_{\geq 0}^n,\|\lambda\|_1=n$; we will use Cauchy-Schwarz to bound $\| s_{T-1} \|_1^2$ as follows:

$$
\begin{aligned}
\left\|s_{T-1}\right\|_1^2 & =\left(\sum_{i=1}^n \sqrt{\sum_{t=0}^{T-1}\left[\nabla f\left(x_t\right)\right]_i^2}\right)^2 \\
& =\left(\sum_{i=1}^n\left[\sqrt{\lambda_i} \cdot\left(\frac{1}{\sqrt{\lambda_i}} \sqrt{\sum_{t=0}^{T-1}\left[\nabla f\left(x_t\right)\right]_i^2}\right)\right]\right)^2 \\
& \leq\left(\sum_{i=1}^n \lambda_i\right) \cdot\left(\sum_{i=1}^n\left(\frac{1}{\lambda_i} \sum_{t=0}^{T-1}\left[\nabla f\left(x_t\right)\right]_i^2\right)\right) \\
& =n \cdot\left(\sum_{t=0}^{T-1} \nabla f\left(x_t\right)^{\top} \operatorname{diag}(\lambda)^{-1} \nabla f\left(x_t\right)\right)
\end{aligned}
$$

*(from the Cauchy-Schwarz inequality)*

Taking square roots and using the fact that $\lambda$ was arbitrary yields the statement. $\blacksquare$

Plugging the bound of \ref{theorem-3-5} into \ref{eq-3} proves \ref{theorem-3-1}.