---
name: mobjects
description: Mobject hierarchy, VMobject, VGroup, positioning, styling - first-principles guide
tags: mobject, vmobject, vgroup, positioning, styling
---

# Mobjects

## What is a Mobject?

"Mobject" stands for **Mathematical Object**. It is the base class for *everything*
visible on screen in Manim -- every circle, line, equation, image, and arrow.

A Mobject carries four things:
1. **A position** in 2D/3D space, stored as a numpy array `[x, y, z]`.
2. **A set of points** -- vertices or curve samples that define its shape.
3. **Visual properties** -- color, opacity, stroke width, fill color.
4. **Child objects (submobjects)** -- other Mobjects nested inside it, forming a tree.

You never write `Mobject()` directly. You use subclasses: `Circle`, `Square`,
`Text`, `MathTex`, `Arrow`, etc. Each subclass generates the right points for its shape.

Think of Mobjects as shapes on an infinite canvas. The camera shows a rectangular
window (roughly 14.2 units wide by 8 units tall). Anything outside exists but is hidden.

## The Mobject family tree

Each level adds capabilities the parent lacks.

```
Mobject -- base class with position, submobjects, basic transforms (shift/scale/rotate)
 +-- VMobject (Vector Mobject) -- adds stroke/fill. All curve-based shapes live here.
 |    +-- VGroup -- collection of VMobjects as one unit (move/color/scale together)
 +-- Group -- like VGroup but for ANY Mobject type (use when mixing images + shapes)
 +-- ImageMobject -- raster images (PNG/JPG). Not vector; can't animate parts.
 +-- ValueTracker -- invisible, stores a float. Drives animations via updaters.
```

**Rule of thumb:** grouping shapes/text/equations? Use `VGroup`.
Group includes an `ImageMobject`? Use `Group`.

## Creating shapes

```python
# Circle: radius defaults to 1. fill_opacity: 0=hollow, 1=solid.
circle = Circle(color=BLUE, fill_opacity=0.5)
# Square: side_length defaults to 2.
square = Square(color=RED)
# Rectangle: independent width and height.
rect = Rectangle(width=4, height=2)
# Dot: a tiny filled circle at a point. Defaults to ORIGIN with DEFAULT_DOT_RADIUS (0.08).
dot = Dot(color=WHITE)
# Line: start/end are points (numpy arrays or direction constants).
line = Line(start=LEFT, end=RIGHT, color=YELLOW)
# Arrow: line with tip. buff = gap between tip and endpoint (0 = touching).
arrow = Arrow(start=LEFT, end=RIGHT, buff=0)
# Text: rendered with Pango (system fonts, no LaTeX needed). font_size defaults to 48.
text = Text("Hello")
# MathTex: rendered with LaTeX. Use raw strings so backslashes pass through.
math = MathTex(r"E = mc^2")  # see equations.md for details
```

## Positioning: where things go on screen

### The coordinate system

Manim uses a math coordinate system: origin at screen center, X right, Y up.
Visible area spans roughly X: [-7.1, 7.1] and Y: [-4, 4].

Direction constants (numpy arrays) let you avoid raw numbers. These are
exported from Manim directly — import and use them, do not redeclare:

```text
UP = (0,1,0)    DOWN = (0,-1,0)    LEFT = (-1,0,0)    RIGHT = (1,0,0)
ORIGIN = (0,0,0)
UL = UP+LEFT     UR = UP+RIGHT     DL = DOWN+LEFT     DR = DOWN+RIGHT
```

Scale them: `3 * RIGHT` = point (3,0,0).
Combine them: `2 * UP + 3 * RIGHT` = point (3,2,0).

### Positioning methods

```python
# ABSOLUTE: move center to a specific point.
mob.move_to(ORIGIN)                    # screen center
mob.move_to(2 * UP + 3 * RIGHT)       # point (3, 2)

# RELATIVE: shift from current position.
mob.shift(RIGHT)                       # 1 unit right from current spot

# NEXT TO another mobject. direction = which side, buff = gap size.
mob.next_to(other_mob, RIGHT)

# SNAP TO EDGE/CORNER. buff = distance from screen boundary.
mob.to_edge(UP)
mob.to_corner(UL)

# ALIGN one edge with another mobject's edge.
mob.align_to(other_mob, UP)            # match top edges
```

### Progressive examples

