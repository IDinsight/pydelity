"""Page-break verification: a verdict on each break between two consecutive pages.

A vision model, the judge, reads both pages of a break from their images and page
files and says whether content carries on from the earlier page to the later one, and
how it joins. Code checks its verdict. When page-break verification's verifier is on,
a second request to the same model reviews the verdict before its file is written.
"""
