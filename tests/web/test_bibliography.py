"""BibTeX parsing -> alpha keys + bibliography HTML."""

from pathlib import Path

from simplex.web.bibliography import Author, BibEntry, Bibliography


def test_parses_braced_and_quoted_fields() -> None:
    text = """
    @article{DHS11,
      author = {Duchi, John and Hazan, Elad and Singer, Yoram},
      title = "Adaptive subgradient methods",
      journal = {JMLR},
      year = {2011},
    }
    """
    bib = Bibliography.parse(text)
    entry = bib.get("DHS11")
    assert entry.entry_type == "article"
    assert entry.fields["title"] == "Adaptive subgradient methods"
    assert entry.fields["journal"] == "JMLR"
    assert entry.year == 2011
    assert tuple(a.last for a in entry.authors) == ("Duchi", "Hazan", "Singer")


def test_alpha_key_three_authors() -> None:
    text = """
    @article{x,
      author = {Duchi, John and Hazan, Elad and Singer, Yoram},
      year = {2011},
    }
    """
    bib = Bibliography.parse(text)
    assert bib.get("x").alpha_key == "DHS11"


def test_alpha_key_two_authors() -> None:
    text = """
    @inproceedings{x,
      author = {Kingma, Diederik P. and Ba, Jimmy},
      year = {2015},
    }
    """
    assert Bibliography.parse(text).get("x").alpha_key == "KB15"


def test_alpha_key_single_author() -> None:
    text = """
    @book{x,
      author = {Houseman, Alfred},
      year = {2000},
    }
    """
    assert Bibliography.parse(text).get("x").alpha_key == "Hou00"


def test_alpha_key_four_plus_authors() -> None:
    text = """
    @article{x,
      author = {Alpha, A. and Beta, B. and Gamma, G. and Delta, D. and Epsilon, E.},
      year = {2023},
    }
    """
    # 5 authors: 3 initials + "+" + 23
    assert Bibliography.parse(text).get("x").alpha_key == "ABG+23"


def test_alpha_key_missing_year() -> None:
    text = "@misc{x, author = {Smith, J.}}"
    assert Bibliography.parse(text).get("x").alpha_key.endswith("??")


def test_first_last_author_syntax() -> None:
    """Author given as `First Last` (no comma) must still parse."""
    text = """
    @article{x,
      author = {John Duchi and Elad Hazan},
      year = {2011},
    }
    """
    entry = Bibliography.parse(text).get("x")
    assert entry.authors[0].last == "Duchi"
    assert entry.authors[0].first == "John"
    assert entry.alpha_key == "DH11"


def test_skips_string_preamble_comment() -> None:
    text = """
    @string{jmlr = "Journal of Machine Learning Research"}
    @comment{this is ignored}
    @preamble{"\\newcommand{\\foo}{bar}"}
    @article{real, author = {Smith, J.}, year = 2020}
    """
    bib = Bibliography.parse(text)
    assert tuple(bib.entries) == ("real",)


def test_bibliography_html_only_includes_used_keys() -> None:
    text = """
    @article{a, author = {Adams, A.}, title = {Alpha}, year = 2020}
    @article{b, author = {Brown, B.}, title = {Beta},  year = 2021}
    @article{c, author = {Chen,  C.}, title = {Gamma}, year = 2022}
    """
    bib = Bibliography.parse(text)
    html = bib.to_html(("b", "a"))
    assert "Brown" in html
    assert "Adams" in html
    assert "Chen" not in html
    # Order follows the citation order, not bib order.
    assert html.index("Brown") < html.index("Adams")


def test_bibliography_entry_has_no_double_comma() -> None:
    """Title + venue + year join cleanly with one comma between fields."""
    text = """
    @article{x,
      author = {Smith, John}, title = {A Theorem}, journal = {Acta},
      year = 2020,
    }
    """
    html = Bibliography.parse(text).to_html(("x",))
    # Single comma separators; no `,,` or `,.` between fields.
    assert ",," not in html
    assert ",.}" not in html.replace(" ", "")


def test_bibliography_html_renders_doi_link() -> None:
    text = "@article{x, author = {S, J.}, title = {T}, doi = {10.1/abc}, year = 2020}"
    html = Bibliography.parse(text).to_html(("x",))
    assert "https://doi.org/10.1/abc" in html
    assert 'class="bib-link"' in html


def test_load_from_file(tmp_path: Path) -> None:
    refs = tmp_path / "refs.bib"
    refs.write_text("@article{x, author = {Smith, J.}, year = 2020}\n", encoding="utf-8")
    bib = Bibliography.load(refs)
    assert bib.has("x")


def test_author_initials() -> None:
    assert Author.parse("Doe, John").display == "J. Doe"
    assert Author.parse("Doe, John Paul").display == "J. P. Doe"
    assert Author.parse("Madonna").display == "Madonna"


def test_alpha_key_short_last_name() -> None:
    """Short last names take whatever letters exist (Wu -> 'Wu')."""
    text = "@article{x, author = {Wu, J.}, year = 2020}"
    assert Bibliography.parse(text).get("x").alpha_key == "Wu20"


def test_bibentry_make_lowercases_entry_type() -> None:
    entry = BibEntry.make("k", "Article", {"author": "Smith, J.", "year": "2020"})
    assert entry.entry_type == "article"


def test_bibliography_html_uses_alpha_marker() -> None:
    """The printed bullet must show the alpha key (`[KB15]`) so it
    matches the inline citation chip -- not a `[1]` ordinal."""
    text = """
    @article{a, author = {Adams, A.}, title = {Alpha}, year = 2020}
    @inproceedings{b, author = {Brown, B. and Chen, C.}, title = {Beta}, year = 2021}
    """
    bib = Bibliography.parse(text)
    html = bib.to_html(("a", "b"))
    assert '<ul class="bib-list" role="list">' in html
    assert "<ol" not in html
    # Marker spans, not the old CSS counter.
    assert '<span class="bib-marker">[Ada20]</span>' in html
    assert '<span class="bib-marker">[BC21]</span>' in html
    assert "counter(bib)" not in html