```python
# 1. Circle at center (default position; radius defaults to 1).
circle = Circle(color=BLUE)
# 2. Move to upper-right.
circle.move_to(2 * UP + 3 * RIGHT)
# 3. Label next to circle with a small gap.
label = Text("r=1", font_size=36)
label.next_to(circle, RIGHT, buff=0.3)
# 4. Three shapes in a horizontal row.
shapes = VGroup(Circle(), Square(), Triangle())
shapes.arrange(RIGHT, buff=MED_LARGE_BUFF)
```

### Reading positions back

```python
mob.get_center()     mob.get_top()       mob.get_bottom()
mob.get_left()       mob.get_right()     mob.get_corner(UR)
```

## Method order: size and orientation before position and appearance

Mobject methods split into two groups:

- **Dimension/orientation** -- `scale`, `scale_to_fit_width`, `scale_to_fit_height`, `stretch`, `rotate`, `set(width=...)`, `set(height=...)`. These change what the mobject looks like in isolation.
- **Position/appearance** -- `shift`, `move_to`, `next_to`, `to_edge`, `to_corner`, `align_to`, `set_color`, `set_fill`, `set_stroke`, `set_opacity`. These place the mobject in the scene or color it.

Always call the dimension/orientation methods first, then the position/appearance methods. The reason: positioning is computed from the mobject's bounding box, and rotating or scaling AFTER `next_to(...)` shifts the bounding box without re-running the positioning, leaving the mobject visibly misaligned.

```python
# GOOD: size first, then place
label = MathTex(r"\theta").scale(0.8).rotate(PI / 6).next_to(arc, UR)

# BAD: placed first, then rotated -- ends up off the arc
label = MathTex(r"\theta").next_to(arc, UR).rotate(PI / 6)
```

When `next_to`/`to_edge`/`align_to` references another mobject, that other mobject must already be in its final position and size. Otherwise the relative placement is computed against a state the viewer never sees.

```python
title = Text("Header").to_edge(UP)            # title is now final
subtitle = Text("...").scale(0.8).next_to(title, DOWN)  # safe: title is final
```

The same logic applies to `VGroup`: call `scale`/`set_height` BEFORE `arrange` (which positions children), and call `arrange` before `next_to`/`to_edge` (which positions the group).

## Sizing and scaling

```python
mob.scale(2)                           # multiply size by factor (2=double, 0.5=half)
mob.scale(2, scale_stroke=True)        # v0.19+: also scale stroke width (default False)
mob.scale_to_fit_width(4)             # scale to exact width in Manim units
mob.scale_to_fit_height(2)            # scale to exact height
mob.stretch(2, dim=0)                  # non-uniform: dim=0 horizontal, dim=1 vertical
mob.set(width=4)                       # set width directly (calls scale internally)
mob.set(height=2)                      # set height directly

# Rotation: angle in radians by default.
mob.rotate(PI / 4)                     # 45 degrees counterclockwise
mob.rotate(45 * DEGREES)              # same thing using DEGREES constant
mob.rotate(PI / 2, about_point=ORIGIN) # orbit around a point, not own center
```

## Styling: colors and appearance

Manim has ~170 predefined color constants: `RED`, `BLUE`, `GREEN`, `YELLOW`,
`PURPLE`, `TEAL`, `ORANGE`, `PINK`, `WHITE`, `GREY`, etc.

Variants A-E go lightest to darkest: `BLUE_A` (lightest) to `BLUE_E` (darkest).
Plain `BLUE` equals `BLUE_C` (middle). Custom: `ManimColor("#1F77B4")`.
HSV (v0.19+): `HSV([0.6, 0.8, 1.0])` — convenient for procedural color schemes.

Quick variants without picking a constant (v0.19+):

```python
BLUE.darker(0.2)        # blend 20% toward black
BLUE.lighter(0.2)       # blend 20% toward white
BLUE.contrasting()      # WHITE or BLACK depending on luminance
```

```python
mob.set_color(RED)                     # overall color (stroke + fill)
mob.set_fill(BLUE, opacity=0.5)       # fill interior; 0=transparent, 1=solid
mob.set_stroke(YELLOW, width=4)       # outline; width in pixels
mob.set_opacity(0.5)                   # overall transparency
mob.set_z_index(1)                     # layering: higher = drawn on top (default 0)
mob.set_color_by_gradient(RED, BLUE)  # gradient across the shape
```

## VGroup: working with collections

A `VGroup` holds multiple VMobjects as one unit. Without it, you would have
to move/color/scale each shape individually.

```python
group = VGroup(circle, square, triangle)
group.shift(UP)                        # moves all three together
group.scale(0.5)                       # scales all three together
group.set_color(RED)                   # colors all three
```

