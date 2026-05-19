# Hash Tables

A walk-through of hash tables, universal hash families, and a few classic
applications. Ported from the Dastimator lecture so the rendered scenes
match frame-for-frame; the code is half the size.

## Outline

1. **Intro.** What we'll cover.
2. **Hash Table Recipe.** Array + keys + hash function; chaining once the
   universe outgrows the array.
3. **Universal Hash Families.** Definition + alternative probabilistic
   perspective.
4. **Universal Hash Examples.** Two tiny families: one passes, one fails.
5. **Universal Hash Base Example.** The classic $h_a(x) = \sum a_i x_i
   \pmod p$ family, with a proof that it is universal.
6. **Check Triplets.** Detecting an arithmetic triplet in $O(n^2)$
   expected time via a hash table.
7. **$k$-Universal Hash Families.** Stronger guarantee for collisions
   across $k$ keys.
8. **Two-Universal $\Rightarrow$ Universal.** Union-bound proof.