### Layout

```python
group.arrange(RIGHT, buff=MED_LARGE_BUFF)  # horizontal row with a large gap
group.arrange(DOWN)                    # vertical stack (buff defaults to MED_SMALL_BUFF)
group.arrange_in_grid(rows=2, cols=3, buff=MED_LARGE_BUFF)
```

### Indexing and iteration

```python
group[0]             # first element
group[-1]            # last element
group[1:3]           # slice (returns new VGroup)
for mob in group:    # iterate
    mob.set_color(BLUE)
```

### Adding and removing

```python
group.add(new_mob)
group.remove(old_mob)
```

## The .animate syntax (preview)

Any method becomes a smooth animation when called on `.animate`:

```python
circle.shift(RIGHT)                    # instant (no animation)
self.play(circle.animate.shift(RIGHT)) # smooth slide over 1 second
self.play(circle.animate.scale(2).set_color(RED))  # chain multiple changes
self.play(circle.animate.rotate(PI/2), run_time=2, rate_func=smooth)
```

Full details on animations and rate functions in animations.md.

## Copy and state management

```python
circle_copy = circle.copy()            # independent deep copy
circle.save_state()                    # snapshot position, color, size, etc.
circle.scale(3).set_color(RED)         # make temporary changes
self.play(Restore(circle))            # animate back to saved state
```

## Common spacing constants

Used throughout Manim for `buff` parameters. Avoids magic numbers.

```python
SMALL_BUFF     = 0.1     # tight spacing
MED_SMALL_BUFF = 0.25    # default for next_to()
MED_LARGE_BUFF = 0.5     # comfortable spacing
LARGE_BUFF     = 1.0     # generous spacing
```

## Useful geometry reference

```python
# Polygons
Triangle()                              RegularPolygon(n=6)  # hexagon
Polygon(UL, UR, DR, DL)                RoundedRectangle(corner_radius=0.5, width=4, height=2)
# Convex hull from arbitrary points (v0.19+) -- no need to roll your own
points = [LEFT, UP, RIGHT, DOWN]
ConvexHull(*points, color=BLUE)
# Curves
Arc(radius=1, start_angle=0, angle=PI/2)
ArcBetweenPoints(start, end, angle=PI/4)
line1 = Line(LEFT, ORIGIN)
line2 = Line(ORIGIN, UP)
TangentialArc(line1, line2, radius=0.4)  # v0.19+: tangent to two lines
CubicBezier(p0, p1, p2, p3)            Ellipse(width=4, height=2)
Annulus(inner_radius=0.5, outer_radius=1)
# Note: Sector(inner_radius=, outer_radius=) was REMOVED in v0.19. Use Sector(radius=...) or AnnularSector.
# Dashed variants
DashedLine(start=LEFT, end=RIGHT, dash_length=0.1)
DashedVMobject(any_vmobject, num_dashes=15)
# Labeled geometry (v0.18+/v0.19+) -- pre-built label-on-shape combos
LabeledLine(label="L", start=LEFT, end=RIGHT)
LabeledArrow(label="v", start=LEFT, end=RIGHT, color=YELLOW)
LabeledPolygram([(-1, -1, 0), (1, -1, 0), (0, 1, 0)], label=Text("triangle"))
# Axes and number lines
NumberLine(x_range=[-5, 5, 1], length=10, include_numbers=True)
# Images and SVGs (not VMobjects -- use Group, not VGroup, to mix with shapes)
ImageMobject("path/to/image.png")       SVGMobject("path/to/icon.svg")
# v0.20+: SVGMobject exposes named groups: svg["my_group_id"]
```

## Concise updaters with .always (v0.20+)

`mob.always.method(...)` is shorthand for `mob.add_updater(lambda m: m.method(...), call_updater=True)`. The method is called immediately, then re-called every frame. Use it for "follow this mobject" relationships.

```python
sq = Square().to_edge(LEFT)
label = Text("follow")
label.always.next_to(sq, UP, buff=0.2)   # no lambda needed
self.add(sq, label)
self.play(sq.animate.to_edge(RIGHT))
```

**Caveat:** the call's *arguments* are evaluated ONCE at attach time and captured by reference; the method is re-called every frame with that snapshot. So any function call you pass in -- `t.get_value()`, `mob.get_end()`, `mob.get_length()`, arithmetic on dynamic values -- gives a stale value forever. Use `add_updater(lambda m: m.method(...))` whenever an argument needs to be recomputed each frame. See [updaters.md](updaters.md).
